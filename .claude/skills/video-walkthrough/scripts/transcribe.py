#!/usr/bin/env python3
"""Timestamped transcript, on-device, no API key.

  python3 transcribe.py WORK --model small

Order of preference:
  1. WORK/captions.vtt from the platform (instant, and usually better than Whisper for names)
  2. faster-whisper   (CPU, int8)              model from Hugging Face
  3. mlx-whisper      (Apple Silicon)          model from Hugging Face
  4. openai-whisper   (CPU/GPU, needs torch)   model from OpenAI's CDN
  4b. whisper / mlx_whisper command on PATH (same engines installed via pipx or Homebrew)
  5. sherpa-onnx      (CPU)                    model tarball from GitHub releases; the fallback
                                               when Hugging Face is blocked by a corporate proxy

Writes WORK/transcript.txt ("[mm:ss] text" per block) and WORK/transcript.json.
Run it in the background: a 25-minute recording takes 10-25 minutes on a 4-core CPU.
Whisper mangles proper nouns; fix names you can verify from the slides.
"""
import argparse, importlib.util, json, os, re, subprocess, sys, urllib.request

# Prefer the skill's private environment (created by setup.py --install) when it exists.
_VPY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv", "bin", "python")
if os.path.exists(_VPY) and os.path.realpath(sys.executable) != os.path.realpath(_VPY) and not os.environ.get("VW_NO_VENV"):
    os.execv(_VPY, [_VPY] + sys.argv)

def have(m): return importlib.util.find_spec(m) is not None
def ts(s): s = int(s); return f"{s//60:02d}:{s%60:02d}"

def write(out, segs):
    with open(os.path.join(out, "transcript.txt"), "w") as f:
        for s in segs: f.write(f"[{ts(s['start'])}] {s['text']}\n")
    json.dump(segs, open(os.path.join(out, "transcript.json"), "w"))

def from_vtt(path):
    txt = open(path, encoding="utf-8", errors="ignore").read()
    segs, last = [], ""
    for block in re.split(r"\n\s*\n", txt):
        m = re.search(r"(\d+):(\d+):([\d.]+)\s*-->", block) or re.search(r"(\d+):([\d.]+)\s*-->", block)
        if not m: continue
        g = m.groups(); start = (int(g[0])*3600 + int(g[1])*60 + float(g[2])) if len(g) == 3 else int(g[0])*60 + float(g[1])
        lines = [re.sub(r"<[^>]+>", "", l).strip() for l in block.split("\n") if "-->" not in l and l.strip() and not l.strip().isdigit()]
        text = " ".join(lines).strip()
        if text and text != last:
            segs.append({"start": start, "text": text}); last = text
    return segs

def faster(audio, model):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio, vad_filter=True, beam_size=1)
    return [{"start": s.start, "text": s.text.strip()} for s in segs]

def mlx(audio, model):
    import mlx_whisper
    r = mlx_whisper.transcribe(audio, path_or_hf_repo=f"mlx-community/whisper-{model}-mlx")
    return [{"start": s["start"], "text": s["text"].strip()} for s in r["segments"]]

def openai(audio, model):
    import whisper
    r = whisper.load_model(model).transcribe(audio)
    return [{"start": s["start"], "text": s["text"].strip()} for s in r["segments"]]

def cli(audio, model, out):
    """openai-whisper or mlx-whisper installed as a command rather than an importable module."""
    import shutil, subprocess
    exe = shutil.which("whisper") or shutil.which("mlx_whisper")
    if not exe: raise RuntimeError("no whisper command on PATH")
    subprocess.run([exe, audio, "--model", model, "--output_format", "json", "--output_dir", out, "--verbose", "False"], check=True)
    r = json.load(open(os.path.join(out, "audio.json")))
    return [{"start": s["start"], "text": s["text"].strip()} for s in r["segments"]]

def sherpa(audio, model, out):
    import wave, numpy as np, sherpa_onnx as so, tarfile
    d = os.path.join(out, f"sherpa-onnx-whisper-{model}")
    if not os.path.isdir(d):
        url = f"https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-{model}.tar.bz2"
        tb = d + ".tar.bz2"; print("downloading", url, file=sys.stderr)
        urllib.request.urlretrieve(url, tb)
        tarfile.open(tb).extractall(out); os.remove(tb)
    rec = so.OfflineRecognizer.from_whisper(encoder=f"{d}/{model}-encoder.int8.onnx", decoder=f"{d}/{model}-decoder.int8.onnx",
                                            tokens=f"{d}/{model}-tokens.txt", language="", task="transcribe", num_threads=os.cpu_count() or 4)
    w = wave.open(audio); sr = w.getframerate()
    a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    chunk = 25 * sr; segs = []
    for i in range(0, len(a), chunk):
        s = rec.create_stream(); s.accept_waveform(sr, a[i:i+chunk]); rec.decode_stream(s)
        segs.append({"start": i / sr, "text": s.result.text.strip()})
        write(out, segs)
    return segs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--model", default="small", help="tiny|base|small|medium; small is the accuracy/speed sweet spot on CPU")
    ap.add_argument("--engine", choices=["auto", "vtt", "faster", "mlx", "openai", "cli", "sherpa"], default="auto")
    a = ap.parse_args()
    audio = os.path.join(a.work, "audio.wav"); vtt = os.path.join(a.work, "captions.vtt")
    order = [a.engine] if a.engine != "auto" else ["vtt", "faster", "mlx", "openai", "cli", "sherpa"]
    for eng in order:
        try:
            if eng == "vtt":
                if not os.path.exists(vtt): continue
                segs = from_vtt(vtt)
            elif eng == "faster":
                if not have("faster_whisper"): continue
                segs = faster(audio, a.model)
            elif eng == "mlx":
                if not have("mlx_whisper"): continue
                segs = mlx(audio, a.model)
            elif eng == "openai":
                if not have("whisper"): continue
                segs = openai(audio, a.model)
            elif eng == "cli":
                import shutil
                if not (shutil.which("whisper") or shutil.which("mlx_whisper")): continue
                segs = cli(audio, a.model, a.work)
            else:
                if not have("sherpa_onnx"): continue
                segs = sherpa(audio, a.model, a.work)
            write(a.work, segs)
            print(json.dumps({"engine": eng, "segments": len(segs)}))
            return 0
        except Exception as e:
            print(f"{eng} failed: {e}", file=sys.stderr)
    print("no transcription engine worked; run setup.py for install hints", file=sys.stderr)
    return 2

if __name__ == "__main__":
    sys.exit(main())
