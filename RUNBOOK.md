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

### Step 1c — RESEARCH WATCH (every cycle)

Search for movement in the field itself: new ForecastBench results, the latest Metaculus
AI Benchmark quarterly (pros vs bots), new AIA-class systems or LLM-forecasting papers,
ViEWS challenge results — and PUBLIC FORECASTS from top human teams (Samotsvety, Swift
Centre, Good Judgment/FRI) relevant to Iran or regime stability. Their sites are
egress-blocked from the audit environment; search snippets quote them, which is how their
track record entered this project. When the field picture changes, update HYBRID.md's
research tables; when a top team publishes a relevant probability, log it as an
independent HUMAN anchor voice in the ensemble. Record the result each cycle even when
negative ("no field movement; no relevant public forecasts found").

### FRED (point-in-time macro data)

A local `fred` MCP server (see `docs/FRED.md`) provides FRED series with full vintage
history — `as_of` queries return data *as published on a date*, the only honest basis
for macro backtests. It runs on the owner's machine, so it is present in local sessions
and absent in cloud ones; use it whenever present. Project uses: cross-check resolution
criterion B (search for the World Bank Iran-inflation mirror via `fred_search_series`
before trusting an ID); vintage-honest inputs for any future macro covariates in the
forecaster; empire-question increments (DGS10, CPIAUCSL, FEDFUNDS). The rule that
matters most, now failure mode #8 in the forecast agent: never test against
current-vintage data.

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
- **Forecast Agent weekly ledger retrieval sweep** — Tuesdays (trig_01KHhqY7E64vya29TdbGZygq):
  the session reads the app's pending forecasts, retrieves current news for each, and
  writes documented revisions (history-appended, coherence-checked) into the app's
  database — supplying the retrieval the in-page agent structurally lacks

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

