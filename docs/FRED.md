# FRED reference

Context for working with the local `fred` MCP server. Drop this in a project as
`CLAUDE.md`, or point at it with `@FRED.md` in a session.

## What this is

A local cache-and-query layer over the FRED API.

```
FRED  ->  fred_fetch  ->  SQLite  ->  fred_query / fred_revisions / fred_export_csv
```

- Store: `~/.local/share/fred-mcp/fred.db`
- Exports: `./fred-exports/` relative to the session's working directory
- The store is a cache. FRED is the source of truth. If it is ever wrong,
  delete the file and re-fetch.

## The rule that matters most

**Never backtest against current-vintage data.**

Current FRED values include revisions published long after the period they
describe. A model tested on them sees numbers nobody had at the time, so the
backtest measures hindsight rather than forecasting skill. This is the most
common way a macro forecasting tool looks good in testing and disappoints live.

Every historical evaluation must use `fred_query` with `as_of` set to the date
the forecast would have been made. That is what this server exists for.

Corollary: any series used in a backtest must have been fetched with
`all_vintages: true`. Without it the store holds only current values and `as_of`
silently returns them, which produces a wrong answer rather than an error.
Check `fred_store_status` (the `vintages` column) before trusting an `as_of`
result.

## Tools

### Finding series

**`fred_search_series`** `{search_text, limit?, order_by?}`
Keyword search. `order_by`: search_rank, popularity, last_updated,
observation_end. Always search before assuming a series ID: FRED holds hundreds
of thousands and IDs are not guessable.

**`fred_browse_category`** `{category_id, limit?}`
List a category. Useful roots: 10 Population/Employment/Labor, 32455 Prices,
32991 Money/Banking/Finance, 32992 National Accounts.

**`fred_get_series_info`** `{series_id}`
Units, frequency, seasonal adjustment, coverage, last updated, notes. Check
this before interpreting values. Seasonal adjustment and units are where
mistakes start.

### Getting data in

**`fred_fetch`** `{series_ids[], observation_start?, observation_end?, frequency?, aggregation_method?, units?, all_vintages?}`
Up to 25 series per call, fetched concurrently. Returns a summary, never the
data itself.

- `frequency`: d, w, bw, m, q, sa, a. Downsample only, never upsample.
- `aggregation_method`: avg, sum, eop. FRED defaults to avg. For stock
  variables and index levels, `eop` is usually what you want.
- `units`: lin, chg, ch1, pch, pc1, pca, cch, cca, log. Transform server-side
  rather than in your own code.
- `all_vintages`: capture every historical vintage. Larger download, required
  for any point-in-time work.

**`fred_store_status`** `{}`
What is already cached: row counts, coverage, vintage counts, fetch times.
Check before re-downloading.

### Getting data out

**`fred_query`** `{series_ids[], start?, end?, as_of?, limit?}`
Reads the local store. No `as_of` gives the current vintage. With `as_of` it
returns the data as published on that date. Caps output at 100 rows by default.

**`fred_revisions`** `{series_id, date?, start?, end?}`
Every stored vintage of each observation date, with first value, latest value
and net revision. Requires a prior `all_vintages` fetch.

**`fred_export_csv`** `{series_ids[], start?, end?, as_of?, filename?, layout?}`
Writes to `./fred-exports/`. `layout: "wide"` puts dates in rows and series in
columns, which is what you want for modelling. `"long"` keeps the realtime
columns, which is what you want for vintage work. Use this for anything beyond
a few dozen rows: it keeps the data out of context entirely.

**`fred_get_vintage_dates`** `{series_id, limit?, sort_order?}`
Revision dates straight from FRED, without values.

## Working directly in SQL

The store is a plain SQLite file. For anything the tools do not cover, query it
with a script rather than asking for more tool calls.

```sql
-- observations(series_id, date, realtime_start, realtime_end, value)
-- series_meta(series_id, title, units, frequency, seasonal_adjustment,
--             last_updated, fetched_at)

-- current vintage
SELECT date, value FROM observations
 WHERE series_id = 'GDPC1' AND realtime_end = '9999-12-31' ORDER BY date;

-- as it stood on a given date
SELECT date, value FROM observations
 WHERE series_id = 'GDPC1'
   AND realtime_start <= '2025-06-30' AND realtime_end >= '2025-06-30'
 ORDER BY date;

-- first print vs latest, per observation
SELECT date,
       MIN(realtime_start) AS first_published,
       (SELECT value FROM observations o2
         WHERE o2.series_id = o1.series_id AND o2.date = o1.date
         ORDER BY realtime_start LIMIT 1) AS first_value,
       (SELECT value FROM observations o3
         WHERE o3.series_id = o1.series_id AND o3.date = o1.date
           AND o3.realtime_end = '9999-12-31') AS current_value
  FROM observations o1 WHERE series_id = 'GDPC1' GROUP BY date;
```

`9999-12-31` is FRED's sentinel for "still current".

## Series worth knowing

Treat this as a starting point, not an authority. Verify with
`fred_search_series` before relying on any ID: some are close variants of each
other and picking the wrong one is a silent error.

