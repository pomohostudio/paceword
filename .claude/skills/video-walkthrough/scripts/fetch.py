#!/usr/bin/env python3
"""Get a video into a working directory, shrink it, and split out the audio.

  python3 fetch.py <url-or-path> --out WORK [--cookies-from-browser chrome] [--keep-full]

Writes into WORK/:
  video.mp4        960px-wide, 3 fps, small enough to move around (source kept as source.* unless --no-keep)
  audio.wav        mono 16 kHz, what every transcription engine wants
  info.json        yt-dlp metadata when the input was a URL (title, uploader, duration, webpage_url)
  captions.vtt     platform captions when yt-dlp found any (saves a Whisper run)

Why shrink: screen recordings are mostly static, so 3 fps at 960px keeps every
screen change legible while cutting a 25-minute Loom from ~150 MB to ~16 MB.
Scene detection and screenshots come from this file; audio is untouched.
"""
import argparse, glob, json, os, shutil, subprocess, sys

def run(cmd, **kw):
    return subprocess.run(cmd, check=False, **kw)

def ytdlp_cmd():
    return ["yt-dlp"] if shutil.which("yt-dlp") else [sys.executable, "-m", "yt_dlp"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cookies-from-browser", help="chrome, safari, firefox... for login-gated videos")
    ap.add_argument("--width", type=int, default=960)
    ap.add_argument("--fps", type=int, default=3)
    ap.add_argument("--no-keep", action="store_true", help="delete the full-size source after shrinking")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    src = a.src
    is_url = src.startswith(("http://", "https://"))
    if is_url:
        cmd = ytdlp_cmd() + ["--no-playlist", "-o", os.path.join(a.out, "source.%(ext)s"),
               "--write-info-json", "--write-subs", "--write-auto-subs", "--sub-langs", "en.*,pt.*,es.*",
               "--sub-format", "vtt"]
        if a.cookies_from_browser:
            cmd += ["--cookies-from-browser", a.cookies_from_browser]
        cmd += ["--", src]
        r = run(cmd)
        srcs = [p for p in glob.glob(os.path.join(a.out, "source.*")) if not p.endswith((".json", ".vtt", ".part", ".ytdl"))]
        if not srcs:
            print("download failed. If the host is blocked by a proxy, download on another machine and pass the local file.", file=sys.stderr)
            return 1
        src = srcs[0]
        for p in glob.glob(os.path.join(a.out, "source.*.json")):
            shutil.move(p, os.path.join(a.out, "info.json"))
        vtts = sorted(glob.glob(os.path.join(a.out, "source.*.vtt")))
        if vtts:
            shutil.move(vtts[0], os.path.join(a.out, "captions.vtt"))
    else:
        src = os.path.expanduser(src)
        if not os.path.exists(src):
            print(f"not found: {src}", file=sys.stderr); return 1
    video = os.path.join(a.out, "video.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", f"scale={a.width}:-2", "-r", str(a.fps),
         "-c:v", "libx264", "-crf", "30", "-preset", "fast", "-an", video])
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", os.path.join(a.out, "audio.wav")])
    if a.no_keep and is_url:
        os.remove(src)
    dur = subprocess.run(["ffmpeg", "-i", video], capture_output=True, text=True).stderr
    import re
    m = re.search(r"Duration: (\d+):(\d+):(\d+)", dur)
    secs = int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3)) if m else 0
    meta = {"source": a.src, "duration_seconds": secs, "video": video, "audio": os.path.join(a.out, "audio.wav")}
    if os.path.exists(os.path.join(a.out, "info.json")):
        try:
            info = json.load(open(os.path.join(a.out, "info.json")))
            meta.update({k: info.get(k) for k in ("title", "uploader", "upload_date", "webpage_url", "extractor_key") if info.get(k)})
        except Exception:
            pass
    json.dump(meta, open(os.path.join(a.out, "meta.json"), "w"), indent=2)
    print(json.dumps(meta, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