**2026-09-14 — update 1a** (routine's first firing, same day as manual update 1).
Retrieval/increments: NO-OP — duplicate of this morning's cycle; ensemble stays **0.14
[0.08, 0.28]**. Ran the two steps added to the cycle after update 1 was written:

*Data watch:* ForecastBench snapshot 2026-09-13 (fresh, yesterday) — new crowd anchors:
Manifold "Mojtaba supreme leader on 2027-01-01" **0.80** (leadership continuity priced
high; note construct — his personal ouster by internal succession would NOT resolve our
criterion A); Manifold "US and Iran at war on 2027-01-01" **0.58**; Polymarket "US–Iran
diplomatic meeting by 2027-03-31" **0.605**, "blockade ends by Oct 31" **0.365**. Crowd
picture: war grinds on, diplomacy expected, near-term leadership stable — consistent with
0.14 and with the resolved cohesion crux. No new expert-coding releases (next: FH/EIU
~Feb 2027, V-Dem ~Mar 2027).

*Research watch:* no Q3-2026 AIB results yet. FRI's ForecastBench extrapolation puts
LLM–superforecaster parity ~Nov 2026 [CI Dec 2025–Jan 2028] — the parity window is now.
New paper relevant to our panel design: "The Wisdom of Deliberating AI Crowds" (arXiv
2512.22625) — whether deliberation improves LLM forecasts; our panel is deliberately
non-deliberating (blind), revisit at the Nov re-poll. Field tables unchanged.

**2026-10-14 — update 2** (+30 days). *Branch note:* this cycle ran on `forecast-agent`;
the routine's stored prompt still names `cthmodules-audit`, which was renamed and the old
ref deleted on 2026-09-16.

*Crux (a), IRGC cohesion — stays resolved "held"; no re-opening.* No defection or
unit-level fracture reporting surfaced this cycle. The UK Commons briefing records security
forces as having remained loyal through the January crackdown. The only force-on-force
events are periphery insurgency, not fracture: three law-enforcement officers killed at
Shadegan (Aug), and IRGC clashes with armed men in Taftan county, Sistan-Baluchestan, on
13 Oct (no independently confirmed casualties). Baluch and Arab-minority militancy there is
longstanding and does not bear on cohesion of the central security apparatus.

*Crux (b), creeping coup — still NO, now with affirmative counter-evidence.* Mojtaba
Khamenei is exercising real decision authority: Iran's seven-day Hormuz proposal was
approved by him and the Supreme National Security Council before transmission through
Qatari mediators. A figurehead structure does not produce that.

*War:* bilateral kinetic pause since ~7–9 Sept, still holding at the Day-225 OPREP
(10 Oct) — no US/coalition strike on Iranian territory ashore, no Iranian attack on a host
state. On 8 Oct Trump announced no US strikes before the 3 Nov midterms. Diplomacy is
nonetheless deadlocked: Iran called the US response to its seven conditions "insufficient"
(Rezaei, 11 Oct); Hormuz stays closed; the nuclear-first vs Hormuz-first sequencing dispute
that killed the June MOU is untouched. Proxy track live (Houthi missile strike on Riyadh's
King Khalid airport ~10 Oct, deadliest in a Gulf state since the war began). No ground
invasion — the only foreign-imposed replacement mechanism — and none in prospect while the
pause holds.

*Economy — the cycle's one genuinely new development.* Free-market rial ~2.6–2.7m/USD
(Iran International 2.7m on 6 Oct; alanchand 2,605,000 on 13 Oct) against ~1.44–1.47m at
the late-December protest trigger: a further ~80% depreciation in nine months. CBI governor
Hemmati puts September y/y inflation at 83.8% (84.4% in Aug); independent readings say
~90%. The central bank is deploying up to $2bn in cash dollars to defend the currency and
Tehran is openly divided over doing so; the deputy governor calls the slide "temporary" and
blames "misleading expectations."

Increments (log-odds on 0.14):
- rial 1.44m → ~2.65m, inflation 52% → ~84–90%, reserves burned on a contested $2bn
  defence, oil revenue strangled by blockade — a compounding stressor over a 34-month
  horizon: **+0.20**
- but no new mass protest wave has materialised at these *worse* numbers, and January 2026
  already ran the natural experiment: a smaller shock produced a wave that was suppressed
  with security forces loyal. The dose-response from economic pain to regime change is weak
  here, and that is now evidenced rather than assumed: **−0.10**
- ~30 further uneventful days of a front-loaded hazard window, kinetic pause removing the
  invasion channel near-term: **−0.08**
- Mojtaba exercising decision authority through the SNSC (consolidation; also tells against
  the "authority over war policy is contested" reading): **−0.05**
- periphery insurgency logged, no increment: **0.00**

Net **−0.03**.

**Ensemble: 0.14 → 0.13  [0.07, 0.28].** Within the ±0.10 soft norm. The upper bound is
held at 0.28 rather than narrowed: the economic trajectory fattens the upper tail even as
the central estimate drifts down on elapsed time and demonstrated absorptive capacity.

*Data watch — NEGATIVE.* No qualifying new expert coding. V-Dem's 2026 wave ~Mar 2027;
Freedom House and EIU ~Feb 2027; ERT tracks V-Dem; no Polity/GWF-successor or UCDP release
in October. Logged as a finding in its own right: the **Critical Threats collapse-indicators
tracker this runbook sends me to has not been updated since 3 Feb 2026.** It bills itself as
a live, regularly updated product, so a cited instrument of this cycle is stale and must be
treated as non-informative rather than as "indicators unchanged." ForecastBench snapshots
not re-pulled this cycle (last: 2026-09-13).

*Crowd anchors (Polymarket, mid-Oct).* Iran leader at end-2026: Mojtaba Khamenei **88%**.
Leadership-change-by hazard: 4% (30 Sep), 6% (31 Oct), 9% (30 Nov). The regime-fall market's
own text: as of September 2026 "hard-line military and clerical networks remain in control,
with no scheduled events or verified internal fractures pointing to imminent change."
Construct caveat carried forward from update 1a: Mojtaba's *personal* ouster by internal
succession would NOT resolve criterion A, so these markets bound something broader than our
question and are logged as an anchor rather than averaged in. One Polymarket page returned
mutually inconsistent figures for "No Head of State" (5% vs 59%) — not used.

*Research watch — the field moved.* Spring 2026 FutureEval: Metaculus's 10 Pros still edged
the top-10 bots, but by only **+1.25 head-to-head points over 99 shared questions, not
statistically significant** — against p=0.00001 (Q2 2025) and p=0.001 (Q1 2025). Nine of ten
individual Pros still beat every individual bot. And on **5 Sept 2026 a bot won the Summer
2026 Metaculus Cup outright** (bots 1st/2nd/5th), though the Cup rewards coverage, earliness
and update frequency and is not a controlled comparison. Metaculus's objection is preserved:
most external parity claims rest on backtests against resolved questions, not live forward
evaluation. Consistent with FRI's extrapolated parity window (~Nov 2026, CI Dec 2025 –
Jan 2028) logged last cycle. HYBRID.md research tables updated accordingly.

