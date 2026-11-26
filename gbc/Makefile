# Skydeck Slide -- build with RGBDS (set RGBDS=/path/to/rgbds/ if not on PATH)
RGBDS ?=
ASM  := $(RGBDS)rgbasm
LINK := $(RGBDS)rgblink
FIX  := $(RGBDS)rgbfix
PY   ?= python3 -I

ROM := build/skydeck.gbc
SRC := src/main.asm src/game.asm
OBJ := $(SRC:src/%.asm=build/%.o)

all: $(ROM)

build/assets/assets.inc: tools/makeassets.py tools/art.py
	$(PY) tools/makeassets.py --out build/assets

build/%.o: src/%.asm src/hardware.inc build/assets/assets.inc
	@mkdir -p build
	$(ASM) -I src -I build/assets -o $@ $<

$(ROM): $(OBJ)
	$(LINK) -n build/skydeck.sym -m build/skydeck.map -o $@ $(OBJ)
	$(FIX) -C -v -p 0xFF -t "SKYDECKSLIDE" -l 0x33 -k "SS" $@

clean:
	rm -rf build

.PHONY: all clean
