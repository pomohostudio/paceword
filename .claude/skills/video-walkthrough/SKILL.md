---
name: video-walkthrough
description: "Summarise a screen-recorded video (Loom, YouTube, Vimeo, Google Drive, a local .mp4/.mov) into a chaptered write-up with a screenshot at every screen change that shows new information, each linked to its moment in the recording, plus an Obsidian note and, on request, a note written straight into the vault. Use this whenever the user shares a video link or file and wants a summary, recap, resume, notes, key points, \"what's in this video\", or screenshots of the slides/screens, especially for product demos, walkthroughs, tutorials, webinars and recorded meetings. Also use it when a plain transcript would lose the visual content (dashboards, forms, slides). Everything runs on-device: yt-dlp, ffmpeg and a local Whisper; no API keys."
---

# Video walkthrough

Turn a screen recording into a document someone can read in five minutes instead of watching for thirty: chapters in the video's own order, a short summary per chapter, and a screenshot wherever the screen changed to show something new. Every screenshot links back to that second of the recording, so the reader can verify anything.

Screen recordings defeat naive approaches. Scene detection alone misses slow scrolling through one long page, which is where most of a demo's content lives; fixed-interval sampling produces duplicates and catches half-loaded screens. The scripts here combine both and let you choose from contact sheets, which is faster and more accurate than either alone.

## Preflight

```
python3 "${CLAUDE_SKILL_DIR}/scripts/setup.py" --check
```

Silent means ready. Otherwise run it without `--check` for install commands. Needs `ffmpeg`, `yt-dlp` and a local Whisper engine. If the engine is missing, run `python3 "${CLAUDE_SKILL_DIR}/scripts/setup.py" --install`: it creates a private environment inside the skill folder and installs faster-whisper there (sherpa-onnx as fallback), which avoids Homebrew Python refusing pip installs and survives Python upgrades.

## Workflow

Work in a scratch directory, `WORK`. Run steps 1 and 2 in one go, start step 3 in the background immediately, and do step 4 while it runs.

**1. Fetch and shrink.**
```
python3 "${CLAUDE_SKILL_DIR}/scripts/fetch.py" "<url or path>" --out WORK
```
Produces `video.mp4` (960px, 3 fps), `audio.wav`, `meta.json`, and `captions.vtt` when the platform had captions. Login-gated videos: add `--cookies-from-browser chrome`. If the host is blocked by a proxy (Loom often is in cloud sessions), ask the user to download on their machine and pass the local file; a shrunk copy of a 25-minute recording is about 16 MB.

**2. Find screen changes.**
```
python3 "${CLAUDE_SKILL_DIR}/scripts/frames.py" WORK/video.mp4 --out WORK
```
Writes candidate frames and 3x4 contact sheets in `WORK/sheets/`. Expect roughly 3 to 5 candidates per minute of video.

**3. Transcribe, in the background.**
```
python3 "${CLAUDE_SKILL_DIR}/scripts/transcribe.py" WORK --model small
```
Uses platform captions when present, otherwise local Whisper. Budget 10 to 25 minutes for a 25-minute recording on a 4-core CPU; run it with `run_in_background` and keep working. Do not wait on it before reading the sheets.

**4. Read every contact sheet** with the Read tool and decide which candidates to keep. Keep a frame when it shows something the previous kept frame did not: a new slide, a new page or tab, a dialog, a form section scrolled into view, a generated result appearing. Drop loading spinners, mid-scroll frames that repeat content, and near-duplicates. When two candidates show the same screen, prefer the later one, where the UI has settled. Note the time of each keeper; you will need it for the spec. For a 25-minute product demo, 30 to 45 keepers is typical. Read a couple of keepers at full size (`WORK/candidates/...jpg`) to confirm legibility before committing.

**5. Read the transcript** once it is done. Whisper mangles names; fix the ones you can verify from the slides or the video metadata and say so in the transcript note.

**6. Write `WORK/spec.json`.** See the docstring at the top of `scripts/build.py` for the exact shape. Guidance that matters:
- Chapters follow the video's own order, with start and end timecodes from the transcript. Six to ten chapters for a half-hour demo.
- Paragraphs summarise what was said and shown, in the presenter's argument order, with their concrete examples kept (the actual event name, the actual number). Two or three paragraphs per chapter.
- Each kept frame goes in the chapter whose time range contains it, with a one-sentence caption naming what the screen shows and, when useful, why it matters.
- Five takeaways at the top: the claims a reader would repeat to a colleague.
- `meta` holds presenter, company, product, venue or customer, as pairs. `kicker` is the one-line context: platform, date, duration.

**7. Build.**
```
python3 "${CLAUDE_SKILL_DIR}/scripts/build.py" WORK/spec.json --out WORK/out
```
Adds `--vault "<vault path>"` when the user wants it in Obsidian. Produces:
- `<slug>.html`, a self-contained page with screenshots embedded. Publish it with the Artifact tool (favicon 🎬) and give the user the link.
- `<slug>-obsidian.zip`, a note plus an attachments folder, for a vault on another machine. Send it with SendUserFile.
- With `--vault`: the note under `Sources/<Platform>/Summaries/`, the transcript under `Sources/<Platform>/Transcripts/`, screenshots under `Sources/<Platform>/attachments/<slug>/`, with `platform`, `source` and `source/<platform>` tag in the frontmatter so it groups with the user's other sources. Never overwrites; existing names get a numeric suffix.

**8. Report** in a few lines: what the video is, what was delivered and where, how many screenshots, and any caveat (blocked host, uncertain names, sections you compressed).

## Judgement calls

- **Quality of the summary comes from the transcript, not the frames.** Frames show; the transcript explains. Write the paragraphs from the transcript and use frames as evidence.
- **Screenshots are for information, not decoration.** A slide with a new bullet is a keeper; the same dashboard at a different scroll position with nothing new is not. Titles and closing slides are keepers because they anchor the reader.
- **Long static stretches are usually the presenter scrolling a form or a document.** `frames.py` samples those every 20 seconds; if a stretch still looks under-sampled on the sheets, extract extra frames with `ffmpeg -ss <t> -i WORK/video.mp4 -frames:v 1 -q:v 5 out.jpg` rather than lowering the scene threshold globally.
- **Do not re-run transcription to fix a few names.** Fix them in `transcript.txt` and, if the summary relies on one, in the paragraphs.
- **Keep the user's machine tidy.** Everything lives in `WORK`; tell the user the path so they can delete it, or delete it yourself when they say they are done.

## Default vault

Antonio's vault: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/ASO`, with sources under `Sources/<Platform>` (YouTube, Instagram, Web already exist; Loom will be created on first use). When he says "add to Obsidian" or "put it in the vault", pass that path to `--vault`. On a machine that is not his Mac (a cloud session), the vault is unreachable; deliver the zip instead and say why.
