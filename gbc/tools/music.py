#!/usr/bin/env python3
"""Skydeck Slide music: original songs written as note text, compiled for the driver.

Notation: space-separated events NOTE:STEPS. NOTE is like C5, F#4, Bb3 or r for
a rest; drums use K (kick), S (snare), H (hi-hat). A step is a 16th note; bars
are 16 steps and each bar is checked. Songs are tables of bars per channel:
  ch1 = pulse harmony, ch2 = pulse lead, ch3 = wave bass, ch4 = noise drums.

Output (RGBDS include): a note frequency table and, per song, a header
(tempo in frames per step, ch1/ch2 duty and envelope, ch3 volume) followed by
pointers to four event lists of (note, steps) pairs. Note byte 0 = rest,
$FF = loop to the start, $FE = stop.
"""
import os

NOTE_BASE = 36            # MIDI number of C2 = table entry 0
SEMI = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
DRUMS = {"K": 1, "S": 2, "H": 3}


def midi(name):
    n = SEMI[name[0]]
    i = 1
    if name[i] in "#b":
        n += 1 if name[i] == "#" else -1
        i += 1
    return 12 * (int(name[i:]) + 1) + n


def chord_arp(root, kind, octave):
    """8th-note arpeggio for one bar: root, 3rd, 5th, octave and back."""
    r = midi(f"{root}{octave}")
    third = 3 if kind == "m" else 4
    tones = [r, r + third, r + 7, r + 12, r + 7, r + third, r, r + third]
    return [(t, 2) for t in tones]


def parse(text, drums=False):
    ev = []
    for tok in text.split():
        name, _, steps = tok.partition(":")
        steps = int(steps)
        if name == "r":
            ev.append((0, steps))
        elif drums:
            ev.append((("drum", DRUMS[name]), steps))
        else:
            ev.append((midi(name), steps))
    return ev


def bars(*texts, drums=False):
    out = []
    for i, t in enumerate(texts):
        ev = parse(t, drums)
        total = sum(s for _, s in ev)
        if total != 16:
            raise SystemExit(f"bar {i + 1} has {total} steps: {t}")
        out += ev
    return out


def bass_bar(root, octave=2, style="walk"):
    r = midi(f"{root}{octave}")
    if style == "walk":        # root, root, fifth, octave, fifth
        return [(r, 4), (r, 2), (r + 7, 2), (r + 12, 4), (r + 7, 4)]
    return [(r, 2), (r + 12, 2)] * 4    # driving octaves


def stab_bar(t1, t2):
    a, b = midi(t1), midi(t2)
    return [(0, 2), (a, 2), (0, 2), (b, 2)] * 2


# ---------------------------------------------------------------------------
# Title: "Rooftop Nocturne" -- A minor, mellow, Am F C G
# ---------------------------------------------------------------------------
TITLE_PROG = [("A", "m"), ("F", ""), ("C", ""), ("G", "")] * 2
TITLE = {
    "tempo": 8, "duty1": 0x40, "env1": 0x52, "duty2": 0x80, "env2": 0x84, "vol3": 0x40,
    "loop": True,
    "ch2": bars(
        "E5:4 D5:2 C5:2 A4:6 r:2",
        "C5:4 A4:2 C5:2 F5:6 r:2",
        "E5:4 G5:2 E5:2 D5:4 C5:4",
        "D5:6 B4:2 G4:6 r:2",
        "A4:2 C5:2 E5:2 A5:6 G5:2 E5:2",
        "F5:4 E5:2 C5:2 A4:8",
        "G4:2 C5:2 E5:2 G5:4 E5:2 D5:4",
        "D5:4 E5:2 D5:2 B4:8"),
    "ch1": sum((chord_arp(r, k, 3 if r in "AGF" else 4) for r, k in TITLE_PROG), []),
    "ch3": sum((bass_bar(r, 2) for r, _ in TITLE_PROG), []),
    "ch4": bars(*["K:4 H:4 S:4 H:2 H:2"] * 7, "K:4 H:4 S:4 S:2 S:2", drums=True),
}

# ---------------------------------------------------------------------------
# Match: "Skydeck Rush" -- E minor, driving, A section Em C G D, B section
# ---------------------------------------------------------------------------
MATCH_A = ["E", "C", "G", "D"] * 2
MATCH_B = ["A", "C", "D", "E", "A", "C", "D", "D"]
STABS = {"E": ("G4", "B4"), "C": ("E4", "G4"), "G": ("B4", "D5"), "D": ("F#4", "A4"),
         "A": ("C5", "E5")}
