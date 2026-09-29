"""Human keystroke schedule for typed text on fixed lines (quick runs in words, pauses at spaces/commas/line ends).
Writes typing.json (and typing.js: window.TYPING = ...) that BOTH the film (text reveal) and the mix (one key click
per character) read, so picture and sound share one rhythm.

Usage: python keystrokes.py T0 T1 "line one" "line two" ...
"""
import json
import random
import sys

T0, T1 = float(sys.argv[1]), float(sys.argv[2])
LINES = sys.argv[3:]
rng = random.Random(7)
gaps = []
for li, line in enumerate(LINES):
    for ci, ch in enumerate(line):
        if li == 0 and ci == 0:
            gaps.append(0.0)
            continue
        prev = line[ci - 1] if ci else "\n"
        g = 0.030 + rng.uniform(-0.010, 0.012)
        g += rng.uniform(0.020, 0.045) if prev == " " else 0
        g += 0.070 if prev == "," else 0
        g += 0.060 if prev == "\n" else 0
        g += 0.05 if rng.random() < 0.08 else 0
        gaps.append(g)
acc, times = 0.0, []
for g in gaps:
    acc += g
    times.append(acc)
scale = (T1 - T0) / times[-1]
keys, i = [], 0
for li, line in enumerate(LINES):
    for ci, ch in enumerate(line):
        keys.append({"t": round(T0 + times[i] * scale, 4), "line": li, "col": ci, "ch": ch})
        i += 1
data = {"lines": LINES, "keys": keys}
json.dump(data, open("typing.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
open("typing.js", "w", encoding="utf-8").write("window.TYPING = " + json.dumps(data, ensure_ascii=False) + ";")
print(len(keys), "keys", keys[0]["t"], "->", keys[-1]["t"])
