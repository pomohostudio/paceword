#!/usr/bin/env python3
"""Preflight for the video-walkthrough skill.

  python3 setup.py --check     # silent on success, exit 2 if something is missing
  python3 setup.py             # same, plus install hints
  python3 setup.py --install   # create a private Python environment inside the skill folder and
                               # install faster-whisper into it (falls back to sherpa-onnx)

Why a private environment: Homebrew's Python refuses plain `pip install` (PEP 668),
and a system-wide Whisper can silently disappear when Homebrew upgrades Python.
The venv lives at <skill>/.venv, so transcribe.py always finds the same engine.
"""
import importlib.util, os, platform, shutil, subprocess, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV = os.path.join(SKILL, ".venv")
VPY = os.path.join(VENV, "bin", "python")

def have_bin(name): return shutil.which(name) is not None
def have_mod(name): return importlib.util.find_spec(name) is not None

def venv_has(mod):
    if not os.path.exists(VPY): return False
    return subprocess.run([VPY, "-c", f"import {mod}"], capture_output=True).returncode == 0

def engines():
    found = [e for e in ("faster_whisper", "whisper", "mlx_whisper", "sherpa_onnx") if have_mod(e)]
    found += [b for b in ("whisper", "mlx_whisper", "whisper-cli") if have_bin(b)]
    found += [f"venv:{m}" for m in ("faster_whisper", "sherpa_onnx", "whisper") if venv_has(m)]
    return found

def install():
    if not os.path.exists(VPY):
        print(f"[video-walkthrough] creating {VENV}")
        subprocess.run([sys.executable, "-m", "venv", VENV], check=True)
    pip = [VPY, "-m", "pip", "install", "-q", "--upgrade"]
    subprocess.run(pip + ["pip"], check=False)
    for pkgs, mod in ((["faster-whisper"], "faster_whisper"), (["sherpa-onnx", "numpy"], "sherpa_onnx")):
        print(f"[video-walkthrough] installing {' '.join(pkgs)} ...")
        r = subprocess.run(pip + pkgs)
        if r.returncode == 0 and venv_has(mod):
            print(f"[video-walkthrough] ready. transcription engine: {mod} (private environment)")
            return 0
        print(f"[video-walkthrough] {pkgs[0]} did not install; trying the next engine")
    print("[video-walkthrough] no engine could be installed; send this output to Claude")
    return 2

def main():
    if "--install" in sys.argv:
        return install()
    check = "--check" in sys.argv
    missing = []
    if not have_bin("ffmpeg"): missing.append("ffmpeg")
    if not have_bin("yt-dlp") and not have_mod("yt_dlp"): missing.append("yt-dlp")
    if not engines(): missing.append("whisper engine")
    if not missing: return 0
    print(f"[video-walkthrough] missing: {', '.join(missing)}")
    if check: return 2
    mac = platform.system() == "Darwin"
    print("\nInstall hints:")
    if "ffmpeg" in missing:
        print("  ffmpeg:  " + ("brew install ffmpeg" if mac else "sudo apt install ffmpeg"))
    if "yt-dlp" in missing:
        print("  yt-dlp:  " + ("sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos -o /usr/local/bin/yt-dlp && sudo chmod a+rx /usr/local/bin/yt-dlp" if mac else "pip install --user yt-dlp"))
    if "whisper engine" in missing:
        print(f"  whisper: python3 {os.path.abspath(__file__)} --install")
    return 2

if __name__ == "__main__":
    sys.exit(main())
