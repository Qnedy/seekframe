"""Scan every frame of a video for single-frame pops and list the hardest jumps.

Usage: python scan_pops.py video.mp4
A pop = frame n differs from both neighbours while the neighbours agree. The whole-frame result must be "none".
"Local flashes" are noisy during fast motion over repetitive detail (text, card strips): they are frames to LOOK at
(tile them into a sheet), not confirmed bugs.
"""
import subprocess
import sys

import numpy as np

from analyze_track import find_ffmpeg

W, H = 480, 270
raw = subprocess.run([find_ffmpeg(), "-v", "error", "-i", sys.argv[1], "-vf", f"scale={W}:{H}", "-f", "rawvideo",
                      "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
F = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(np.float32)
n = len(F)


def d(a, b):
    return float(np.abs(F[a] - F[b]).mean())


step = np.array([d(i, i + 1) for i in range(n - 1)])
pops = [(i, round(step[i - 1], 2), round(step[i], 2)) for i in range(1, n - 1)
        if min(step[i - 1], step[i]) > 1.5 and d(i - 1, i + 1) < 0.5 * min(step[i - 1], step[i])]
local = []
for i in range(1, n - 1):
    x = np.abs(F[i] - F[i - 1]).max(axis=2)
    y = np.abs(F[i] - F[i + 1]).max(axis=2)
    z = np.abs(F[i - 1] - F[i + 1]).max(axis=2)
    c = int(((x > 60) & (y > 60) & (z < 20)).sum())
    if c > 40:
        local.append((i, c))
print(f"{n} frames scanned")
print("single-frame pops (whole frame):", pops if pops else "none")
print("local flashes to eyeball (frame, px):", local[:60] if local else "none")
print("largest frame-to-frame changes:")
for i in sorted(np.argsort(step)[::-1][:10]):
    print(f"  {i}->{i + 1}  t={i / 60:.3f}s  diff {step[i]:.2f}")
