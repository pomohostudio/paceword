#!/usr/bin/env python3
"""Turn a spec (written by Claude after reading the transcript and sheets) into deliverables.

  python3 build.py WORK/spec.json --out WORK/out [--vault "~/Library/.../ASO"] [--platform loom]

Outputs in --out:
  <slug>.html                 self-contained page, screenshots embedded, each linked to its moment in the source
  <slug>-obsidian.zip         note + attachments folder, for a vault
With --vault, also writes into the vault using the per-platform layout yt2obsidian uses:
  <vault>/Sources/<Platform>/Summaries/<Title> (<id>).md          summary with embedded screenshots
  <vault>/Sources/<Platform>/Transcripts/Transcript <Title> (<id>).md
  <vault>/Sources/<Platform>/attachments/<slug>/<nn>-<mm>m<ss>s.jpg
Existing files are never overwritten; a numeric suffix is added instead.

Spec shape (see SKILL.md for guidance on writing it):
{
  "title": "Narrative OS Walkthrough",
  "source_url": "https://www.loom.com/share/...",      # optional; frames link to ?t=<seconds> for Loom/YouTube
  "video": "WORK/video.mp4",
  "platform": "loom",                                   # loom | youtube | vimeo | local | ...
  "kicker": "Loom demo, recorded 11 Sep 2026, 25:40",
  "meta": [["Presenter", "Chris Lowder, co-founder, Lowder-Tascarella Hospitality"], ["Product", "Hearthline / Narrative OS"]],
  "lede": "One paragraph saying what the video is and why it matters.",
  "takeaways": ["...", "..."],
  "chapters": [
    {"title": "The pitch", "start": "00:00", "end": "03:45",
     "paragraphs": ["...", "..."],
     "frames": [{"t": 1.8, "caption": "Title slide ..."}, {"t": 21.8, "caption": "..."}]}
  ],
  "transcript": "WORK/transcript.txt",
  "tags": ["hospitality"]                               # optional extra Obsidian tags
}
"""
import argparse, base64, html, json, os, re, shutil, subprocess, sys, zipfile

def tstr(s): s = int(s); return f"{s//60:02d}:{s%60:02d}"
def slugify(t): return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:60]

def jump(url, s):
    if not url: return None
    if "youtube.com" in url or "youtu.be" in url:
        sep = "&" if "?" in url else "?"; return f"{url}{sep}t={int(s)}s"
    if "loom.com" in url or "vimeo.com" in url:
        base = url.split("?")[0]; return f"{base}?t={int(s)}"
    return url

def grab(video, t, path):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", "-q:v", "5", path])

def unique(path):
    if not os.path.exists(path): return path
    root, ext = os.path.splitext(path); n = 2
    while os.path.exists(f"{root} ({n}){ext}"): n += 1
    return f"{root} ({n}){ext}"