BASS_OCT = {"E": 2, "C": 3, "G": 2, "D": 3, "A": 2}
MATCH = {
    "tempo": 6, "duty1": 0x00, "env1": 0x71, "duty2": 0x80, "env2": 0xA3, "vol3": 0x20,
    "loop": True,
    "ch2": bars(
        "B4:2 E5:2 G5:2 B5:4 A5:2 G5:2 F#5:2",
        "E5:4 G5:2 E5:2 C5:6 r:2",
        "D5:2 G5:2 B5:2 D6:4 B5:2 A5:2 G5:2",
        "F#5:6 E5:2 D5:4 A4:4",
        "E5:2 E5:2 G5:2 E5:2 B5:4 A5:4",
        "G5:2 E5:2 C5:2 E5:2 G5:4 C6:4",
        "B5:2 A5:2 G5:2 D5:2 G5:4 B5:4",
        "A5:4 F#5:4 D5:4 F#5:2 A5:2",
        "A5:4 G5:2 E5:2 C5:4 E5:4",
        "G5:4 E5:2 G5:2 C6:8",
        "A5:2 F#5:2 D5:2 F#5:2 A5:4 D6:4",
        "B5:6 G5:2 E5:8",
        "C6:2 B5:2 A5:2 E5:2 A5:4 C6:4",
        "B5:2 A5:2 G5:2 E5:2 G5:4 E5:4",
        "F#5:4 A5:4 D6:4 C6:2 A5:2",
        "F#5:8 r:4 D5:2 F#5:2"),
    "ch1": sum((stab_bar(*STABS[r]) for r in MATCH_A + MATCH_B), []),
    "ch3": sum((bass_bar(r, BASS_OCT[r], "drive") for r in MATCH_A + MATCH_B), []),
    "ch4": bars(*["K:2 H:2 S:2 H:2 K:2 K:2 S:2 H:2"] * 7,
                "K:2 H:2 S:2 H:2 K:2 S:2 S:2 S:2",
                *["K:2 H:2 S:2 H:2 K:2 K:2 S:2 H:2"] * 7,
                "K:2 S:2 S:2 S:2 K:2 S:2 S:2 S:2", drums=True),
}

# ---------------------------------------------------------------------------
# Jingles (play once)
# ---------------------------------------------------------------------------
WIN = {
    "tempo": 6, "duty1": 0x80, "env1": 0x83, "duty2": 0x80, "env2": 0xC5, "vol3": 0x20,
    "loop": False,
    "ch2": parse("C5:2 E5:2 G5:2 C6:4 r:2 G5:2 C6:16"),
    "ch1": parse("G4:2 C5:2 E5:2 G5:4 r:2 E5:2 E5:16"),
    "ch3": parse("C3:6 G3:4 r:2 G2:2 C3:16"),
    "ch4": parse("K:2 H:2 H:2 S:4 r:2 S:2 K:16", drums=True),
}
LOSE = {
    "tempo": 8, "duty1": 0x40, "env1": 0x63, "duty2": 0x80, "env2": 0xA4, "vol3": 0x40,
    "loop": False,
    "ch2": parse("E5:4 D5:4 C5:4 B4:4 A4:16"),
    "ch1": parse("C5:4 B4:4 A4:4 G#4:4 E4:16"),
    "ch3": parse("A2:8 E2:8 A2:16"),
    "ch4": parse("K:4 r:4 K:4 r:4 S:16", drums=True),
}

SONGS = [("SongTitle", TITLE), ("SongMatch", MATCH), ("SongWin", WIN), ("SongLose", LOSE)]


def encode(events, channel, loop):
    out = bytearray()
    for note, steps in events:
        while steps > 0:
            n = min(steps, 255)
            if note == 0:
                out += bytes((0, n))
            elif isinstance(note, tuple):
                out += bytes((note[1], n))
            else:
                # the wave channel sounds an octave below the pulse channels
                idx = note - NOTE_BASE + (12 if channel == 3 else 0)
                if not 0 <= idx < 72:
                    raise SystemExit(f"note {note} out of range on channel {channel}")
                out += bytes((idx + 1, n))
            steps -= n
    out.append(0xFF if loop else 0xFE)
    return bytes(out)


def generate():
    lines = ["; generated by gbc/tools/music.py -- original music for Skydeck Slide"]
    lines.append("MusicNoteTable::")
    for i in range(72):
        f = 440 * 2 ** ((i + NOTE_BASE - 69) / 12)
        x = max(0, min(2047, round(2048 - 131072 / f)))
        lines.append(f"    dw ${x:04X}")
    for name, song in SONGS:
        if song["loop"]:
            lengths = {ch: sum(s for _, s in song[ch]) for ch in ("ch1", "ch2", "ch3", "ch4")}
            if len(set(lengths.values())) != 1:
                raise SystemExit(f"{name}: channel lengths differ {lengths}")
        lines.append(f"{name}::")
        lines.append(f"    db {song['tempo']}, ${song['duty1']:02X}, ${song['env1']:02X}, "
                     f"${song['duty2']:02X}, ${song['env2']:02X}, ${song['vol3']:02X}")
        lines.append(f"    dw {name}_1, {name}_2, {name}_3, {name}_4")
        for ch in (1, 2, 3, 4):
            data = encode(song[f"ch{ch}"], ch, song["loop"])
            lines.append(f"{name}_{ch}:")
            for i in range(0, len(data), 16):
                lines.append("    db " + ",".join(f"${b:02X}" for b in data[i:i + 16]))
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "build", "assets", "music.inc"))
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        f.write(generate())
    print(f"wrote {a.out}")
