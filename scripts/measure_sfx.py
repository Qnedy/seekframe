"""Measure where each sound effect starts, peaks and ends (numpy only).

Usage: python measure_sfx.py sfx_dir [--json out.json]
  onset       first sample above -30 dB relative to the file's peak
  peak_sample time of the absolute sample peak (and its level in dBFS)
  peak_env    time of the loudest 10 ms RMS window (the perceived "hit"; use this to sync)
  end         last sample above -40 dB relative to peak
  hits        for multi-hit sounds (typing), every 10 ms-RMS local max above -12 dB rel. peak
"""
import json
import os
import sys

import numpy as np

from analyze_track import find_ffmpeg

import subprocess

SR = 48000


def load(path):
    raw = subprocess.run([find_ffmpeg(), "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2)


def db(x):
    return 20 * np.log10(max(float(x), 1e-12))


def measure(path):
    x = load(path)
    a = np.abs(x).max(axis=1)
    peak = a.max()
    pk = int(np.argmax(a))
    above30 = np.nonzero(a > peak * 10 ** (-30 / 20))[0]
    above40 = np.nonzero(a > peak * 10 ** (-40 / 20))[0]
    w = int(0.010 * SR)
    rms = np.sqrt(np.convolve((x ** 2).mean(axis=1), np.ones(w) / w, mode="same"))
    pe = int(np.argmax(rms))
    # hits: local maxima of the RMS envelope at least 60 ms apart, above -12 dB of the loudest
    hop = int(0.005 * SR)
    r = rms[::hop]
    thr = r.max() * 10 ** (-12 / 20)
    gap = int(0.06 * SR / hop)
    hits = []
    for i in range(1, len(r) - 1):
        if r[i] >= thr and r[i] == r[max(0, i - gap): i + gap + 1].max():
            hits.append(round(i * hop / SR, 3))
    return {
        "file": os.path.basename(path),
        "duration_s": round(len(a) / SR, 3),
        "onset_s": round(above30[0] / SR, 4),
        "peak_sample_s": round(pk / SR, 4),
        "peak_dbfs": round(db(peak), 1),
        "peak_env_s": round(pe / SR, 4),
        "end_s": round(above40[-1] / SR, 3),
        "hits_s": hits,
    }


if __name__ == "__main__":
    d = sys.argv[1]
    res = [measure(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith((".wav", ".mp3"))]
    for m in res:
        extra = f"  hits: {len(m['hits_s'])}" if len(m["hits_s"]) > 2 else ""
        print(f"{m['file']:<26} len {m['duration_s']:>5.2f}s  onset {m['onset_s']:.3f}  "
              f"peak(sample) {m['peak_sample_s']:.3f} @ {m['peak_dbfs']:+.1f} dBFS  "
              f"peak(10ms RMS) {m['peak_env_s']:.3f}  end {m['end_s']:.2f}{extra}")
    if "--json" in sys.argv:
        json.dump(res, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
