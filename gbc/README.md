# Skydeck Slide (Game Boy Color)

An original first-person puck-sliding game for the Game Boy Color. The art, characters, music, sound, text and code are all new.

You play a puck match on a rooftop at night against a ladder of three opponents. Tomo the tortoise is slow and forgiving. Rusty the fox moves faster and returns harder. Okta the octopus is quickest of all and steps forward to meet close shots. The first to 7 points wins a match; beat all three to become champion.

A ready-built ROM is in `release/skydeck.gbc`; it runs in any Game Boy Color emulator (SameBoy, mGBA, BGB) or on hardware via a flash cart.

## Controls

The D-pad moves your paddle: up and down move it along the table, left and right across it. Holding a direction builds up speed, and letting go stops the paddle. Hitting the puck while moving forward hits it harder, and moving sideways as you hit angles the shot. Start pauses.

## Building

You need Python 3 and [RGBDS](https://rgbds.gbdev.io/) 0.9 or newer.

```bash
make
```

If RGBDS is not on your `PATH`, point the Makefile at it (note the trailing slash):

```bash
make RGBDS=/path/to/rgbds/
```

The ROM is written to `build/skydeck.gbc`. `tools/makeassets.py` runs first and generates every graphic: the scenes are drawn in code (`tools/art.py`) using the same perspective maths the game uses, with each palette a shading ramp of one material and textured surfaces throughout, the opponents are built from shapes in `tools/art.py` (outlined, lit from the top left), and the font is defined in `tools/makeassets.py`. PNG previews of the screens land in `build/assets/`.

## Music

All music is original. `tools/music.py` holds the songs as note text (one bar per string, checked to be 16 sixteenth-note steps) and compiles them for the driver in `src/music.asm`. The title plays "Rooftop Nocturne", a mellow A minor loop. Matches play "Skydeck Rush", a driving E minor tune with a second section. Short jingles mark a win or a loss. The driver uses the second pulse channel for the lead, the first for harmony (arpeggios or off-beat stabs), the wave channel for bass and the noise channel for drums. Sound effects borrow channels 1 and 4 for a few frames and the music picks up again on its next note. Pausing a match pauses the music where it is.

`make release` copies the built ROM to `release/skydeck.gbc`, the one ROM the repository is allowed to contain.

## Testing

`tools/play.py` runs the ROM headlessly in [PyBoy](https://github.com/Baekalfen/PyBoy) (`pip install pyboy`). It accepts a scripted input timeline, can hand control to a simple bot after that, prints scores and variables, takes screenshots, records the sound to a WAV file (`--wav`) and pokes memory to jump to later stages.

```bash
python3 tools/play.py build/skydeck.gbc --frames 20000 --input "150-152:start" --bot 2 --report 1000
```

## How it works

The world is a table 192 units deep and 96 wide; depth 0 is the opponent's end. Positions and velocities are 8.8 fixed point. A depth is turned into a screen row by a perspective table (`PerspY`), and an X position is scaled by a per-depth factor (`PerspScale`), so far objects sit near the horizon and close together. The same tables pick the sprite size for the puck and paddles.

Every time you hit the puck, the game saves the puck's state, runs the real puck physics forward silently until the puck reaches the opponent's line, notes where it got to and restores it. The opponent then slides toward that spot, with an aiming error and a speed set by its level. On each return the opponent adds a little speed and a wider random angle, growing through a rally, so long rallies end.

Source layout: `src/main.asm` holds boot, interrupts, video and text helpers, input, maths and sound effects. `src/game.asm` holds the game states, physics, the opponent and sprite drawing. `src/music.asm` is the music driver.