*Human anchors — NEGATIVE.* No new published Samotsvety, Swift Centre or Good Judgment/FRI
probability on Iran regime stability found this cycle.

Panel re-poll: not due (quarterly; next ~2026-11). Market price: no criterion-A market
exists; crowd anchors logged above in lieu.

Sources: [GlobalSecurity Day-225 OPREP](https://www.globalsecurity.org/military/ops/iran-war-oprep.htm) ·
[Iran International on the $2bn rial defence](https://www.iranintl.com/en/202610076990) ·
[Iran International, dollar at 1.47m (Jan baseline)](https://www.iranintl.com/en/202601061682) ·
[UK Commons Library, Iran protests 2026](https://commonslibrary.parliament.uk/research-briefings/cbp-10462/) ·
[Critical Threats collapse indicators (stale, 3 Feb 2026)](https://www.criticalthreats.org/analysis/indicators-of-iranian-regime-collapse) ·
[Stimson, indicators of regime collapse](https://www.stimson.org/2026/what-would-be-indicators-of-regime-collapse-in-iran/) ·
[Elcano on protest resilience and containment](https://www.realinstitutoelcano.org/en/analyses/irans-2025-26-protests-resilience-and-political-containment/) ·
[Spring 2026 AIB / FutureEval](https://www.metaculus.com/futureeval/) ·
[Q2 AIB results](https://forum.effectivealtruism.org/posts/F2stjK9wHSy3HPEC9/q2-ai-benchmark-results-pros-maintain-clear-lead) ·
[Summer 2026 Metaculus Cup](https://hraness.com/reading/artificial-intelligence-now-beats-some-of-the-best-human-forecasters)

**2026-11-14 — update 3** (+31 days). *Branch note:* ran on `forecast-agent`; the routine's
stored prompt still names `cthmodules-audit`, renamed and deleted 2026-09-16.

*Crux (a), IRGC cohesion — stays resolved "held"; no re-opening.* No defection or
unit-level fracture reporting surfaced. Expert read unchanged from update 1 (Alfoneh: no
signs of defections in the security apparatus; one analyst allows "there were defections,
but they were not too dramatic"). Violence remains periphery insurgency — Shadegan (Aug),
Taftan in Sistan-Baluchestan (13 Oct). No new mass protest wave reported Sept–Nov.

*Crux (b), creeping coup — PARTIALLY RE-OPENED, as a coding question rather than an event.*
No new development, so no increment, but the analytic record deserves logging: Mojtaba was
reportedly elected by the Assembly of Experts under IRGC pressure (Iran International
sourced), decision-making is described as having "coalesced around security institutions"
with Mojtaba a coordinating figure rather than sole authority (Vatanka, MEI), and he "owes
his leadership and survival to the security forces" more than his father did. These
readings are dated Mar–May 2026 and are therefore not new evidence; what is new is
recognising that they bear on CODING. Update 2 scored −0.05 for Mojtaba exercising SNSC
authority as telling against a contested-authority reading. That was too quick: a garrison
state that keeps a clerical figurehead is exactly the case the resolution's "contested"
(0.5) band exists for. Flagged as a standing construct risk; resolve it by reading V-Dem's
own `v2x_regime` coding rules, not by argument.

*War:* US strikes resumed after an eight-week pause — 2–3 Nov (anti-aircraft facility,
Qeshm Island, Trump-confirmed) and 6 Nov (air defence near the strait), both officially
limited. October was the war's heaviest month (~28 attacks) but overwhelmingly IRGC strikes
on COMMERCIAL tankers, not on regime or state targets, so the pressure runs through the
economy rather than the survival apparatus. Hormuz ~4 transits/day against ~74 pre-war;
Brent ~$117. Iran's two-day reopening offer stands on seven conditions; it called the US
reply "unconvincing" (4 Nov). Qatar and Pakistan mediating; no ceasefire in force. No
ground invasion — still the only foreign-imposed replacement mechanism — and none in
prospect.

*Economy:* no new November print located; October figures stand (rial ~2.6–2.7m/USD against
~1.45m in late Dec 2025; Sept y/y inflation 83.8% official, ~90% independent; up to $2bn of
reserves committed to defending the currency amid open division in Tehran).

Increments (log-odds on 0.13):
- US strikes resumed; external pressure continues but stays limited and air-only: **+0.05**
- October attack peak = deeper economic strangulation over a 33-month horizon: **+0.05**
- diplomacy deteriorated ("unconvincing"), so the war and the siege persist: **+0.05**
- ~31 further days with no cohesion failure, no new protest wave and no succession
  instability, in a front-loaded hazard window: **−0.12**
- crux (b) coding risk logged, no increment: **0.00**

Net **+0.03** — essentially flat.

*PANEL RE-POLL (due; first since the 2026-08-10 baseline of 0.18).* Three forecasters run
blind on an identical factual brief, different models, none shown prior answers or each
other's:

| panelist | p | 90% interval |
|---|---|---|
| A | 0.14 | [0.05, 0.32] |
| B | 0.09 | [0.03, 0.22] |
| C | 0.07 | [0.03, 0.15] |

Median **0.09**, mean 0.10; the panel has moved 0.18 → 0.09 since August. Convergent themes
— and this is ONE species, so agreement here is correlation, not confirmation: all three
scored the survived succession as a large downward increment (−0.4 to −0.5), all three
scored the absence of a replacement vehicle downward (−0.3 to −0.4), all three scored the
currency and inflation collapse upward (~+0.3).

**The disagreement is the finding, and it is not to be averaged away.** The panel split on
the DIRECTION of the coding risk. B scored a garrison state coded "contested" as **+0.2
up**. A scored measurement inertia as **−0.3 down** (V-Dem and Polity code conservatively
and with lag, truncating the effective window well before 2029-08-09), and C similarly
**−0.2 down**. Same construct feature, opposite signs, from the same brief. This is a
construct-validity question the panel cannot settle; it is settled by reading the codebook.
A also uniquely named a second successful decapitation as the main upward path (+0.6),
noting Mojtaba's thinner independent clerical standing.

*ENSEMBLE across species* (per HYBRID.md: independence lives between species, not within):
statistical tool **0.17 [0.09, 0.32]** (FORECASTING.md, GWF party-based band, n=25
comparable); LLM panel median **0.09**; crowd/market construct-mismatched and logged as an
anchor only, not averaged; human anchors **none published**. Equal weight on the two usable
species gives 0.13.

**Ensemble: 0.13 → 0.13  [0.05, 0.30].** Central value unchanged, now resting on a fresh
panel rather than a three-month-old one. The interval is WIDENED at the low end (0.07 →
0.05): panel lows came in at 0.03/0.03/0.05 against the statistical voice's 0.09, and a 90%
interval should be at least as wide as the disagreement between reasonable reference
classes.

*Data watch — NEGATIVE.* V-Dem's 2026 wave ~Mar 2027; Freedom House and EIU ~Feb 2027; ERT
tracks V-Dem; no Polity/GWF-successor or UCDP release. **Second cycle running, the Critical
Threats collapse-indicators tracker this runbook cites has not been updated since
2026-02-03** — treat as non-informative, never as "indicators unchanged." ForecastBench
snapshots not re-pulled this cycle (last: 2026-09-13).

*Crowd anchors (Polymarket).* Iran leader at end-2026: Mojtaba Khamenei **88%**;
leadership-change hazard 4% (30 Sep), 6% (31 Oct), 9% (30 Nov). Construct caveat stands:
his personal ouster by internal succession would NOT resolve criterion A.

*Research watch — the field moved again.* **FRI now states outright that "AI models now
match superforecasters on ForecastBench", explicitly not by a statistically significant
margin**, and is running an October 2026 rematch with superforecasters returning against
the top AI forecasters; results unpublished. Best 2026 ForecastBench score 67 (GPT-5.5
high) against 65.3 (2025, GPT-5) and 61.5 (2023, GPT-4). A Claude 4.5 Sonnet bot placed
33rd of 1130 humans (top ~3%) in the Spring 2026 Cup. No Q3/Q4 2026 Metaculus AIB results
located. Worth noting for our own method: FRI's extrapolated parity date (~Nov 2026) has
landed near its central estimate, a small piece of evidence that capability extrapolation
of this kind is tractable. HYBRID.md research tables updated.

*Human anchors — NEGATIVE.* No new published Samotsvety, Swift Centre or Good Judgment/FRI
probability on Iran regime stability located.

Next panel re-poll: ~Feb 2027 (quarterly).

Sources: [GlobalSecurity Iran war OPREP](https://www.globalsecurity.org/military/ops/iran-war-oprep.htm) ·
[Al Jazeera, Iran calls US reply unconvincing](https://www.aljazeera.com/news/2026/11/4/iran-says-us-reply-to-hormuz-plan-unconvincing-trump-confirms-strikes) ·
[CFR, planning for Iran's leadership transition](https://www.cfr.org/reports/leadership-transition-in-iran) ·
[CSM, regime quells protests](https://www.csmonitor.com/World/Middle-East/2026/0331/iran-war-irgc-basij-intimidation-protests) ·
[Foreign Policy on Mojtaba's appointment](https://foreignpolicy.com/2026/03/11/ayatollah-mojtaba-khamenei-iran-war-supreme-leader/) ·
[Critical Threats collapse indicators (stale since 2026-02-03)](https://www.criticalthreats.org/analysis/indicators-of-iranian-regime-collapse) ·
[FRI: LLMs are closing the gap on human superforecasters](https://forecastingresearch.substack.com/p/llms-are-closing-the-gap-on-human) ·
[ForecastBench paper](https://faculty.wharton.upenn.edu/wp-content/uploads/2026/02/ForecastBench_A_Dynamic_.pdf) ·
[Metaculus, AI forecasting in 2026](https://www.metaculus.com/notebooks/43363/ai-forecasting-in-2026/)

**2026-11-15 — update 3a, canonical panel re-poll ATTEMPTED AND BLOCKED.** No change to the
number; this entry exists so the protocol record is honest.

The separate quarterly re-poll Routine (`trig_01RznzGXuQzmqfXuHy9asCvW`) fired 30 minutes
after the monthly cycle and specifies the registered protocol more fully than the monthly
one does. Comparing the two specs surfaced a real deviation in update 3's panel, recorded
here against that panel's number:

**Update 3's re-poll departed from the Version 3.1 protocol in three ways.** Version 3.1
states that each panelist "ran its own news retrieval and surfaced evidence the others
missed", over four models, with the shared outside-view scenario table. Update 3 instead
used (i) three models not four, (ii) a single situation brief written by the orchestrator,
and (iii) an explicit instruction NOT to search. (ii) is the one that matters: a panel fed
one author's brief shares that author's framing. The brief led with stability facts — the
succession survived, the forces stayed loyal, there is no coherent opposition — and all
three panelists then returned large downward increments on exactly those points. So the
reported move from 0.18 (Aug) to a 0.09 median (Nov) is **confounded with orchestrator
anchoring and is not apples-to-apples with the August baseline**, which used independent
retrieval. Treat update 3's 0.09 as an upper bound on how much of that drop is real
updating.

**The canonical re-run could not be executed.** Four panelists (haiku/sonnet/opus/fable,
own retrieval, scenario table, no prior numbers) were launched three times on 11-14 and
11-15. All three batches were destroyed by container restarts before any agent reported;
`run_in_background: false` was not honored by the harness, so the work could not be pinned
inside a single turn. Ten agent-runs produced zero results. No canonical November panel
exists.

**Standing position.** The logged ensemble remains **0.13 [0.05, 0.30]** from update 3,
unchanged. Its LLM-panel species input (median 0.09) now carries the documented protocol
deviation above and should be weighted accordingly — the statistical species (0.17) is the
better-founded of the two inputs this cycle. The canonical re-poll is DEFERRED to the next
cycle, where it should be run with the panelists executed in a way that survives a restart,
or in a session where background agents are stable.

**Process finding for the owner.** Two Routines now schedule the same quarterly re-poll:
the monthly cycle's step 3 and the dedicated quarterly Routine. Recommend keeping the
dedicated one, which carries the fuller protocol spec, and dropping the panel step from the
monthly cycle. Both Routines still name the `cthmodules-audit` branch, renamed and deleted
on 2026-09-16; three cycles have now run on `forecast-agent` instead. Neither change made
here: editing a scheduled trigger is the owner's call.
