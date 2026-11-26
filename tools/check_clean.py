#!/usr/bin/env python3
"""Guard: refuse to commit ROMs, binaries or other games' assets.

Checks the files staged in git (or the paths given):
  * ROM, save, image, audio and object file types, and anything under build/
  * binary content in general
  * long runs of hex bytes, which is what dumped data from another game looks like
The one exception is our own game's release build, gbc/release/skydeck.gbc,
accepted only when its cartridge header names Skydeck Slide.

Exit status 1 if anything is found. Run before every commit:
  python3 -I tools/check_clean.py
"""
import os
import re
import subprocess
import sys

BAD_EXT = {".nes", ".unf", ".fds", ".gb", ".gbc", ".sfc", ".smc", ".bin", ".chr", ".sav",
           ".nst", ".ppm", ".idx", ".ram", ".png", ".bmp", ".wav", ".avi", ".o", ".dbg"}
BAD_DIRS = ("build/", "rom/", "gbc/build/")
RELEASE_ROM = "gbc/release/skydeck.gbc"
RELEASE_TITLE = b"SKYDECKSLIDE"
HEX_RUN = re.compile(r"(?:\$?[0-9A-Fa-f]{2}[ ,]+){24,}")


def staged():
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
                         capture_output=True, text=True, check=True).stdout
    return [p for p in out.split("\n") if p]


def main():
    paths = sys.argv[1:] or staged()
    problems = []
    for p in paths:
        if not os.path.isfile(p):
            continue
        ext = os.path.splitext(p)[1].lower()
        if p == RELEASE_ROM:
            head = open(p, "rb").read(0x150)
            if head[0x134:0x134 + len(RELEASE_TITLE)] != RELEASE_TITLE:
                problems.append(f"{p}: release ROM header is not Skydeck Slide")
            continue
        if ext in BAD_EXT or p.startswith(BAD_DIRS):
            problems.append(f"{p}: file type/location not allowed")
            continue
        data = open(p, "rb").read()
        if b"\0" in data:
            problems.append(f"{p}: binary file")
            continue
        m = HEX_RUN.search(data.decode("utf-8", "replace"))
        if m:
            problems.append(f"{p}: long run of hex bytes near: {m.group(0)[:40]}...")
    if problems:
        print("check FAILED:")
        for x in problems:
            print("  " + x)
        sys.exit(1)
    print(f"check passed ({len(paths)} files)")


if __name__ == "__main__":
    main()
