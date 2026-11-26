# Skydeck Slide: under the hood

This folder is the whole game: SM83 assembly for the Game Boy Color, plus the Python tools that draw its graphics and compile its music. Nothing here is taken from any other game.

## Building

You need Python 3 and RGBDS 0.9 or newer. If RGBDS is not on your `PATH`, point the Makefile at it (note the trailing slash).

```bash
make
```

```bash
make RGBDS=/path/to/rgbds/
```

`make` writes `build/skydeck.gbc`. `make release` also copies it to `release/skydeck.gbc`, the one ROM the repository is allowed to contain. The cartridge is MBC5 (128 KiB): code, sprites, tables and music sit in the fixed bank, and each stage, the title, the How to Play screen, the glossary backdrops, the glossary text and the opponents' sprites live in switchable banks that are mapped in while a screen loads.

## Graphics

`tools/makeassets.py` turns the artwork into Game Boy Color data. The artwork itself is code in `tools/art.py`: every scene is drawn procedurally, with the same perspective maths the game uses, so the table, rails and sprites line up. Each 4-colour palette is a shading ramp of one material (copper, bamboo, ice, sandstone, rope, obsidian, chrome, sky, wood and so on), and surfaces get texture from dithered gradients and stipple noise. For every 8x8 tile the generator picks the palette that reproduces it best and maps any stray colour to its nearest match. It then removes duplicate tiles, including mirrored ones, and writes the tiles, maps, attributes and palettes as RGBDS include files, along with PNG previews in `build/assets/`.

The far end of the table is drawn so that the backboard tiles cover exactly ten tiles of one row, and those tiles are flagged to appear in front of sprites. That is how each opponent stands behind the board with only the top of their body showing.

Opponents are 32x32 and use six colours. They are drawn with six colour slots, then split into two stacked sprite layers with a palette each, so a figure can have an outline, three shades of its main colour and two accents. Each opponent's 64 tiles and two palettes are loaded when their splash card appears.

## Music

All music is original, written as note text in `tools/music.py`, one bar per string, with each bar checked to be sixteen steps. The tracks are "Rooftop Nocturne" on the title, "Skydeck Rush" for most matches, "Deep Current" for the match against Okta, and short win and lose jingles. The driver in `src/music.asm` puts the lead on pulse channel 2, harmony on pulse channel 1, bass on the wave channel and drums on the noise channel. Sound effects borrow channels 1 and 4 for a few frames, and the music picks up again on its next note. Paddle hits are a quick pitch drop with a noise click (lower for the opponent). A goal for you plays a rising four-note cheer with a sparkle, a goal against you a sagging three-note groan with a thud; both are short note sequences (`SFX` in `tools/music.py`) played by a small sequencer in the driver. Every stage win, and the championship, ends with the same fanfare, "Victory Lap".

## How a match works

The world is a table 192 units deep and 96 wide; depth 0 is the opponent's end. Positions and velocities are 8.8 fixed point. A perspective table turns depth into a screen row, and a second one scales X by depth, so far objects sit near the horizon and close together. The same tables pick the sprite size for the puck and paddles.

Your paddle accelerates while a direction is held and stops when it is released. When you hit the puck, its depth speed is reflected and your paddle's own velocity is added on both axes, so moving into a shot adds power and moving sideways adds angle. The puck has a speed cap, a minimum speed and gentle friction, and it bounces off the rails.

Every time you hit the puck, the game saves the puck's state and runs the real puck physics forward, silently, until the puck reaches the opponent's line. It notes where the puck got to and puts it back. The opponent then slides toward that spot with an aiming error. Seven per-level tables (`OppSpeed`, `OppErrShift`, `OppReturnMax`, `OppReturnBonus`, `OppAimShift`, `OppServeSpeed` in `src/game.asm`) set how fast each rival moves, how accurately they aim, how hard and wide they return and how fast they serve. From the fifth rival on, opponents also step forward to meet a close puck. Every return in a rally adds a little speed and angle, so long rallies end.

## Screens

The title has a menu: start a game, read How to Play (an illustrated table with arrows and a bank-shot path), or open the glossary. The glossary holds a profile for each rival in a Hall of Rivals, plus pages of puck terms on a chalkboard. Before each match a splash card shows the stage, the rival standing in it and the rival's opening line.

## Testing

`tools/play.py` runs the ROM headlessly in [PyBoy](https://github.com/Baekalfen/PyBoy) (`pip install pyboy`). It takes a scripted input timeline and can hand control to a simple bot that tracks the puck. It prints scores and variables, takes screenshots, records the sound to a WAV file, and can poke memory to jump to later stages.

```bash
python3 tools/play.py build/skydeck.gbc --frames 20000 --input "150-152:start" --bot 2 --report 1000
```

## Source layout

`src/main.asm` holds boot, interrupts, screen loading, text, input, maths and sound effects. `src/game.asm` holds the game states (title, How to Play, glossary, splash card, match), physics, the opponent and sprite drawing. `src/music.asm` is the music driver.
