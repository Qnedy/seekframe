"""Build a film soundtrack from a cue sheet (numpy only).

Usage: python mix.py cues.json out/mix_raw.wav

cues.json:
{
  "dur": 36.0,
  "music": {"file": "assets/song.mp3", "start": 8.029, "level_db": -19, "ref": [9, 12], "fade_out": 0.35},
  "sfx_dir": "sfx",
  "peaks": "sfx/peaks.json",
  "cues": [
    {"sfx": "click", "t": 3.75, "db": -20},
    {"sfx": "whoosh", "t": 10.3, "db": -17, "kind": "env"},
    {"sfx": "pop", "t": [8.0, 8.23, 8.46], "db": -22}
  ]
}
- "music.start": where film t=0 sits in the song (drop_in_song - drop_in_film).
- "music.ref": [from, to] film seconds whose RMS is set to level_db (pick a post-drop window).
- "peaks": written by measure_sfx.py. Transient cues put their sample peak on t;
  "kind": "env" cues (swooshes, swells, sparkles) put their loudest 10 ms on t.
- "db": level of each cue's loudest 10 ms. Loudness normalisation happens afterwards (loudnorm.py).
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np

from analyze_track import find_ffmpeg

SR = 48000
FF = find_ffmpeg()


def load(path, start=None, dur=None):
    cmd = [FF, "-v", "error"] + (["-ss", f"{start:.4f}"] if start is not None else []) + ["-i", path]
    cmd += (["-t", f"{dur:.4f}"] if dur else []) + ["-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()


def rms_peak(x, win=0.010):
    w = int(win * SR)
    return float(np.sqrt(np.convolve((x ** 2).mean(axis=1), np.ones(w) / w, mode="same")).max())


cfg = json.load(open(sys.argv[1], encoding="utf-8"))
out_path = sys.argv[2]
dur = cfg["dur"]
buf = np.zeros((int((dur + 2) * SR), 2), np.float32)

mus = cfg.get("music")
if mus:
    m = load(mus["file"], mus["start"], dur + 0.5)
    a, b = mus.get("ref", [0, dur])
    ref = m[int(a * SR):int(b * SR)]
    m *= 10 ** (mus.get("level_db", -19) / 20) / max(np.sqrt((ref ** 2).mean()), 1e-9)
    env = np.ones(len(m), np.float32)
    env[:480] = np.linspace(0, 1, 480)
    e0, fo = int(dur * SR), int(mus.get("fade_out", 0.35) * SR)
    env[e0 - fo:e0] = np.linspace(1, 0, fo)
    env[e0:] = 0
    buf[:len(m)] += m * env[:, None]

peaks = {p["file"].rsplit(".", 1)[0]: p for p in json.load(open(cfg["peaks"]))}
cache, placed = {}, []
for c in cfg["cues"]:
    name, kind = c["sfx"], c.get("kind", "transient")
    p = peaks[name]
    x = cache.setdefault(name, load(os.path.join(cfg["sfx_dir"], p["file"])))
    pk = p["peak_sample_s" if kind == "transient" else "peak_env_s"]
    y = x * (10 ** (c["db"] / 20) / max(rms_peak(x), 1e-9))
    for t in (c["t"] if isinstance(c["t"], list) else [c["t"]]):
        s = int(round((t - pk) * SR))
        a, e = max(0, s), min(len(buf), s + len(y))
        if e > a:
            buf[a:e] += y[a - s:e - s]
        placed.append({"sfx": name, "t": t, "starts_at": round(s / SR, 4), "db": c["db"]})

out = buf[:int(dur * SR)]
pk = float(np.abs(out).max())
if pk > 0.98:
    out *= 0.98 / pk
os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
with wave.open(out_path, "wb") as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
json.dump(placed, open(os.path.splitext(out_path)[0] + "_placements.json", "w"), indent=1)
print(f"{len(placed)} cues placed, peak {20 * np.log10(max(pk, 1e-9)):.1f} dBFS -> {out_path}")
