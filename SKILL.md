---
name: seekframe
description: Make polished 2D motion-design product films (launch videos, feature explainers, before/after stories, app walkthroughs) as code — an HTML page with seek(t) rendered by Playwright with real motion blur, a beat-synced soundtrack with SFX placed on measured peaks, and frame-level QA. Starts with an intake of the product's context (screens, brand, format, script or co-written script, own music or a measured free track, optional reference video to copy the style from). Use when the user asks for a product video, launch film, promo, app demo video, animated explainer, or wants to reuse this motion studio for another project or format.
---

# Seekframe: motion film studio

Films are code: one HTML page whose every style is a pure function of time, rendered frame by frame, scored to a
measured beat grid, then checked frame by frame before anyone sees it. This skill is product-agnostic; the brand,
story and assets come from the user each time.

Scripts live next to this file in `scripts/`; a starter page is `templates/film.html`. Copy both into the project
(e.g. `film/`), never edit them in place.

## 0. Studio setup (once per machine)
- ffmpeg: Windows `winget install --id Gyan.FFmpeg -e` (user scope, no admin; old shells won't see it on PATH —
  the scripts find it under %LOCALAPPDATA%\Microsoft\WinGet\Packages), macOS `brew install ffmpeg`.
- Playwright + Chromium in the project: `npm i -D playwright && npx playwright install chromium`.
  Note: `playwright install` deletes other projects' older browser builds; say so if it happens.
- numpy in a project venv: `python -m venv .venv && .venv/Scripts/python -m pip install numpy`.
- Ask before anything needing admin/sudo or system-wide changes beyond these.

