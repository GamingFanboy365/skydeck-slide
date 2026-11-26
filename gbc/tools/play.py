#!/usr/bin/env python3
"""Headless test runs of Skydeck Slide with PyBoy (pip install pyboy).

  python3 gbc/tools/play.py build/skydeck.gbc --frames 600 \
      --input "60-62:start;200-260:up+left" --shots 100,300 --out build/shots/run

Input items are FRAMES:BUTTONS separated by ';' (FRAMES = N or A-B, buttons
joined with '+': a b start select up down left right). --sheet makes one
contact sheet of all shots. --ram prints game variables from the .sym file.
"""
import argparse
import os
import re


def parse_inputs(spec):
    held = {}
    for item in filter(None, (spec or "").split(";")):
        frames, _, btns = item.partition(":")
        a, _, b = frames.partition("-")
        for f in range(int(a), int(b or a) + 1):
            held.setdefault(f, set()).update(btns.split("+"))
    return held


def s8(v):
    return v - 256 if v >= 128 else v


def bot_buttons(pb, syms, skill, f):
    """Line up with the puck and push into it when it comes close."""
    m = pb.memory
    state = m[syms["wState"]]
    if state in (0, 4, 5):
        return {"start"} if f % 40 == 0 else set()
    if state != 2:
        return set()
    px, pz = s8(m[syms["wPuckX"] + 1]), m[syms["wPuckZ"] + 1]
    mx, mz = s8(m[syms["wPlayerX"] + 1]), m[syms["wPlayerZ"] + 1]
    vz = s8(m[syms["wPuckVZ"] + 1])
    want = set()
    slack = {1: 6, 2: 3, 3: 1}[skill]
    # a sloppy bot reacts late
    if skill == 1 and f % 3:
        return set()
    aim = px + (4 if f % 120 < 60 else -4)
    if aim > mx + slack:
        want.add("right")
    elif aim < mx - slack:
        want.add("left")
    live = m[syms["wPuckLive"]]
    if (vz >= 0 or not live) and pz > 120 and pz < mz:
        want.add("up")
    elif mz < 176:
        want.add("down")
    return want


def load_syms(path):
    syms = {}
    if os.path.exists(path):
        for line in open(path):
            m = re.match(r"([0-9a-f]+):([0-9a-f]+) (\S+)", line, re.I)
            if m:
                syms[m.group(3)] = int(m.group(2), 16)
    return syms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--frames", type=int, default=600)
    ap.add_argument("--input")
    ap.add_argument("--shots", default="")
    ap.add_argument("--out", default="build/shots/run")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--watch", default="", help="comma list of symbols to print at each shot")
    ap.add_argument("--bot", type=int, default=0, metavar="SKILL",
                    help="after the input script, a simple bot plays (1-3; higher = sharper)")
    ap.add_argument("--report", type=int, default=0, help="print scores every N frames")
    ap.add_argument("--poke", action="append", default=[],
                    help="FRAME:SYMBOL=VALUE, write a byte (for testing later stages)")
    args = ap.parse_args()

    from pyboy import PyBoy
    pb = PyBoy(args.rom, window="null", sound_emulated=False, cgb=True)
    held = parse_inputs(args.input)
    shots = {int(x) for x in args.shots.split(",") if x}
    syms = load_syms(os.path.splitext(args.rom)[0] + ".sym")
    watch = [w for w in args.watch.split(",") if w]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    pressed = set()
    images = []
    pokes = {}
    for p in args.poke:
        fr, _, rest = p.partition(":")
        name, _, val = rest.partition("=")
        pokes.setdefault(int(fr), []).append((name, int(val, 0)))
    for f in range(args.frames):
        for name, val in pokes.get(f, []):
            base, _, off = name.partition("+")
            pb.memory[syms[base] + int(off or 0)] = val
        want = held.get(f, set())
        if args.bot and not want and f > 200:
            want = bot_buttons(pb, syms, args.bot, f)
        for b in pressed - want:
            pb.button_release(b)
        for b in want - pressed:
            pb.button_press(b)
        pressed = set(want)
        pb.tick(1, f in shots)
        if args.report and f % args.report == 0:
            m = pb.memory
            print(f"f{f}: state={m[syms['wState']]} level={m[syms['wLevel']]} "
                  f"you={m[syms['wScoreP']]} opp={m[syms['wScoreO']]}")
        if f in shots:
            img = pb.screen.image.copy()
            img.save(f"{args.out}_f{f:05d}.png")
            images.append(img)
            if watch:
                vals = []
                for w in watch:
                    name, _, n = w.partition(":")
                    n = int(n or 1)
                    a = syms.get(name)
                    vals.append(f"{name}=" + ("?" if a is None else
                                " ".join(f"{pb.memory[a + i]:02X}" for i in range(n))))
                print(f"f{f}: " + "  ".join(vals))
    pb.stop(save=False)
    if args.sheet and images:
        from PIL import Image
        cols = min(6, len(images))
        rows = (len(images) + cols - 1) // cols
        w, h = images[0].size
        sheet = Image.new("RGB", (cols * w * 2, rows * h * 2))
        for i, im in enumerate(images):
            sheet.paste(im.convert("RGB").resize((w * 2, h * 2), Image.NEAREST),
                        ((i % cols) * w * 2, (i // cols) * h * 2))
        sheet.save(f"{args.out}_sheet.png")
        print(f"wrote {args.out}_sheet.png")


if __name__ == "__main__":
    main()
