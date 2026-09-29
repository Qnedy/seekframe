"""Break down a reference video: frames at N per second, timestamped contact sheets, and sampled colours.

Usage: python reference_sheets.py ref.mp4 out_dir [fps=2] [cols=4] [rows=3]
Writes out_dir/frames/f_###.png, out_dir/contact_##.png (each tile stamped with its time) and prints the video specs.
Then LOOK at every sheet and write the beat breakdown (see SKILL.md, "Reference video").
Sample colours afterwards with: python reference_sheets.py --color frame.png x y
"""
import os
import subprocess
import sys

from analyze_track import find_ffmpeg

FF = find_ffmpeg()
FP = FF.replace("ffmpeg.exe", "ffprobe.exe") if FF.endswith("ffmpeg.exe") else "ffprobe"

if sys.argv[1] == "--color":
    img, x, y = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    raw = subprocess.run([FF, "-v", "error", "-i", img, "-vf", f"crop=3:3:{x}:{y},scale=1:1,format=rgb24", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    print("#%02X%02X%02X" % (raw[0], raw[1], raw[2]))
    sys.exit()

src, out = sys.argv[1], sys.argv[2]
fps = sys.argv[3] if len(sys.argv) > 3 else "2"
cols = sys.argv[4] if len(sys.argv) > 4 else "4"
rows = sys.argv[5] if len(sys.argv) > 5 else "3"
os.makedirs(os.path.join(out, "frames"), exist_ok=True)
print(subprocess.run([FP, "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate", "-show_entries",
                      "format=duration", "-of", "compact", src], capture_output=True, text=True).stdout)
subprocess.run([FF, "-y", "-v", "error", "-i", src, "-vf", f"fps={fps}", os.path.join(out, "frames", "f_%03d.png")], check=True)
font = "C\\:/Windows/Fonts/arial.ttf" if os.name == "nt" else "/System/Library/Fonts/Helvetica.ttc"
vf = (f"fps={fps},scale=480:-1,drawtext=fontfile='{font}':text='%{{pts\\:hms}}':x=8:y=8:fontsize=22:fontcolor=white:"
      f"box=1:boxcolor=black@0.6:boxborderw=4,tile={cols}x{rows}:padding=6:margin=6:color=gray")
subprocess.run([FF, "-y", "-v", "error", "-i", src, "-vf", vf, os.path.join(out, "contact_%02d.png")], check=True)
print("frames:", len(os.listdir(os.path.join(out, "frames"))), "| sheets:", sorted(f for f in os.listdir(out) if f.startswith("contact_")))