## 1. Workflow (do not skip steps)
1. **Intake — ask first, build nothing yet.** When the skill starts, ask the user for everything that is specific to
   their product, in one message, in their language, grouped and easy to answer (they can reply in parts or skip
   items; say which default you'll use for each skipped item):
   - **Product**: name, website/URL, what it does in one sentence, who uses it, and the real problem it solves.
   - **Screens**: screenshots or recordings of the real app/site (the film shows real UI, rebuilt as 2D mocks), plus any
     photos for cards.
   - **Brand**: logo/brand mark file, colours, fonts (default: read them from the site's CSS), tone of voice.
   - **Format**: length, aspect (16:9 1920×1080 default; 9:16 1080×1920 reels; 1:1), fps (60 default), language of
     on-screen text, where it will be posted.
   - **Script**: *"Do you have a script, or should I write one and we refine it together?"* If they send one, adapt it
     to the beat map and flag anything that won't fit. If not, write a default (step 3) and iterate with them.
   - **Music**: *"Attach a track, or should I find one?"* If none: search free tracks on Mixkit (§4), measure 5–10
     candidates and offer the best 2–3 with BPM and drop time.
   - **Reference video (optional)**: *"Is there a video whose style you want to follow?"* If they send one, break it
     down first (see "Reference video" below) and use it as the style guide.
   Then research on your own before writing: read the site (copy, CSS colours/fonts), study every screenshot, learn the
   actual flow and vocabulary. A generic story that isn't the product is unusable, however polished.
2. **Reference video** (when provided): `python scripts/reference_sheets.py ref.mp4 ref_out 2` → frames at 2 fps +
   timestamped contact sheets; look at every sheet. Write a breakdown: beats (time range, what happens, camera move,
   how each scene turns into the next), colours (sample with `reference_sheets.py --color frame.png x y`), fonts, the
   engine of the video (e.g. "every beat is one user action → one system response"), and a short **steal / leave**
   list (what fits the user's style constraints, what conflicts). Share it with the user, then write the product's
   script with the same structure.
3. **Script first, in chat, for approval** — no render until the user approves. Keep it in the user's language, scene
   by scene with seconds, on-screen copy verbatim, and what transforms into what. Offer 2–3 measured music options.
   Strong default structure: *problem → drop/turn → product doing the work (real screens) → proof/result → end card*.
   Before/after on the music's build and drop works very well. Iterate: when they add a feature or change a scene,
   send back only the changed scenes plus the new total length. Long chat messages can fail to send — split them.
4. **Beat map**: pick the track, measure BPM + drop (§4), then key every scene boundary to beats; put the story's turn
   on the drop.
5. **Build** the page (§2, §3), render test stills, review, fix.
6. **Frame-by-frame review** of every fast moment, then the full render (§5), mix (§4), QA (§6).
7. **Deliver**: the mp4 + a 2×2 stills sheet, state specs (res, fps, duration, LUFS) and any deviation from the
   approved script. Keep replies short.

## 2. Look & motion rules
- **No edits, only transformations.** The film never cuts or dissolves; each scene is built from something already on
  screen. In our films a chat bubble opened up into the app, a tapped button turned into the bot's reply, a brand
  colour spread across the frame and later collapsed into a message, and headlines slid up from behind a clipping line.
- **Identical at the handoff**: when one layer replaces another, make them match exactly at that instant (position,
  size, corner radius, colour, text) and only then swap which one is drawn. If the incoming layer needs text, give it
  a copy of the text it is replacing.
- **Swap only when covered**: relayout or visibility changes happen only while something fully covers that region
  (a flood, a full-screen app page). Otherwise it is a visible pop.
- **Camera**: a single transform on the world layer, driven by keyframes `[t, zoom, cx, cy]` with eased segments and
  zoom blended in log space so pushes feel even. Give each scene a single, steady movement and keep its direction;
  a push immediately followed by a pull reads as a wobble. Lay typed text out on fixed lines so the camera never has to
  follow a cursor to a new line. At the tightest zoom of every segment, check that nothing important is cropped.
- **Springs** are closed-form step responses (template `spring()`), for pops and settles.
- **Colour takeovers**: a colour that spreads from one object must reach past every visible corner (`farthest()`
  helper) and needs roughly a third of a second with sine easing; shorter looks like a flicker. Collapse it into the
  next object with in-out easing.
- **Keep it moving**: nothing should sit still for more than about a second; a slow drift or a staggered reveal is
  enough.
- **2D only** unless asked: no 3D, particles, glows-for-decoration or template looks. Real screens/photos on cards.
- **Typography**: load every face with `document.fonts.load()` before the first frame. Spacing in px for scaled
  text (an `em` in a small parent is tiny). Tabular numerals on rolling counters.
- Text on screen in the user's language; product vocabulary copied from the real app/site.

## 3. Build rules (templates/film.html)
- `seek(t)` derives every style from `t` alone: no CSS transitions or animations, no timers, nothing remembered from
  the previous frame (one `measure()` pass after the fonts load is fine). Constants live at the top of the script, so
  they already exist when the renderer first calls `seek`.
- Give each layer its own stacking order (`z-index`), so overlays, cards, the phone and any colour takeover always
  stack the way the scene intends.
- Use `visibility` (the template's `show()`), not `display` — `display=''` falls back to a stylesheet `none`.
- Time-derived UI (counters, clocks, lists) comes from event tables, e.g. `COUNT = [[t, +1], ...]`.
- Typing: `scripts/keystrokes.py T0 T1 "line 1" "line 2"` writes one schedule shared by the text reveal and the key
  clicks.
- Put scripts in folders whose names don't shadow Python stdlib modules (a `typing.py` breaks numpy).

## 4. Music & SFX
- **User's own track**: measure it exactly like a found one. If it has no clear drop, put the story's turn on the
  strongest downbeat after a build; tell the user where it lands.
- **Find tracks** on Mixkit (free for commercial use): genre pages (`/free-stock-music/house/`, `/edm/`, `/dance/`,
  `/pop/`), full-length files at `https://assets.mixkit.co/music/<id>/<id>.mp3`. Mixkit lists no BPM: download several
  candidates and measure.
- **Measure**: `python scripts/analyze_track.py song.mp3 --json song.json` (tempo, beat grid, drop). Then pin the drop
  to the ms with `python scripts/drop_attack.py song.mp3 <approx_drop>`. Verify: house tracks with **off-beat bass**
  can lock the grid half a beat late — cross-check that the drop attack sits on the grid; if it's ~half a beat off,
  trust the attack. `scripts/selftest.py` checks the analyzer on a synthetic track.
- **Align**: `music.start = drop_in_song − drop_in_film` (drop lands on the story's turn).
- **SFX**: Mixkit `https://assets.mixkit.co/active_storage/sfx/<id>/<id>.wav` (fall back to `<id>-preview.mp3` on 403).
  One sound per on-screen event. Measure all: `python scripts/measure_sfx.py sfx_dir --json sfx_dir/peaks.json`.
- **Place & balance**: write `cues.json` (format in `scripts/mix.py`), `python scripts/mix.py cues.json out/mix_raw.wav`.
  Transients (pops, clicks, impacts, whistles) put their sample peak on the event; swells (swooshes, sparkles) their
  loudest 10 ms. Typical levels: music −19 dB RMS post-drop; impact −12; UI pops/clicks −19…−24; whooshes −17…−23;
  dense repeated pops (typing, message floods) −22…−31 with small random variation.
- **Loudness**: `python scripts/loudnorm.py out/mix_raw.wav out/mix.wav -14 -1 20` → must print `(linear)` and land
  within ±0.5 LU of −14. If it lands low, the true-peak ceiling is limiting the gain: lower the loudest cue (usually
  the impact) or the limiter's `limit` in loudnorm.py, and rerun.
- Verify sync in the final file: loudest ms within ±40 ms of a few key events.

## 5. Render
- `FILM=film.html OUT=out node scripts/render.mjs stills 1.2,5.8,...` → test stills; `frames a-b` → single-sample
  frames for frame-by-frame review; `full a-b` → one blurred segment `OUT/seg_<a>.mp4`.
- Motion blur: 8 subframes per frame over a 0.5-frame shutter, blended with ffmpeg `tmix` (built into render.mjs).
  With too few samples a fast object shows up as several separate copies instead of a smooth streak. If text still
  looks doubled at 8, **slow the move** (≥ ~1 s, sine easing)
  rather than adding samples.
- Long renders: ~180-frame segments, 2–3 running in parallel, each as its own foreground command (a single long
  background render has died silently before). Concat with `ffmpeg -f concat -c copy`, then mux the audio
  (`-c:v copy -c:a aac -b:a 256k -shortest`). Check the frame count equals `DUR × 60`.
- `node scripts/sheet.mjs out/sheet.png <cols> <width> a.png b.png ...` tiles labelled frames for review.

## 6. QA before showing anyone
1. Test stills across the whole timeline → contact sheet → fix layout, framing, clipped text, word spacing.
2. Single-sample frames around every fast moment (sends, drops, floods, morphs, page slides, grows) → sheets → look
   for pops, z-order errors, stray dots (e.g. zero-length round-cap dashes), wrong handoffs.
3. Full render → `python scripts/scan_pops.py final.mp4` → whole-frame pops must be `none`; tile the flagged local
   frames and look at them.
4. Tile the fastest blurred frames at 960 px and check for ghosting; slow those moves and re-render only the affected
   segments.
5. Audio: `(linear)` loudnorm, ≈ −14 LUFS, true peak ≤ −1 dBTP, spot-check sync.
6. Report what was checked and anything that changed vs the approved script.

## 7. Platform gotchas (Windows / PowerShell)
- Editing files with PowerShell string replace: `$`, backticks and `${...}` get eaten — prefer the Edit tool for JS.
- `.NET` file APIs resolve relative paths against the process cwd, not `cd` — use `$PWD\...`.
- Write UTF-8 without BOM for HTML/JS (`[Text.UTF8Encoding]::new($false)`).
