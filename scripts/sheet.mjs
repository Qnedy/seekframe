// Tile PNGs into a labelled contact sheet: node sheet.mjs out/sheet.png cols w file1 file2 ...
import { execFileSync } from 'node:child_process';
import { existsSync, readdirSync } from 'node:fs';
import { join, basename } from 'node:path';

const [out, cols, w, ...files] = process.argv.slice(2);
const root = join(process.env.LOCALAPPDATA ?? '', 'Microsoft', 'WinGet', 'Packages');
let ff = 'ffmpeg';
for (const pkg of readdirSync(root).filter(d => d.startsWith('Gyan.FFmpeg')))
  for (const b of readdirSync(join(root, pkg))) if (existsSync(join(root, pkg, b, 'bin', 'ffmpeg.exe'))) ff = join(root, pkg, b, 'bin', 'ffmpeg.exe');
const W = +w, H = Math.round(W * 9 / 16), C = +cols;
const args = ['-y', '-loglevel', 'error'];
files.forEach(f => args.push('-i', f));
let fc = files.map((f, i) => `[${i}]scale=${W}:${H},drawtext=fontfile='C\\:/Windows/Fonts/arial.ttf':text='${basename(f, '.png').replace(/[:,]/g, ' ')}':x=6:y=6:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.7[v${i}]`).join(';');
const layout = files.map((_, i) => `${(i % C) * W}_${Math.floor(i / C) * H}`).join('|');
fc += ';' + files.map((_, i) => `[v${i}]`).join('') + `xstack=inputs=${files.length}:layout=${layout}:fill=gray`;
if (files.length === 1) fc = `[0]scale=${W}:${H}[o]`;
args.push('-filter_complex', fc, '-frames:v', '1', out);
execFileSync(ff, args);
