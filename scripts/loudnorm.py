"""Gentle peak limiting, then two-pass LINEAR ffmpeg loudnorm.

Usage: python loudnorm.py in.wav out.wav [I=-14] [TP=-1] [LRA=20]
LRA is wide on purpose: a quiet intro before a drop raises the loudness range, and a narrow LRA makes
loudnorm fall back to dynamic mode (audible pumping). The printout must end in "(linear)".
"""
import json
import re
import subprocess
import sys

from analyze_track import find_ffmpeg

FF = find_ffmpeg()
src, dst = sys.argv[1], sys.argv[2]
I = sys.argv[3] if len(sys.argv) > 3 else "-14"
TP = sys.argv[4] if len(sys.argv) > 4 else "-1"
LRA = sys.argv[5] if len(sys.argv) > 5 else "20"
TARGET = f"I={I}:TP={TP}:LRA={LRA}"
lim = dst + ".lim.wav"
subprocess.run([FF, "-hide_banner", "-y", "-i", src, "-af", "alimiter=limit=0.4:attack=3:release=60:level=disabled",
                "-c:a", "pcm_f32le", lim], check=True, capture_output=True)
p1 = subprocess.run([FF, "-hide_banner", "-i", lim, "-af", f"loudnorm={TARGET}:print_format=json", "-f", "null", "-"],
                    capture_output=True, text=True).stderr
m = json.loads(re.findall(r"\{[^{}]*\}", p1)[-1])
af = (f"loudnorm={TARGET}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
      f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=json")
p2 = subprocess.run([FF, "-hide_banner", "-y", "-i", lim, "-af", af, "-ar", "48000", "-c:a", "pcm_s16le", dst],
                    capture_output=True, text=True).stderr
r = json.loads(re.findall(r"\{[^{}]*\}", p2)[-1])
print(f"in {m['input_i']} LUFS / {m['input_tp']} dBTP -> out {r['output_i']} LUFS / {r['output_tp']} dBTP ({r['normalization_type']})")
