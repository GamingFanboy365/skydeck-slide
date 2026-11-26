# Skydeck Slide -- build with RGBDS (set RGBDS=/path/to/rgbds/ if not on PATH)
RGBDS ?=
ASM  := $(RGBDS)rgbasm
LINK := $(RGBDS)rgblink
FIX  := $(RGBDS)rgbfix
PY   ?= python3 -I

ROM := build/skydeck.gbc
SRC := src/main.asm src/game.asm src/music.asm
OBJ := $(SRC:src/%.asm=build/%.o)

all: $(ROM)

build/assets/assets.inc: tools/makeassets.py tools/art.py
	$(PY) tools/makeassets.py --out build/assets

build/assets/music.inc: tools/music.py
	$(PY) tools/music.py --out build/assets/music.inc

build/%.o: src/%.asm src/hardware.inc build/assets/assets.inc build/assets/music.inc
	@mkdir -p build
	$(ASM) -I src -I build/assets -o $@ $<

$(ROM): $(OBJ)
	$(LINK) -n build/skydeck.sym -m build/skydeck.map -o $@ $(OBJ)
	$(FIX) -C -v -p 0xFF -t "SKYDECKSLIDE" -l 0x33 -k "SS" $@

# copy the ROM to release/ (the one ROM the repository may contain)
release: $(ROM)
	@mkdir -p release
	cp $(ROM) release/skydeck.gbc

clean:
	rm -rf build

.PHONY: all clean release
