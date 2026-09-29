// Render film.html with Playwright.
//   node render.mjs stills 1.2,5.8,8.9,12.1     -> out/still_<t>.png
//   node render.mjs frames 330-360              -> out/frames/<n>.png (single sample, no blur) for frame-by-frame review
//   node render.mjs full                        -> out/film_silent.mp4 (60 fps, 8 subframes per frame blended by tmix)
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const FPS = 60, SUB = 8, SHUTTER = 0.5; // shutter as a fraction of the frame interval
const [mode = 'stills', arg = ''] = process.argv.slice(2);
const FILM = process.env.FILM || 'film.html', OUT = process.env.OUT || 'out';
mkdirSync(`${OUT}/frames`, { recursive: true });

function findFfmpeg() {
  const root = join(process.env.LOCALAPPDATA ?? '', 'Microsoft', 'WinGet', 'Packages');
  for (const pkg of existsSync(root) ? readdirSync(root).filter(d => d.startsWith('Gyan.FFmpeg')) : [])
    for (const b of readdirSync(join(root, pkg))) {
      const exe = join(root, pkg, b, 'bin', 'ffmpeg.exe');
      if (existsSync(exe)) return exe;
    }
  return 'ffmpeg';
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', e => errors.push(String(e)));
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
await page.goto(pathToFileURL(resolve(FILM)).href);
await page.evaluate(() => window.ready);
const DUR = await page.evaluate(() => window.DUR);

async function shot(t, path, type = 'png') {
  await page.evaluate(tt => window.seek(tt), t);
  return page.screenshot({ path, type, ...(type === 'jpeg' ? { quality: 95 } : {}) });
}

if (mode === 'stills') {
  for (const s of arg.split(',')) await shot(parseFloat(s), `${OUT}/still_${s}.png`);
} else if (mode === 'frames') {
  const [a, b] = arg.split('-').map(Number);
  for (let f = a; f <= b; f++) await shot(f / FPS, `${OUT}/frames/${String(f).padStart(4, '0')}.png`);
} else if (mode === 'full') {
  // optional frame range "a-b" renders one segment (out/seg_<a>.mp4) so long renders can run in chunks
  const total = Math.round(DUR * FPS);
  const [fa, fb] = arg ? arg.split('-').map(Number) : [0, total - 1];
  const nFrames = fb + 1;
  const outFile = arg ? `${OUT}/seg_${String(fa).padStart(4, '0')}.mp4` : `${OUT}/film_silent.mp4`;
  const ff = spawn(findFfmpeg(), [
    '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS * SUB), '-c:v', 'png', '-i', '-',
    '-vf', `tmix=frames=${SUB},select='eq(mod(n\\,${SUB})\\,${SUB - 1})',setpts=N/${FPS}/TB`,
    '-r', String(FPS), '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', outFile,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let f = fa; f < nFrames; f++) {
    for (let k = 0; k < SUB; k++) {
      // samples spread across the open shutter, centred on the frame time
      const t = (f + ((k + 0.5) / SUB - 0.5) * SHUTTER) / FPS;
      const buf = await shot(Math.max(0, t), undefined);
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    if (f % 60 === 0) console.log(`frame ${f}/${nFrames}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  console.log('done', nFrames, 'frames');
}
if (errors.length) console.log('PAGE ERRORS:\n' + errors.join('\n'));
await browser.close();
