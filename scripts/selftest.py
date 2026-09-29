"""Sanity check the analyzer on a synthetic kick track with known beat times and a known drop."""
import wave

import numpy as np

from analyze_track import SR, analyze

bpm, start, drop_bar = 121.0, 0.437, 17
period = 60 / bpm
dur = start + period * 4 * 32 + 1
y = np.zeros(int(dur * SR), dtype=np.float32)
t = np.arange(int(0.25 * SR)) / SR
kick = (np.sin(2 * np.pi * (55 + 90 * np.exp(-t * 30)) * t) * np.exp(-t * 12)).astype(np.float32)
hat = (np.random.default_rng(0).standard_normal(int(0.03 * SR)) * np.exp(-np.arange(int(0.03 * SR)) / 200)).astype(np.float32)
for k in range(32 * 4):
    b = start + k * period
    i = int(round(b * SR))
    loud = 1.0 if k >= (drop_bar - 1) * 4 or k < 8 * 4 else 0.25  # quiet break before the drop
    y[i: i + len(kick)] += kick[: len(y) - i] * loud * (1.3 if k % 4 == 0 else 1.0)
    j = int(round((b + period / 2) * SR))
    y[j: j + len(hat)] += hat[: len(y) - j] * 0.2
drop_true = start + (drop_bar - 1) * 4 * period

with wave.open("selftest.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(y / np.abs(y).max(), -1, 1) * 32000).astype(np.int16).tobytes())

r = analyze("selftest.wav")
print(f"true BPM {bpm}, got {r['bpm']}")
print(f"true first beat {start:.4f}s, got {r['first_beat_s']:.4f}s (err {1000 * (r['first_beat_s'] - start):+.1f} ms)")
print(f"true drop {drop_true:.4f}s, got {r['drop_transient_s']:.4f}s (err {1000 * (r['drop_transient_s'] - drop_true):+.1f} ms)")