CSS = """
:root{--ground:#F3F4F1;--surface:#FFFFFF;--ink:#1C2536;--muted:#5B6473;--line:#D9DBD6;--accent:#17646B;--accent-ink:#0F474C;--brass:#8A6E33;--shadow:0 1px 2px rgba(28,37,54,.06),0 8px 24px rgba(28,37,54,.06)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--ground:#141A22;--surface:#1C2430;--ink:#E8EAE6;--muted:#A4ACB8;--line:#2A3442;--accent:#5FB3B8;--accent-ink:#8FD3D6;--brass:#C9A45C;--shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.35)}}
:root[data-theme="dark"]{--ground:#141A22;--surface:#1C2430;--ink:#E8EAE6;--muted:#A4ACB8;--line:#2A3442;--accent:#5FB3B8;--accent-ink:#8FD3D6;--brass:#C9A45C;--shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.35)}
*{box-sizing:border-box}
body{background:var(--ground);color:var(--ink);font-family:"Source Sans 3",system-ui,-apple-system,"Segoe UI",sans-serif;font-size:17px;line-height:1.55;padding-inline:clamp(16px,4vw,40px);padding-block:0 64px}
a{color:var(--accent-ink)}
.wrap{max-width:1080px;margin:0 auto}
header.hero{padding-block:40px 24px;border-bottom:1px solid var(--line)}
.kicker{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--brass);font-weight:500}
h1{font-family:Fraunces,Georgia,"Times New Roman",serif;font-weight:600;font-size:clamp(34px,5vw,54px);line-height:1.05;letter-spacing:-.01em;margin:10px 0 14px;text-wrap:balance;max-width:20ch}
.meta{display:flex;flex-wrap:wrap;gap:8px 22px;color:var(--muted);font-size:15px}
.meta b{color:var(--ink);font-weight:600}
.lede{max-width:66ch;font-size:19px;margin:18px 0 0}
.takeaways{padding-block:28px;border-bottom:1px solid var(--line)}
.takeaways h3{font-family:Fraunces,Georgia,serif;font-weight:600;font-size:22px;margin:0 0 10px}
.takeaways ol{margin:0;padding-left:1.2em;display:grid;gap:8px;max-width:66ch}
.takeaways li::marker{color:var(--brass);font-family:"IBM Plex Mono",monospace;font-weight:500}
nav.chapters{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--ground);border-bottom:1px solid var(--line);display:flex;gap:4px;overflow-x:auto;padding-block:10px;scrollbar-width:none}
nav.chapters::-webkit-scrollbar{display:none}
nav.chapters a{white-space:nowrap;text-decoration:none;color:var(--muted);font-size:14px;font-weight:600;padding:6px 12px;border-radius:999px;border:1px solid transparent}
nav.chapters a:hover,nav.chapters a:focus-visible{color:var(--accent-ink);border-color:var(--line);background:var(--surface);outline:none}
.chapter{padding-block:40px 8px;border-bottom:1px solid var(--line)}
.eyebrow{display:flex;align-items:center;gap:8px}
.eyebrow .dash{width:22px;height:1px;background:var(--brass)}
.tc{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace;font-size:12.5px;font-weight:500;color:var(--brass);letter-spacing:.02em;font-variant-numeric:tabular-nums}
h2{font-family:Fraunces,Georgia,serif;font-weight:600;font-size:clamp(26px,3.2vw,34px);line-height:1.1;margin:8px 0 14px;text-wrap:balance}
.prose{max-width:68ch}.prose p{margin:0 0 14px}
.figs{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px 20px;margin-top:22px;padding-bottom:28px}
@media (max-width:760px){.figs{grid-template-columns:1fr}}
figure{margin:0;display:flex;flex-direction:column;gap:9px}
figure a,figure .img{display:block;line-height:0;background:var(--surface);border:1px solid var(--line);box-shadow:var(--shadow)}
figure img{width:100%;height:auto;display:block;max-width:100%}
figcaption{font-size:14px;line-height:1.45;color:var(--muted);display:flex;gap:10px;align-items:baseline}
figcaption .tc{flex:none}
details.transcript{margin-top:36px;border-top:1px solid var(--line);padding-top:18px}
details.transcript summary{cursor:pointer;font-family:Fraunces,Georgia,serif;font-weight:600;font-size:22px;list-style:none;display:flex;align-items:center;gap:10px}
details.transcript summary::-webkit-details-marker{display:none}
details.transcript summary::before{content:"+";font-family:"IBM Plex Mono",monospace;color:var(--brass);width:1em}
details[open].transcript summary::before{content:"\\2212"}
details.transcript .tr{max-width:72ch;margin-top:14px;font-size:15.5px}
details.transcript .tr p{margin:0 0 10px;display:grid;grid-template-columns:52px 1fr;gap:10px}
.note{color:var(--muted);font-size:14px;max-width:68ch;margin-top:10px}
footer{margin-top:36px;color:var(--muted);font-size:14px}
@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", required=True)
    ap.add_argument("--vault", help="Obsidian vault root; writes note, transcript and attachments there")
    ap.add_argument("--vault-sources", default="Sources", help="folder inside the vault holding per-platform folders")
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    os.makedirs(a.out, exist_ok=True)
    title = spec["title"]; slug = slugify(title); url = spec.get("source_url")
    platform = spec.get("platform") or ("youtube" if url and "youtu" in url else "loom" if url and "loom" in url else "video")
    video = spec["video"]
    # screenshots
    shots = os.path.join(a.out, "shots"); shutil.rmtree(shots, ignore_errors=True); os.makedirs(shots)
    n = 0; frames = []
    for ch in spec["chapters"]:
        for fr in ch["frames"]:
            n += 1; t = float(fr["t"]); s = int(t)
            name = f"{n:02d}-{s//60:02d}m{s%60:02d}s.jpg"; path = os.path.join(shots, name)
            grab(video, t, path); fr["_file"] = path; fr["_name"] = name; fr["_n"] = n; frames.append(fr)
    transcript = []
    if spec.get("transcript") and os.path.exists(spec["transcript"]):
        for l in open(spec["transcript"]).read().strip().split("\n"):
            m = re.match(r"\[(\d+:\d+)\]\s*(.*)", l)
            if m: transcript.append((m.group(1), m.group(2)))
    # ---- HTML ----
    def b64(p): return "data:image/jpeg;base64," + base64.b64encode(open(p, "rb").read()).decode()
    def fig(fr):
        t = float(fr["t"]); j = jump(url, t)
        img = f'<img src="{b64(fr["_file"])}" alt="Screenshot at {tstr(t)}" loading="lazy">'
        box = f'<a href="{html.escape(j)}" target="_blank" rel="noopener">{img}</a>' if j else f'<div class="img">{img}</div>'
        return f'<figure id="f{fr["_n"]}">{box}<figcaption><span class="tc">{tstr(t)}</span>{html.escape(fr["caption"])}</figcaption></figure>'
    nav = "".join(f'<a href="#c{i+1}">{html.escape(c["title"])}</a>' for i, c in enumerate(spec["chapters"]))
    secs = []
    for i, c in enumerate(spec["chapters"]):
        ps = "".join(f"<p>{html.escape(p)}</p>" for p in c.get("paragraphs", []))
        secs.append(f'<section class="chapter" id="c{i+1}"><div class="eyebrow"><span class="tc">{c.get("start","")}</span><span class="dash"></span><span class="tc">{c.get("end","")}</span></div><h2>{html.escape(c["title"])}</h2><div class="prose">{ps}</div><div class="figs">{"".join(fig(f) for f in c["frames"])}</div></section>')
    meta = "".join(f'<span>{html.escape(k)} <b>{html.escape(v)}</b></span>' for k, v in spec.get("meta", []))
    if url: meta += f'<span><a href="{html.escape(url)}" target="_blank" rel="noopener">Open the recording</a></span>'
    tk = "".join(f"<li>{html.escape(t)}</li>" for t in spec.get("takeaways", []))
    tr = "".join(f'<p><span class="tc">{html.escape(a_)}</span>{html.escape(b_)}</p>' for a_, b_ in transcript)
    tr_block = f'<details class="transcript"><summary>Full transcript</summary><p class="note">{html.escape(spec.get("transcript_note", "Transcribed locally with Whisper; timestamps mark the start of each block. Proper nouns may be mangled."))}</p><div class="tr">{tr}</div></details>' if transcript else ""
    page = (f'<title>{html.escape(title)}</title>\n<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@500&display=swap">\n<style>{CSS}</style>\n'
            f'<div class="wrap"><header class="hero"><div class="kicker">{html.escape(spec.get("kicker",""))}</div><h1>{html.escape(title)}</h1><div class="meta">{meta}</div><p class="lede">{html.escape(spec.get("lede",""))}</p></header>'
            f'<div class="takeaways"><h3>What matters</h3><ol>{tk}</ol></div><nav class="chapters" aria-label="Chapters">{nav}</nav>{"".join(secs)}{tr_block}'
            f'<footer>{len(frames)} screenshots, one at each screen change with new information.</footer></div>\n')
    html_path = os.path.join(a.out, f"{slug}.html"); open(html_path, "w").write(page)
    # ---- Markdown ----
    tags = [f"source/{platform}"] + list(spec.get("tags", []))
    fm = ["---", f"title: {title}", "type: source", f"platform: {platform}"] + ([f"source: {url}"] if url else []) + \
         [f"{k.lower().replace(' ', '_')}: {v}" for k, v in spec.get("meta", [])] + ["tags:"] + [f"  - {t}" for t in tags] + ["---", ""]
    def md_body(attach_prefix):
        md = [f"# {title}", "", spec.get("lede", ""), ""]
        if url: md += [f"[Open the recording]({url})", ""]
        if spec.get("takeaways"): md += ["## What matters", ""] + [f"{i+1}. {t}" for i, t in enumerate(spec["takeaways"])] + [""]
        for c in spec["chapters"]:
            md += [f"## {c['title']} ({c.get('start','')}–{c.get('end','')})", ""] + [p + "\n" for p in c.get("paragraphs", [])]
            for fr in c["frames"]:
                j = jump(url, float(fr["t"])); link = f" ([jump]({j}))" if j else ""
                md += [f"![[{attach_prefix}{fr['_name']}]]", f"*{tstr(float(fr['t']))} — {fr['caption']}*{link}", ""]
        return md
    # bundle zip
    bdir = os.path.join(a.out, "bundle", title); shutil.rmtree(os.path.join(a.out, "bundle"), ignore_errors=True)
    os.makedirs(os.path.join(bdir, "attachments"))
    for fr in frames: shutil.copy(fr["_file"], os.path.join(bdir, "attachments", fr["_name"]))
    body = fm + md_body("")
    if transcript: body += ["## Full transcript", ""] + [f"**{a_}** {b_}  " for a_, b_ in transcript]
    open(os.path.join(bdir, f"{title}.md"), "w").write("\n".join(body))
    zpath = os.path.join(a.out, f"{slug}-obsidian.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(bdir):
            for f in files:
                p = os.path.join(root, f); z.write(p, os.path.relpath(p, os.path.join(a.out, "bundle")))
    result = {"html": html_path, "obsidian_zip": zpath, "screenshots": len(frames)}
    # ---- vault ----
    if a.vault:
        vault = os.path.expanduser(a.vault)
        pf = os.path.join(vault, a.vault_sources, platform.capitalize())
        sid = spec.get("id") or (re.sub(r"[^A-Za-z0-9_-]", "", url.rstrip("/").split("/")[-1].split("?")[0]) if url else slug[:11])
        att = os.path.join(pf, "attachments", slug); os.makedirs(att, exist_ok=True)
        for fr in frames: shutil.copy(fr["_file"], os.path.join(att, fr["_name"]))
        os.makedirs(os.path.join(pf, "Summaries"), exist_ok=True); os.makedirs(os.path.join(pf, "Transcripts"), exist_ok=True)
        summ = unique(os.path.join(pf, "Summaries", f"{title} ({sid}).md"))
        open(summ, "w").write("\n".join(fm + md_body("")))
        if transcript:
            trp = unique(os.path.join(pf, "Transcripts", f"Transcript {title} ({sid}).md"))
            open(trp, "w").write("\n".join(fm + [f"# Transcript: {title}", "", f"Summary: [[{os.path.basename(summ)[:-3]}]]", ""] + [f"**{a_}** {b_}  " for a_, b_ in transcript]))
            result["vault_transcript"] = trp
        result["vault_summary"] = summ; result["vault_attachments"] = att
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
