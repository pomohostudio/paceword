#!/usr/bin/env node
/**
 * fred-mcp v2
 *
 * A local cache-and-query layer over the FRED API.
 *
 *   FRED  ->  fred_fetch  ->  SQLite  ->  fred_query / fred_revisions / fred_export_csv
 *
 * Design notes worth knowing before you edit this:
 *
 * 1. Observations are stored keyed on (series_id, date, realtime_start).
 *    FRED returns one row per *vintage* of each observation, distinguished by
 *    its realtime window. Collapsing that to date+value loses revision history
 *    and silently produces duplicate dates. So we keep the window.
 *
 * 2. fred_fetch returns a SUMMARY, not data. Observations go to disk. Pulling
 *    a full monthly series into a model's context costs tens of thousands of
 *    tokens; a summary costs about two hundred.
 *
 * 3. The store is a cache, not a source of truth. FRED is. If the schema ever
 *    needs to change, delete the file and re-fetch. There are no migrations
 *    by design.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { DatabaseSync } from "node:sqlite";
import { z } from "zod";
import { mkdirSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join, resolve } from "node:path";

const API_KEY = process.env.FRED_API_KEY;
// When the platform's egress proxy injects the api_key query parameter itself
// (an environment "API credential"), the server must NOT require or append a key.
const PROXY_AUTH = process.env.FRED_PROXY_AUTH === "1";
const BASE = "https://api.stlouisfed.org/fred";
const DB_DIR = join(homedir(), ".local", "share", "fred-mcp");
const DB_PATH = process.env.FRED_DB_PATH || join(DB_DIR, "fred.db");
const EXPORT_DIR = resolve(process.cwd(), "fred-exports");

// FRED's sentinel for "the current vintage, still in effect".
const OPEN_VINTAGE = "9999-12-31";
const EARLIEST_VINTAGE = "1776-07-04";

if (!API_KEY && !PROXY_AUTH) {
  console.error(
    "fred-mcp: FRED_API_KEY is not set (and FRED_PROXY_AUTH!=1). Refusing to start."
  );
  process.exit(1);
}

const redact = (t) => (API_KEY ? String(t).split(API_KEY).join("[REDACTED]") : String(t));

/* ------------------------------------------------------------------ store */

mkdirSync(DB_DIR, { recursive: true });
const db = new DatabaseSync(DB_PATH);

db.exec(`
  PRAGMA journal_mode = WAL;
  CREATE TABLE IF NOT EXISTS observations (
    series_id      TEXT NOT NULL,
    date           TEXT NOT NULL,
    realtime_start TEXT NOT NULL,
    realtime_end   TEXT NOT NULL,
    value          REAL,
    PRIMARY KEY (series_id, date, realtime_start)
  );
  CREATE INDEX IF NOT EXISTS idx_obs_lookup
    ON observations (series_id, date, realtime_end);
  CREATE TABLE IF NOT EXISTS series_meta (
    series_id           TEXT PRIMARY KEY,
    title               TEXT,
    units               TEXT,
    frequency           TEXT,
    seasonal_adjustment TEXT,
    last_updated        TEXT,
    fetched_at          TEXT
  );
`);

const insertObs = db.prepare(
  `INSERT OR REPLACE INTO observations
     (series_id, date, realtime_start, realtime_end, value)
   VALUES (?, ?, ?, ?, ?)`
);
const insertMeta = db.prepare(
  `INSERT OR REPLACE INTO series_meta
     (series_id, title, units, frequency, seasonal_adjustment, last_updated, fetched_at)
   VALUES (?, ?, ?, ?, ?, ?, ?)`
);

/* ------------------------------------------------------------------- http */

async function fredGet(path, params) {
  const url = new URL(`${BASE}/${path}`);
  if (API_KEY) url.searchParams.set("api_key", API_KEY);
  url.searchParams.set("file_type", "json");
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
  }

  let res;
  try {
    res = await fetch(url, {
      headers: { "User-Agent": "fred-mcp/2.0" },
      signal: AbortSignal.timeout(60000),
    });
  } catch (err) {
    throw new Error(`Network error calling FRED: ${redact(err.message)}`);
  }

  const body = await res.text();
  if (!res.ok) {
    let detail = body.slice(0, 400);
    try {
      const p = JSON.parse(body);
      if (p.error_message) detail = p.error_message;
    } catch {}
    throw new Error(`FRED returned ${res.status}: ${redact(detail)}`);
  }
  try {
    return JSON.parse(body);
  } catch {
    throw new Error("FRED returned a response that was not valid JSON.");
  }
}