**Labour**
- UNRATE unemployment rate, SA. UNRATENSA unadjusted.
- PAYEMS total nonfarm payrolls
- ICSA initial jobless claims, weekly. Fast-moving, useful for nowcasting.
- CIVPART participation rate, U6RATE broad underemployment
- JTSJOL job openings

**Output and activity**
- GDPC1 real GDP, GDP nominal
- INDPRO industrial production
- RSAFS retail sales
- HOUST housing starts

**Prices**
- CPIAUCSL headline CPI, CPILFESL core CPI
- PCEPI headline PCE, PCEPILFE core PCE (the Fed's target measure)
- PPIACO producer prices

**Rates and markets**
- FEDFUNDS effective fed funds
- DGS2, DGS10 Treasury yields. T10Y2Y the 2s10s spread.
- VIXCLS volatility index

**Regime**
- USREC NBER recession indicator, 0/1. Note this is dated retrospectively by
  the NBER, so it is unusable as a real-time input and fine as a labelling
  variable for evaluation.

## Revision behaviour differs by series

Do not assume one profile generalises. Test each series you plan to use.

- **GDPC1**: advance, second and third estimates, then annual and
  comprehensive revisions. Heavily revised, several vintages per quarter.
- **PAYEMS**: monthly revisions to the prior two months, plus annual
  benchmarking against unemployment insurance records. Benchmark revisions can
  be large.
- **UNRATE**: the seasonally adjusted series is revised once a year when
  seasonal factors are recomputed, typically with the January reference month.
  The unadjusted series is effectively never revised. Poor choice for
  demonstrating revisions, and a reason not to generalise from it.
- **Daily market series** (DGS10, VIXCLS): not revised. `all_vintages` adds
  nothing.

## Patterns

**Point-in-time backtest**
1. `fred_fetch` every input series with `all_vintages: true`
2. Confirm vintage counts in `fred_store_status`
3. For each forecast date, `fred_query` with `as_of` set to that date
4. Evaluate against the current vintage, since that is the best estimate of
   what actually happened

**Publication lag matters as much as revision.** A series being revised is one
problem; a series not existing yet at forecast time is a different and worse
one. Q1 GDP is not published until late April. Check `realtime_start` on the
first vintage of each series to learn its true lag, rather than assuming.

**Mixed frequency**: fetch at native frequency and aggregate deliberately with
`frequency` plus `aggregation_method`. Do not let a default average silently
convert a stock variable into something meaningless.

**Charting and modelling**: `fred_export_csv` with `layout: "wide"`, then work
against the file with a script. Never pull full series into context.

## Things that will bite

- Missing values arrive from FRED as `"."` and are stored as NULL. Handle them
  rather than treating NULL as zero.
- `fred_query` truncates to the most recent 100 rows unless `limit` is set.
  Check the `truncated` flag before concluding a series is short.
- Two sessions can run the server at once. Writes are upserts keyed on the
  vintage, so this is safe, but a fetch in one session changes what another
  sees.
- FRED transformations (`units`) are applied before storage. A series fetched
  with `units: "pch"` is stored as percent change, not as levels. Fetch levels
  and transform at query time if you might want both.

---

## Pattern B — making the cloud environment self-sufficient

Goal: `fred_*` tools available natively in the paceword cloud environment, including in
Routine-fired sessions (which run without account connectors — environment-level MCP
servers are the only way data like this reaches the automated cycles).

Two facts established 2026-09-14: the container's network policy blocks
`api.stlouisfed.org` (must be allowed), and this server does not match any public
fred-mcp package (its command must be copied from the machine where it works).

### Step 1 — on the Mac, get the server's exact spec

In a terminal (or ask any local Claude session to run it):

    claude mcp get fred        # or: claude mcp list

Copy the `command`, `args`, and env var NAMES it shows. Do not paste the API key value
into any chat — it goes only into the environment settings in step 2. Two cases:

- Command is portable (`uvx <pkg>`, `npx <pkg>`, `pipx run <pkg>`): proceed directly.
- Command is a local path (`/Users/.../fred-mcp/...`): the container cannot run a Mac
  path. Package it first: push the server's code to a private repo the environment can
  clone, or make it pip/npm installable; then the command becomes portable.

### Step 2 — Claude Code web → this environment's settings

1. **Network policy**: add `api.stlouisfed.org` to the allowed domains.
2. **Environment variables**: add `FRED_API_KEY` (free key: fredaccount.stlouisfed.org/apikeys).
3. **MCP servers**: add server `fred` with the command/args from step 1.

### Step 3 — verify (a session can do this)

In a new session on this environment (or an existing one after MCP reconnect):

    curl -sS -o /dev/null -w "%{http_code}" "https://api.stlouisfed.org"   # expect not 000
    # then: fred_store_status via the fred tools, and a small fred_fetch/fred_query

### Cloud-specific caveats

- The SQLite store lives in the container and dies with it. Harmless by design — FRED
  is the source of truth and the store is a cache — but it means `all_vintages`
  fetches recur; keep them scoped to the series actually needed.
- Environment changes apply to sessions/containers started after saving; a running
  session picks the server up on its next MCP reconnect at the earliest.
