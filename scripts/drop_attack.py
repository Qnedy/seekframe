"""Pin a drop to the millisecond: strongest full-band level jump within +-0.35 s of the detected drop.
Usage: python drop_attack.py track.mp3 approx_drop_s"""
import sys

import numpy as np

from analyze_track import SR, load

y = load(sys.argv[1])
t0 = float(sys.argv[2])
w = int(0.005 * SR)
a = int((t0 - 0.35) * SR)
env = np.array([np.abs(y[i:i + w]).max() for i in range(a, a + int(0.7 * SR), w)])
before = np.array([env[max(0, k - 20):k].mean() if k else env[0] for k in range(len(env))])
after = np.array([env[k:k + 20].mean() for k in range(len(env))])
k = int(np.argmax(after - before))
# refine to 1 ms: first sample above half the post-jump level
seg = np.abs(y[a + k * w - w: a + k * w + 2 * w])
lvl = after[k]
j = int(np.argmax(seg > 0.5 * lvl))
t = (a + k * w - w + j) / SR
print(f"drop attack {t:.3f}s  (level {20*np.log10(max(before[k],1e-9)):.1f} -> {20*np.log10(lvl):.1f} dBFS)")