/** Run jobs with a small concurrency cap. FRED tolerates this comfortably. */
async function pool(items, limit, worker) {
  const out = [];
  let i = 0;
  const runners = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (i < items.length) {
      const idx = i++;
      out[idx] = await worker(items[idx]);
    }
  });
  await Promise.all(runners);
  return out;
}

const toNum = (v) => (v === "." || v === "" || v == null ? null : Number(v));

/* ------------------------------------------------------------------ tools */

const ok = (d) => ({ content: [{ type: "text", text: JSON.stringify(d, null, 2) }] });
const fail = (e) => ({ isError: true, content: [{ type: "text", text: redact(e.message ?? e) }] });

const server = new McpServer({ name: "fred-mcp", version: "2.0.0" });

server.registerTool(
  "fred_search_series",
  {
    title: "Search FRED series",
    description:
      "Find FRED series IDs by keyword. FRED holds hundreds of thousands of series and IDs are not guessable, so search before fetching.",
    inputSchema: {
      search_text: z.string(),
      limit: z.number().int().min(1).max(200).optional(),
      order_by: z
        .enum(["search_rank", "popularity", "last_updated", "observation_end"])
        .optional(),
    },
  },
  async (a) => {
    try {
      const d = await fredGet("series/search", { ...a, limit: a.limit ?? 15 });
      return ok(
        (d.seriess ?? []).map((s) => ({
          id: s.id,
          title: s.title,
          units: s.units_short,
          freq: s.frequency_short,
          sa: s.seasonal_adjustment_short,
          start: s.observation_start,
          end: s.observation_end,
          popularity: s.popularity,
        }))
      );
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "fred_browse_category",
  {
    title: "Browse a FRED category",
    description:
      "List the series in a FRED category. Useful starting points: 10 = Population, Employment and Labor Markets; 32991 = Money, Banking and Finance; 32992 = National Accounts; 32455 = Prices.",
    inputSchema: {
      category_id: z.number().int(),
      limit: z.number().int().min(1).max(200).optional(),
    },
  },
  async (a) => {
    try {
      const d = await fredGet("category/series", { ...a, limit: a.limit ?? 25 });
      return ok(
        (d.seriess ?? []).map((s) => ({
          id: s.id,
          title: s.title,
          units: s.units_short,
          freq: s.frequency_short,
          popularity: s.popularity,
        }))
      );
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "fred_get_series_info",
  {
    title: "Get FRED series metadata",
    description:
      "Metadata for one series: units, frequency, seasonal adjustment, coverage, last updated, notes. Check this before interpreting values.",
    inputSchema: { series_id: z.string() },
  },
  async (a) => {
    try {
      const d = await fredGet("series", a);
      return ok(d.seriess?.[0] ?? d);
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "fred_fetch",
  {
    title: "Fetch FRED series into the local store",
    description:
      "Download one or more series into the local SQLite cache. Returns a summary only, never the full data: query it afterwards with fred_query, fred_revisions or fred_export_csv. Set all_vintages=true to capture full revision history.",
    inputSchema: {
      series_ids: z.array(z.string()).min(1).max(25),
      observation_start: z.string().optional().describe("yyyy-mm-dd"),
      observation_end: z.string().optional().describe("yyyy-mm-dd"),
      frequency: z
        .enum(["d", "w", "bw", "m", "q", "sa", "a"])
        .optional()
        .describe("Downsample only. Cannot upsample."),
      aggregation_method: z
        .enum(["avg", "sum", "eop"])
        .optional()
        .describe("How to aggregate when downsampling. FRED defaults to avg."),
      units: z
        .enum(["lin", "chg", "ch1", "pch", "pc1", "pca", "cch", "cca", "log"])
        .optional(),
      all_vintages: z
        .boolean()
        .optional()
        .describe(
          "Fetch every historical vintage rather than only current values. Larger download; needed for revision analysis."
        ),
    },
  },
  async (a) => {
    try {
      const { series_ids, all_vintages, ...common } = a;
      const vintageParams = all_vintages
        ? { realtime_start: EARLIEST_VINTAGE, realtime_end: OPEN_VINTAGE }
        : {};

      const results = await pool(series_ids, 4, async (sid) => {
        try {
          const [obsRes, metaRes] = await Promise.all([
            fredGet("series/observations", {
              ...common,
              ...vintageParams,
              series_id: sid,
              limit: 100000,
            }),
            fredGet("series", { series_id: sid }),
          ]);

          const rows = obsRes.observations ?? [];
          for (const o of rows) {
            insertObs.run(
              sid,
              o.date,
              o.realtime_start ?? OPEN_VINTAGE,
              o.realtime_end ?? OPEN_VINTAGE,
              toNum(o.value)
            );
          }

          const m = metaRes.seriess?.[0] ?? {};
          insertMeta.run(
            sid,
            m.title ?? null,
            m.units ?? null,
            m.frequency ?? null,
            m.seasonal_adjustment ?? null,
            m.last_updated ?? null,
            new Date().toISOString()
          );

          const dates = rows.map((r) => r.date).sort();
          const latest = rows
            .filter((r) => (r.realtime_end ?? OPEN_VINTAGE) === OPEN_VINTAGE)
            .sort((x, y) => x.date.localeCompare(y.date))
            .slice(-3)
            .map((r) => ({ date: r.date, value: toNum(r.value) }));

          return {
            series_id: sid,
            title: m.title,
            units: m.units,
            rows_stored: rows.length,
            date_range: dates.length ? [dates[0], dates[dates.length - 1]] : null,
            last_updated: m.last_updated,
            latest_values: latest,
          };
        } catch (err) {
          return { series_id: sid, error: redact(err.message) };
        }
      });

      return ok({
        stored_in: DB_PATH,
        vintages: all_vintages ? "all" : "current only",
        series: results,
      });
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "fred_query",
  {
    title: "Query the local FRED store",
    description:
      "Read stored observations. By default returns the current vintage. Pass as_of to see the data as it stood on a past date. Use limit to keep results small, or fred_export_csv for anything large.",
    inputSchema: {
      series_ids: z.array(z.string()).min(1).max(25),
      start: z.string().optional().describe("yyyy-mm-dd"),
      end: z.string().optional().describe("yyyy-mm-dd"),
      as_of: z
        .string()
        .optional()
        .describe("Point-in-time vintage date, yyyy-mm-dd. Omit for current."),
      limit: z.number().int().min(1).max(500).optional(),
    },
  },
  async (a) => {
    try {
      const rows = selectObs(a);
      const capped = a.limit ? rows.slice(-a.limit) : rows.slice(-100);
      return ok({
        returned: capped.length,
        total_matching: rows.length,
        truncated: capped.length < rows.length,
        note:
          capped.length < rows.length
            ? "Showing the most recent rows. Use fred_export_csv for the full set."
            : undefined,
        rows: capped,
      });
    } catch (e) {
      return fail(e);
    }
  }
);

function selectObs({ series_ids, start, end, as_of }) {
  const ph = series_ids.map(() => "?").join(",");
  const clauses = [`series_id IN (${ph})`];
  const args = [...series_ids];
  if (start) (clauses.push("date >= ?"), args.push(start));
  if (end) (clauses.push("date <= ?"), args.push(end));
  if (as_of) {
    clauses.push("realtime_start <= ? AND realtime_end >= ?");
    args.push(as_of, as_of);
  } else {
    clauses.push("realtime_end = ?");
    args.push(OPEN_VINTAGE);
  }
  return db
    .prepare(
      `SELECT series_id, date, value, realtime_start, realtime_end
         FROM observations WHERE ${clauses.join(" AND ")}
        ORDER BY date, series_id`
    )
    .all(...args)
    .map((r) => ({ ...r }));
}

server.registerTool(
  "fred_revisions",
  {
    title: "Show how an observation was revised",
    description:
      "For one series, show every stored vintage of each observation date, so you can see how a published figure changed over time. Requires a prior fred_fetch with all_vintages=true.",
    inputSchema: {
      series_id: z.string(),
      date: z.string().optional().describe("Single observation date, yyyy-mm-dd"),
      start: z.string().optional(),
      end: z.string().optional(),
    },
  },
  async (a) => {
    try {
      const clauses = ["series_id = ?"];
      const args = [a.series_id];
      if (a.date) (clauses.push("date = ?"), args.push(a.date));
      if (a.start) (clauses.push("date >= ?"), args.push(a.start));
      if (a.end) (clauses.push("date <= ?"), args.push(a.end));

      const rows = db
        .prepare(
          `SELECT date, realtime_start, realtime_end, value
             FROM observations WHERE ${clauses.join(" AND ")}
            ORDER BY date, realtime_start`
        )
        .all(...args);

      const byDate = {};
      for (const r of rows) {
        (byDate[r.date] ??= []).push({
          published: r.realtime_start,
          superseded: r.realtime_end === OPEN_VINTAGE ? "current" : r.realtime_end,
          value: r.value,
        });
      }
      const revised = Object.entries(byDate)
        .filter(([, v]) => v.length > 1)
        .map(([date, vintages]) => ({
          date,
          vintages,
          first: vintages[0].value,
          latest: vintages[vintages.length - 1].value,
          net_revision:
            vintages[vintages.length - 1].value != null && vintages[0].value != null
              ? Number((vintages[vintages.length - 1].value - vintages[0].value).toFixed(4))
              : null,
        }));

      return ok({
        series_id: a.series_id,
        dates_examined: Object.keys(byDate).length,
        dates_revised: revised.length,
        note: rows.length
          ? undefined
          : "No rows stored. Run fred_fetch with all_vintages=true first.",
        revisions: revised.slice(0, 60),
      });
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "fred_export_csv",
  {
    title: "Export stored series to CSV",
    description:
      "Write stored observations to a CSV file in ./fred-exports/ next to the current working directory. Returns the file path and a preview, not the data. Use this for charting and for anything larger than a few dozen rows.",
    inputSchema: {
      series_ids: z.array(z.string()).min(1).max(25),
      start: z.string().optional(),
      end: z.string().optional(),
      as_of: z.string().optional(),
      filename: z.string().optional().describe("Defaults to the series IDs joined."),
      layout: z
        .enum(["long", "wide"])
        .optional()
        .describe("long = one row per series+date. wide = dates as rows, series as columns."),
    },
  },
  async (a) => {
    try {
      const rows = selectObs(a);
      if (!rows.length) {
        return ok({ written: false, reason: "No matching rows in the store. Run fred_fetch first." });
      }

      let csv;
      if ((a.layout ?? "long") === "wide") {
        const ids = [...new Set(rows.map((r) => r.series_id))].sort();
        const dates = [...new Set(rows.map((r) => r.date))].sort();
        const lookup = new Map(rows.map((r) => [`${r.series_id}|${r.date}`, r.value]));
        csv =
          ["date", ...ids].join(",") +
          "\n" +
          dates
            .map((d) => [d, ...ids.map((s) => lookup.get(`${s}|${d}`) ?? "")].join(","))
            .join("\n");
      } else {
        csv =
          "series_id,date,value,realtime_start,realtime_end\n" +
          rows
            .map((r) =>
              [r.series_id, r.date, r.value ?? "", r.realtime_start, r.realtime_end].join(",")
            )
            .join("\n");
      }

      mkdirSync(EXPORT_DIR, { recursive: true });
      const name = (a.filename ?? a.series_ids.join("_")).replace(/[^\w.-]/g, "_");
      const path = join(EXPORT_DIR, name.endsWith(".csv") ? name : `${name}.csv`);
      writeFileSync(path, csv + "\n", "utf8");

      return ok({
        written: true,
        path,
        rows: rows.length,
        layout: a.layout ?? "long",
        preview: csv.split("\n").slice(0, 4),
      });
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "fred_store_status",
  {
    title: "What is in the local store",
    description:
      "List cached series with row counts, date coverage, whether vintages were captured, and when each was last fetched. Check this before re-downloading.",
    inputSchema: {},
  },
  async () => {
    try {
      const rows = db
        .prepare(
          `SELECT m.series_id, m.title, m.units, m.frequency, m.last_updated, m.fetched_at,
                  COUNT(o.date) AS rows_stored,
                  MIN(o.date) AS first_date, MAX(o.date) AS last_date,
                  COUNT(DISTINCT o.realtime_start) AS vintages
             FROM series_meta m LEFT JOIN observations o ON o.series_id = m.series_id
            GROUP BY m.series_id ORDER BY m.series_id`
        )
        .all();
      return ok({ db_path: DB_PATH, export_dir: EXPORT_DIR, series: rows.map((r) => ({ ...r })) });
    } catch (e) {
      return fail(e);
    }
  }
);

server.registerTool(
  "fred_get_vintage_dates",
  {
    title: "Get FRED vintage dates",
    description:
      "Dates on which a series was revised or newly released, straight from FRED. Use fred_revisions for the values themselves.",
    inputSchema: {
      series_id: z.string(),
      limit: z.number().int().min(1).max(2000).optional(),
      sort_order: z.enum(["asc", "desc"]).optional(),
    },
  },
  async (a) => {
    try {
      const d = await fredGet("series/vintagedates", a);
      return ok({ count: d.count, vintage_dates: d.vintage_dates ?? [] });
    } catch (e) {
      return fail(e);
    }
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
console.error(`fred-mcp v2: ready on stdio (store: ${DB_PATH})`);
