#!/usr/bin/env python3
"""Find every screen change and give Claude contact sheets to choose from.

  python3 frames.py WORK/video.mp4 --out WORK

Two passes, because screen recordings defeat plain scene detection:
  1. ffmpeg scene detection at a low threshold (0.10) catches tab switches, dialogs,
     page loads and slide changes.
  2. Interval sampling (every 20 s) inside any stretch longer than 60 s with no
     detected change catches slow scrolling through one long page, which is where
     most of the actual content lives in a product demo.
Candidates within 2.5 s of each other collapse to one, and each kept time is
shifted +1.5 s so the UI has settled (no half-loaded pages, no mid-fade slides).

Writes:
  WORK/candidates/c_<index>_<mm>m<ss>s.jpg   one frame per candidate
  WORK/candidates.json                       [{"t": seconds, "file": path}, ...]
  WORK/sheets/sheet_<n>.jpg                  3x4 contact sheets, 12 candidates each, in order
Look at the sheets (Read tool) and pick the frames that show new information.
"""
import argparse, glob, json, os, re, subprocess, sys

def scene_times(video, thr):
    log = subprocess.run(["ffmpeg", "-v", "info", "-i", video, "-vf", f"select='gt(scene,{thr})',showinfo",
                          "-vsync", "vfr", "-f", "null", "-"], capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r"pts_time:([0-9.]+)", log)]

def duration(video):
    err = subprocess.run(["ffmpeg", "-i", video], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    return int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3)) if m else 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--scene", type=float, default=0.10)
    ap.add_argument("--gap", type=float, default=60, help="sample inside static stretches longer than this")
    ap.add_argument("--every", type=float, default=20, help="sampling interval inside those stretches")
    ap.add_argument("--settle", type=float, default=1.5)
    ap.add_argument("--merge", type=float, default=2.5)
    a = ap.parse_args()
    dur = duration(a.video)
    times = sorted(set([0.3] + scene_times(a.video, a.scene)))
    keep = []
    for t in times:
        if not keep or t - keep[-1] >= a.merge:
            keep.append(t)
    keep = [t + a.settle for t in keep if t + a.settle < dur - 0.5]
    filled = []
    bounds = keep + [dur]
    for t0, t1 in zip(bounds, bounds[1:]):
        filled.append(t0)
        if t1 - t0 > a.gap:
            t = t0 + a.every
            while t < t1 - 5:
                filled.append(t); t += a.every
    filled = sorted(set(round(t, 2) for t in filled))
    cdir = os.path.join(a.out, "candidates"); sdir = os.path.join(a.out, "sheets")
    for d in (cdir, sdir):
        os.makedirs(d, exist_ok=True)
        for f in glob.glob(os.path.join(d, "*.jpg")): os.remove(f)
    cands = []
    for i, t in enumerate(filled, 1):
        s = int(t); name = f"c_{i:03d}_{s//60:02d}m{s%60:02d}s.jpg"
        path = os.path.join(cdir, name)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", a.video, "-frames:v", "1", "-q:v", "3", path])
        cands.append({"index": i, "t": t, "file": path})
    json.dump(cands, open(os.path.join(a.out, "candidates.json"), "w"), indent=1)
    files = [c["file"] for c in cands]
    for n in range(0, len(files), 12):
        chunk = files[n:n+12]
        lst = os.path.join(sdir, f"list_{n//12+1}.txt")
        open(lst, "w").write("".join(f"file '{f}'\n" for f in chunk))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                        "-vf", "scale=640:-1,tile=3x4:padding=6:margin=6", os.path.join(sdir, f"sheet_{n//12+1}.jpg")])
        os.remove(lst)
    sheets = sorted(glob.glob(os.path.join(sdir, "sheet_*.jpg")))
    print(json.dumps({"duration": dur, "scene_changes": len(keep), "candidates": len(cands), "sheets": sheets}, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
