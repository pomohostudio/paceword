# Forecast Agent

A judgmental forecasting tool that came out of auditing "CTHmodules" (a framework claiming to
implement Asimov's Psychohistory). The audit found the framework anti-correlated with
independent reality. What survived is the *method* for forecasting honestly — that is what
this repo is now.

## What's here

- `FORECASTING.md` — the protocol the agent follows. Read this first.
- `README.md` — the full audit write-up and findings.
- `HYBRID.md`, `MARKET.md`, `RUNBOOK.md`, `docs/FRED.md` — supporting analysis and ops.
- `app/forecast-agent.html` — the self-serve app (chat interface), published as a Claude
  Artifact: https://claude.ai/artifact/KripzB3TeigMTviwQmMNK6
  The forecast **ledger lives in that artifact's database**, not in this repo.
- `scripts/`, `results/` — validation scripts and their JSON outputs.

## Non-negotiables when forecasting

Outside view before specifics. Increments in log-odds (each <= 0.3, total <= 0.5 unless the
evidence is extraordinary and you say so). A 90% interval is mandatory. Never self-extremize.
No round-number snapping. You are ONE correlated voice, not a crowd. Stay coherent with
forecasts already in the ledger — a superset event must be >= its subset.

The seven failure modes, every one of which was committed and caught during the audit:
circularity · coherence mistaken for validity · ranking vs probability · censored outcome
data · selection leaks · construct drift · fake independence.

## Triage test for any new "predict the future" method

1. Out-of-sample with a pre-registered resolution date and a named third-party source, or
   only retrodiction? (CTHmodules failed here.)
2. A proper score (Brier/log) against a baseline, or a story that merely "explains" events?
3. Circularity: are inputs independent of outcomes, or drawn from the same corpus? (r=0.96.)
4. Ranking vs probability — "ranks risk well" is not "is calibrated."
5. Auditable track record, or only the author's own scoring?

Fails 1 or 3 → it is another CTHmodules. Say so plainly.

## Tasks that can only run in a LOCAL session

This project is usually driven from a Claude Code *cloud* session, where Instagram is
egress-blocked and yt-dlp / ffmpeg / Whisper are absent. These need a local run:

1. **Reel walkthrough.** Run the `video-walkthrough` skill on
   https://www.instagram.com/reel/DdbRrbYv07m/
   (use the clean URL — drop any `?stkn=` share token, it may not resolve for a downloader).
   Commit the chaptered write-up into `docs/` so the cloud session can read it, then apply
   the triage test above.
2. **Large archive.** A >30MB zip on the user's machine must be read by local path — cloud
   sessions cannot see the local filesystem and chat upload caps at 30MB. Extract, summarise,
   and commit only what matters into `docs/`. Do NOT commit the archive itself.

Put outputs on this branch (`forecast-agent`) and push; the cloud session picks them up there.
