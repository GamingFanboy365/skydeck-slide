# Skydeck Slide — project rules

This repository holds Skydeck Slide, an original Game Boy Color game. It is a
clean-room project: everything in it is our own work.

## Never commit other people's content

- No ROM images of any other game (`*.nes`, `*.gb`, `*.gbc`, ...), and nothing
  taken from them: code, disassembly, graphics, palettes, music, sound or text.
- No screenshots, recordings or dumps of other games.
- Other games may be looked at privately for general technique only (how a
  palette ramp or a dither pattern is used). Their files stay outside the
  repository, and nothing is copied from them.
- All art, characters, music, sound, text and code in Skydeck Slide are
  original. Graphics are drawn in code (`gbc/tools/art.py`), music is written
  as note text (`gbc/tools/music.py`).

Before every commit, run `python3 -I tools/check_clean.py`. It refuses ROMs,
binaries, images, audio and anything under `build/`.

The one ROM the repository may contain is our own release build, at exactly
`gbc/release/skydeck.gbc` (`make release` in `gbc/`). `.gitignore` and
`check_clean.py` allow that single path, and only when the cartridge header
title is SKYDECKSLIDE.

## Layout

- `gbc/src/` — the game in SM83 assembly (RGBDS).
- `gbc/tools/` — asset generator, artwork, music, and the PyBoy test harness.
- `gbc/release/` — the committed release ROM.
- `gbc/build/` — generated output (git-ignored).
- `tools/check_clean.py` — the pre-commit guard.
