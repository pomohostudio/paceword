# Runbook — the standing process

Everything in this repo is a snapshot. Forecasting skill lives in the loop. This is the
loop, sized at roughly one hour per month.

## Monthly update (repeat until 2029-08-09)

1. **Retrieve.** Search current Iran news: war status, succession/Mojtaba, security-force
   cohesion (defections? unit-level fractures?), protests, rial/inflation. The two live
   cruxes from the panel: (a) credibility of IRGC-fracture reporting, (b) any sign of a
   creeping coup (which resolves NO — construct!).
2. **Increment.** For each genuinely new development, one log-odds increment with
   direction and size, appended to a dated section of this file. Superforecaster norm:
   most months the honest increment is 0.00–0.10; moves >0.3 need extraordinary evidence.
3. **Re-poll the panel** (quarterly is enough): re-run the three blind model-forecasters
   with the same prompt, updated context. Do not show them prior answers.
4. **Log the market** price (pre- and post-update) per MARKET.md.
5. **Publish the new ensemble number** in this file with the date. Never edit old entries.

### Step 1b — DATA WATCH (every cycle)

Search for newly released independent expert coding extending coverage past what the
project last used: V-Dem (~March), Freedom House (~Feb), EIU (~Feb), ERT, Polity/GWF
successors, UCDP, and any credible new dataset. **Reliability bar — the audit's own
standard:** institutional source, documented multi-coder or measurement-model
methodology, versioned releases; not single-author or advocacy-sourced codings.

When a qualifying release covers 2026+: pull it via reachable GitHub mirrors
(`vdeminstitute/vdemdata`, `xmarquez/democracyData`,
`forecastingresearch/forecastbench-datasets`), log what it says about Iran —
**especially any `v2regdur` reset, which bears directly on resolution criterion A** —
re-anchor the outside view, and treat it as a crux-level event exempt from the ±0.10
norm. Every update entry records the data-watch result even when negative
("no new qualifying releases").

The first big one: **V-Dem's ~March 2027 release is the first independent expert coding
of 2026 Iran** — the first outside check on everything this project coded by hand.

## Annual events

- **V-Dem release (~March):** re-run `scripts/improve.py` on the new dataset; re-anchor
  the outside view; check whether V-Dem coded a regime spell change for Iran.
- **ForecastBench snapshots:** refresh crowd anchors from
  `forecastingresearch/forecastbench-datasets`.

## At resolution (2029-08-09)

Score every logged forecast with Brier against the resolved outcome, per the
pre-registered criteria and named sources:

| forecast | p (criterion A) | logged |
|---|---|---|
| CTH kernel (registered composite 0.4976; A-implied) | — | 2026-08-09 |
| Session hybrid | 0.17 | 2026-08-10 |
| Panel ensemble | 0.18 | 2026-08-10 |
| Market (pre-disclosure) | TBD | — |
| Every monthly update | dated series | — |

Also score criteria B (IMF WEO inflation) and C (UCDP/PRIO deaths) for the composite.
The comparison of the kernel's score against the hybrid/ensemble series is the final
empirical verdict of this entire project. Publish it either way.

## Automation (as of 2026-09-14)

The cadence is held by three durable Routines bound to the originating Claude session
(they survive container recycling and fire the session with context intact):

- **Monthly runbook cycle** — 14th of each month (trig_01RyjRX5mLob4if4ZpaLGTh5)
- **Quarterly panel re-poll** — Feb/May/Aug/Nov 14th (trig_01RznzGXuQzmqfXuHy9asCvW)
- **Resolution-day scoring** — one-shot, 2029-08-09 (trig_01N5nb5J5K4fdHHJd9kbqEsu)

Fired sessions run without MCP connectors — sufficient, since the cycles need only web
search, git, and (quarterly) subagents. Manage or pause them in the claude.ai Routines
UI. If the session is ever deleted, recreate them from this file's prompts.

## Update log

*(append below; never edit past entries)*

**2026-08-10 — baseline.** Panel ensemble 0.18 [0.10, 0.35]. Cruxes: IRGC-fracture
reporting credibility; creeping-coup construct discount. Market anchors: Polymarket
leadership-change 2wk hazard cooled 10.5%→3.2% Apr→Jul; permanent-peace 1.6%.

**2026-09-14 — update 1** (+35 days). Retrieval on the two cruxes:

*Crux (a), IRGC cohesion — resolves toward "held."* Expert consensus (Alfoneh, AGSIW:
"I have not observed signs of defections within the security apparatus"); nationalism
under foreign attack sustaining armed-forces cohesion; IRGC-IO threats against desertion
reveal anxiety but no unit-level fractures materialised in Aug–Sep. The opposition-sourced
fracture reports (NCRI/IranIntl) weighted by two panelists were not corroborated. This
was the panel's largest disagreement and it moves toward Opus's reading.

*Crux (b), creeping coup — no new signal.* Mojtaba consolidated ("regime quickly
consolidated under a new set of hard-liners"); formally in office since March 8; no
figurehead structure reported.

*War:* Pakistan-mediated ceasefire + June MOU still suppressing large-scale fighting
at day 198; strikes traded over violations; no settlement. No escalation toward
ground invasion (the only foreign-imposed replacement mechanism).

Increments (log-odds on 0.18): cohesion held one more month under max stress −0.20;
large-scale fighting stayed halted −0.05; 35 uneventful days of a front-loaded hazard
window −0.05. Net −0.30.

**Ensemble: 0.18 → 0.14  [0.08, 0.28].** Exceeds the soft ±0.10 monthly norm because
the period resolved the panel's principal crux, which is the stated exception.

Sources: [Britannica 2026 Iran war](https://www.britannica.com/event/2026-Iran-war) ·
[CFR Global Conflict Tracker](https://www.cfr.org/global-conflict-tracker/conflict/confrontation-between-united-states-and-iran) ·
[GlobalSecurity Day-198 OPREP](https://www.globalsecurity.org/military/ops/iran-war-oprep.htm) ·
[CSM on quelled protests](https://www.csmonitor.com/World/Middle-East/2026/0331/iran-war-irgc-basij-intimidation-protests) ·
[Critical Threats collapse-indicators tracker](https://www.criticalthreats.org/analysis/indicators-of-iranian-regime-collapse) ·
[FDD/LWJ on defection fears](https://www.fdd.org/analysis/2026/01/12/tehran-regime-fears-defections-as-irans-nationwide-movement-defies-containment/)

Panel re-poll: not due (quarterly; next ~2026-11). Market price: pending market creation.
