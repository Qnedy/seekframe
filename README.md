# Seekframe

*Seek + frame: every frame of the film is drawn by `seek(t)`, a pure function of time, which is what makes real motion
blur and frame-by-frame review possible.*

A Claude Code skill that turns an agent into a small motion-design studio: it interviews you about your product,
co-writes the script with you, and renders a polished 2D product film as code, with real motion blur, a beat-synced
soundtrack and frame-by-frame quality control.

## Examples

Two films made with Seekframe for [Partidinha](https://partidinha.com), a WhatsApp bot + app that runs amateur
football games. On-screen text is in Brazilian Portuguese.

**Before / after** (19 s): the group-chat chaos on the music's build, then the bot takes over on the drop.

![Before / after](docs/example-before-after.gif)

<!-- drop the before/after mp4 here -->

**Full flow** (36 s): create the game, players join through the bot, a player who owes money is blocked until the
admin marks the payment, team draw, live match stats, and the day's ranking posted back in the group.

![Full flow](docs/example-full-flow.gif)

<!-- drop the full-flow mp4 here -->

## What it does

1. **Intake.** Asks for everything specific to your product: what it is and the real problem it solves,
   screenshots of the real app, brand (logo, colours, fonts), format (16:9, 9:16, 1:1, length, language), your script
   or none, your music or none, and an optional reference video to copy the style from.
2. **Reference breakdown.** If you send a video, it extracts frames, builds timestamped contact sheets, samples the
   colours and writes a beat-by-beat breakdown with what to reuse and what to leave out.
3. **Script first.** Writes (or adapts) the script scene by scene, with on-screen copy and timings, and iterates with
   you. Nothing is rendered until you approve it.
4. **Music.** Uses your track, or finds free tracks on Mixkit, measures BPM and the exact drop time with numpy,
   and puts the story's turn on the drop.
5. **Film as code.** One HTML page where every style is a pure function of time (`seek(t)`), in one continuous take:
   objects morph into each other instead of cutting or fading.
6. **Render.** Playwright captures 8 subframes per frame, and ffmpeg blends them into 60 fps motion blur.
7. **Sound.** One effect per on-screen event, placed so each effect's measured peak lands on its moment, then
   loudness-normalised to −14 LUFS.
8. **QA before you see it.** Test stills, frame-by-frame review of every fast moment, an automated scan for
   single-frame pops, a ghosting check and an audio sync check.

## Install

Copy this folder to `~/.claude/skills/seekframe/`. Then ask Claude Code for a product video, or invoke the skill by
name.

Requirements (the skill walks you through them): ffmpeg, Node with Playwright and Chromium, and Python 3 with numpy.

```
winget install --id Gyan.FFmpeg -e        # Windows; macOS: brew install ffmpeg
npm i -D playwright && npx playwright install chromium
python -m venv .venv && .venv/Scripts/python -m pip install numpy
```

## Contents

| Path | Purpose |
|---|---|
| `SKILL.md` | The workflow, motion rules, build rules, audio method, render and QA checklist |
| `templates/film.html` | Starter film page: camera, springs, mask-line text, end card |
| `scripts/render.mjs` | Stills, single frames, or motion-blurred segments (8 subframes, `tmix`) |
| `scripts/sheet.mjs` | Labelled contact sheets for review |
| `scripts/reference_sheets.py` | Reference-video frames, timestamped sheets, colour sampling |
| `scripts/analyze_track.py`, `drop_attack.py`, `selftest.py` | Tempo, beat grid and drop detection, with a self-test |
| `scripts/measure_sfx.py` | Onset, peak and end of each sound effect |
| `scripts/mix.py` | Soundtrack from a JSON cue sheet |
| `scripts/loudnorm.py` | Limiter plus two-pass linear loudnorm |
| `scripts/scan_pops.py` | Scans every frame for single-frame pops |
| `scripts/keystrokes.py` | Human typing rhythm, shared by the text reveal and the key-click sounds |

## Assets and licences

This repo ships code only. Music, sound effects and photos are fetched per project from their sources (Mixkit,
Pexels, or your own files) under those sources' licences. Don't commit them here: their licences allow use in a video,
not redistribution of the files.

Built with [Claude Code](https://claude.com/claude-code).

## License

MIT, see [LICENSE](LICENSE).
