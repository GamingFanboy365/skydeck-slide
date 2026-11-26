# Skydeck Slide

**Skydeck Slide** is an original first-person puck-sliding game for the Game Boy Color. You face seven rivals, each on a stage of their own, in matches to seven points. Every picture, character, tune and line of code in it was made for this project.

The ready-to-play ROM is [`gbc/release/skydeck.gbc`](gbc/release/skydeck.gbc). It runs in any Game Boy Color emulator (SameBoy, mGBA, BGB) and on real hardware through a flash cartridge.

## How it began, and what it became

This project started as a request to port *Push the Ball*, a puck game from a VT03 plug-and-play console, to the Game Boy Color. A direct port would have meant carrying another game's art and characters to a new system. So the work took a different route: study how that kind of game plays, then build a new one that stands on its own.

The study came first, done the bring-your-own-ROM way: tools that worked on a privately supplied copy and never put any of it in this repository. That produced an understanding of what makes the genre tick. The paddle builds up speed instead of snapping into place. Hitting while moving puts power and angle on a shot. The puck has a top speed and a little friction. And the opponent doesn't chase the puck: it works out where the puck will arrive and goes there. Once those ideas were clear, the study tools were retired. They are no longer part of this repository, which now holds only the new game.

Skydeck Slide began small: one rooftop table at night, three opponents and a handful of sound effects. Then it grew. The art moved to shading ramps and textured surfaces, and the opponents became larger, layered sprites with personality: spectacles, a beanie, a top hat, a space helmet. Original music arrived: a mellow title theme, a driving match theme and a darker track for one rival. The ladder stretched to seven rivals, each with a stage drawn for them, from a jungle treehouse to a moon base. Splash cards now introduce every match with the rival's opening line. A How to Play screen and a glossary round it out, with rival profiles in a trophy hall and puck terms chalked on a board.

The game that came out of it has more opponents, more places, more music and more ways in than the one that inspired it. It is also entirely its own.

## The rivals

| | Rival | Stage | Style |
|---|---|---|---|
| 1 | Tomo the tortoise | Jungle Canopy | Slow, forgiving, fond of naps |
| 2 | Pip the penguin | Snow Lodge | Fast feet, loose aim |
| 3 | Rusty the fox | City Rooftop | Wide angles and a smirk |
| 4 | Zuri the meerkat | Desert Canyon | Reads straight shots |
| 5 | Okta the octopus | Sunset Pier | Steps in to steal your shots |
| 6 | Blaze the dragon | Volcano Forge | Hard, fast returns |
| 7 | Nova the space cat | Moon Base | Already where the puck is going |

Each rival is quicker, more accurate and returns the puck harder than the last. From Okta on they also step forward to meet close shots. Beat all seven to become champion.

## Playing

The D-pad moves your paddle: up and down along the table, left and right across it. Holding a direction builds speed and letting go stops you. Push into the puck as you hit it to shoot harder, or slide sideways to angle it off the rails. The first to 7 points wins a match. Start pauses.

## Building

You need Python 3 and [RGBDS](https://rgbds.gbdev.io/) 0.9 or newer.

```bash
cd gbc
```

```bash
make release
```

That draws all the graphics, compiles the music, assembles the game into `gbc/build/skydeck.gbc` and copies it to `gbc/release/`. See [`gbc/README.md`](gbc/README.md) for how the game is put together and how to test it.

## In this repository

The game lives in `gbc/`: the assembly source in `gbc/src/`, and the tools that draw every graphic and compile every tune in `gbc/tools/`. `tools/check_clean.py` is a pre-commit guard that keeps ROMs of other games, binaries and anything taken from other games out of the repository. `CLAUDE.md` sets out the project's rules.
