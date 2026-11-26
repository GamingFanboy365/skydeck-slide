#!/usr/bin/env python3
"""Generate all graphics for Skydeck Slide (original art, drawn in code).

The artwork lives in art.py (scenes and opponents) and the font is defined
below. This script turns it into Game Boy Color data: it picks the best
4-colour palette for every 8x8 tile (mapping stray colours to the nearest
palette colour), deduplicates tiles including flipped copies, and writes
RGBDS include files plus PNG previews to gbc/build/assets/.

  python3 -I gbc/tools/makeassets.py [--out gbc/build/assets]
"""
import argparse
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import art  # noqa: E402
from art import C, screen_y, xscale64  # noqa: E402

# ---------------------------------------------------------------------------
# font: our own 5x7 glyphs
# ---------------------------------------------------------------------------
FONT = {
    " ": "", "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110", "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11110 10001 10001 10001 10001 10001 11110", "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000", "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001", "I": "01110 00100 00100 00100 00100 00100 01110",
    "J": "00111 00010 00010 00010 00010 10010 01100", "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111", "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 11001 10101 10011 10001 10001 10001", "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000", "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001", "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100", "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100", "W": "10001 10001 10001 10101 10101 10101 01010",
    "X": "10001 10001 01010 00100 01010 10001 10001", "Y": "10001 10001 01010 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10011 10101 10101 10101 11001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00110 01000 10000 11111", "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    ".": "00000 00000 00000 00000 00000 01100 01100", "!": "00100 00100 00100 00100 00100 00000 00100",
    "-": "00000 00000 00000 11111 00000 00000 00000", ":": "00000 01100 01100 00000 01100 01100 00000",
    "?": "01110 10001 00001 00110 00100 00000 00100", "'": "00100 00100 01000 00000 00000 00000 00000",
    "/": "00001 00010 00010 00100 01000 01000 10000", ">": "01000 00100 00010 00001 00010 00100 01000",
}
FONT_ORDER = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.!-:?'/>"


def glyph_rows(ch):
    rows = FONT[ch].split()
    return [[int(c) for c in r] for r in rows] if rows else [[0] * 5 for _ in range(7)]


def text_font(cv, s, x, y, scale, colour, shadow=None, edge=None):
    """Big text on a canvas: shadow offset down-right, optional edge colour on the left/top."""
    def plot(dx, dy, c):
        for i, ch in enumerate(s):
            for ry, row in enumerate(glyph_rows(ch)):
                for rx, bit in enumerate(row):
                    if bit:
                        for sy in range(scale):
                            for sx in range(scale):
                                cv.set(x + i * 6 * scale + rx * scale + sx + dx,
                                       y + ry * scale + sy + dy, c)
    if shadow:
        plot(1, 1, shadow)
        plot(2, 2, shadow)
    plot(0, 0, colour)
    if edge:   # a lighter top edge on each stroke
        for i, ch in enumerate(s):
            for ry, row in enumerate(glyph_rows(ch)):
                for rx, bit in enumerate(row):
                    above = ry > 0 and glyph_rows(ch)[ry - 1][rx]
                    if bit and not above:
                        for sx in range(scale):
                            cv.set(x + i * 6 * scale + rx * scale + sx, y + ry * scale, edge)


# ---------------------------------------------------------------------------
# tiles, palettes, maps
# ---------------------------------------------------------------------------
def dist(a, b):
    ca, cb = C[a], C[b]
    return 3 * (ca[0] - cb[0]) ** 2 + 4 * (ca[1] - cb[1]) ** 2 + 2 * (ca[2] - cb[2]) ** 2


def fit_tile(pix, palettes):
    """Choose the palette that reproduces the tile best; map other colours to the nearest."""
    best = None
    for i, pal in enumerate(palettes):
        err = 0
        for row in pix:
            for c in row:
                if c not in pal:
                    err += min(dist(c, p) for p in pal)
        if best is None or err < best[0]:
            best = (err, i)
    err, i = best
    pal = palettes[i]
    idx = [[pal.index(c) if c in pal else min(range(4), key=lambda k: dist(c, pal[k]))
            for c in row] for row in pix]
    return i, idx, err


def encode_2bpp(idx):
    out = bytearray()
    for row in idx:
        lo = hi = 0
        for x, v in enumerate(row):
            lo |= (v & 1) << (7 - x)
            hi |= ((v >> 1) & 1) << (7 - x)
        out += bytes((lo, hi))
    return bytes(out)


class TileSet:
    """Deduplicating tile store, including flipped copies (CGB attributes)."""

    def __init__(self):
        self.tiles = []
        self.index = {}

    def add(self, idx):
        variants = (
            (tuple(map(tuple, idx)), 0),
            (tuple(tuple(r[::-1]) for r in idx), 0x20),
            (tuple(tuple(r) for r in idx[::-1]), 0x40),
            (tuple(tuple(r[::-1]) for r in idx[::-1]), 0x60),
        )
        for key, flip in variants:
            if key in self.index:
                return self.index[key], flip
        self.index[variants[0][0]] = len(self.tiles)
        self.tiles.append(variants[0][0])
        return len(self.tiles) - 1, 0


def build_screen(cv, palettes, first_slot):
    ts = TileSet()
    raw = []
    lossy = 0
    preview = [[None] * cv.w for _ in range(cv.h)]
    for ty in range(18):
        for tx in range(20):
            pix = [[cv.get(tx * 8 + x, ty * 8 + y) for x in range(8)] for y in range(8)]
            pal, idx, err = fit_tile(pix, palettes)
            lossy += err > 0
            for y in range(8):
                for x in range(8):
                    preview[ty * 8 + y][tx * 8 + x] = palettes[pal][idx[y][x]]
            t, flip = ts.add(idx)
            raw.append((t, flip, pal))
    tmap, amap = bytearray(), bytearray()
    for t, flip, pal in raw:
        slot = first_slot + t
        tmap.append(slot & 0xFF)
        amap.append(pal | flip | ((1 if slot >= 256 else 0) << 3))
    return ts.tiles, tmap, amap, preview, lossy


def bg_tile_address(slot):
    """LCDC.4 = 0: tile 0-127 at $9000, 128-255 at $8800; slots >= 256 are VRAM bank 1."""
    n = slot & 0xFF
    return 1 if slot >= 256 else 0, (0x9000 + n * 16) if n < 128 else (0x8800 + (n - 128) * 16)


def chunks_for(tiles, first_slot):
    out = []
    for i, t in enumerate(tiles):
        bank, addr = bg_tile_address(first_slot + i)
        data = encode_2bpp(t)
        if out and out[-1][0] == bank and out[-1][1] + len(out[-1][2]) == addr:
            out[-1][2].extend(data)
        else:
            out.append([bank, addr, bytearray(data)])
    return out


# ---------------------------------------------------------------------------
# sprites
# ---------------------------------------------------------------------------
def obj_tiles_8x16(img):
    """Cut an image (w multiple of 8, h multiple of 16) into 8x16 pieces, row by row."""
    out = []
    for oy in range(0, len(img), 16):
        for ox in range(0, len(img[0]), 8):
            top = [row[ox:ox + 8] for row in img[oy:oy + 8]]
            bot = [row[ox:ox + 8] for row in img[oy + 8:oy + 16]]
            out.append((top, bot))
    return out


PADDLE_WIDTHS = [8, 10, 12, 14, 16, 18, 21, 24]
PUCK_SIZES = [3, 4, 5, 6, 7, 8]


def paddle_image(w):
    """A bevelled bar: light top edge, body, dark underside and ends."""
    h = 3 if w < 14 else 4
    cols = (w + 7) // 8
    img = [[0] * (cols * 8) for _ in range(16)]
    x0 = (cols * 8 - w) // 2
    for y in range(h + 1):
        for x in range(w):
            if y == h:
                if 0 < x < w - 1:
                    img[y][x0 + x] = 1          # shadow under the paddle
                continue
            end = x in (0, w - 1)
            img[y][x0 + x] = 1 if end or y == h - 1 else (3 if y == 0 or x == 1 else 2)
    return img, cols


def puck_image(d):
    img = [[0] * 8 for _ in range(16)]
    r = d / 2
    o = (8 - d) // 2
    for y in range(d):
        for x in range(d):
            dx, dy = x + 0.5 - r, y + 0.5 - r
            if dx * dx + dy * dy <= r * r + 0.3:
                edge = dx * dx + dy * dy > (r - 1) ** 2
                hi = dx < 0 and dy < 0 and d >= 5 and not edge
                lower = dy > 0.5 and d >= 5
                img[y + o][x + o] = 3 if hi else (1 if edge or lower and not edge and dx > 0 else 2)
    return img


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------
def rgb15(c):
    r, g, b = c
    return r | g << 5 | b << 10


def db_lines(data, per=16):
    return ["    db " + ",".join(f"${b:02X}" for b in data[i:i + per]) for i in range(0, len(data), per)]


def write_png(path, rows, colour_of):
    h, w = len(rows), len(rows[0])
    raw = bytearray()
    for r in rows:
        raw.append(0)
        for c in r:
            rr, gg, bb = colour_of(c)
            raw += bytes((rr * 255 // 31, gg * 255 // 31, bb * 255 // 31))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "assets"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    out = []

    def label(name):
        out.append(f"{name}::")

    def palettes(name, pals):
        label(name)
        for pal in pals:
            out.append("    dw " + ",".join(f"${rgb15(C[c]):04X}" for c in pal))

    palettes("GamePalettes", art.GAME_PALETTES)
    palettes("TitlePalettes", art.TITLE_PALETTES)
    label("ObjPalettes")
    for pal in art.OBJ_PALETTES:
        out.append("    dw " + ",".join(f"${rgb15(c):04X}" for c in pal))

    # font: BG slots 0.., text in colour 3 of the text palette
    label("FontTiles")
    for ch in FONT_ORDER:
        t = [[0] * 8 for _ in range(8)]
        for y, row in enumerate(glyph_rows(ch)):
            for x, b in enumerate(row):
                if b:
                    t[y][x + 1] = art.TEXT_COLOUR
        out += db_lines(encode_2bpp(t))
    label("FontTilesEnd")
    charmap = [f'    CHARMAP "{ch}", {i}' for i, ch in enumerate(FONT_ORDER)]

    first = 64
    report = []
    for name, cv, pals in (("Game", art.scene_game(), art.GAME_PALETTES),
                           ("Title", art.scene_title(text_font), art.TITLE_PALETTES)):
        tiles, tmap, amap, preview, lossy = build_screen(cv, pals, first)
        if first + len(tiles) > 512:
            raise SystemExit(f"{name}: {len(tiles)} tiles do not fit")
        label(f"{name}Tiles")
        for bank, addr, data in chunks_for(tiles, first):
            out.append(f"    db {bank}")
            out.append(f"    dw ${addr:04X}, {len(data) // 16}")
            out += db_lines(data)
        out.append("    db $FF")
        label(f"{name}Map")
        out += db_lines(tmap, 20)
        label(f"{name}Attr")
        out += db_lines(amap, 20)
        write_png(os.path.join(args.out, f"preview_{name.lower()}.png"), preview, lambda c: C[c])
        report.append(f"{name}: {len(tiles)} unique tiles, {lossy} tiles colour-mapped")

    # small sprites: VRAM bank 0 from $8000
    obj = []

    def add_obj(store, top, bot):
        n = len(store)
        store.append(encode_2bpp(top))
        store.append(encode_2bpp(bot))
        return n

    label("PaddleSprites")   # per size: count, x offset of first column, then tile numbers
    for w in PADDLE_WIDTHS:
        img, cols = paddle_image(w)
        ids = [add_obj(obj, t, b) for t, b in obj_tiles_8x16(img)]
        out.append(f"    db {cols}, {-(cols * 8) // 2 & 0xFF}, " + ",".join(str(i) for i in ids)
                   + ",0" * (3 - cols))
    label("PuckSprites")
    for d in PUCK_SIZES:
        (t, b), = obj_tiles_8x16(puck_image(d))
        out.append(f"    db {add_obj(obj, t, b)}")
    label("ObjTiles")
    out += db_lines(b"".join(obj))
    label("ObjTilesEnd")

    # opponents: VRAM bank 1 from $8000, 24x32 = 3 x 2 pieces of 8x16 per frame
    chars = []
    char_imgs = []
    label("CharSprites")
    for _, fn in art.CHARACTERS:
        for hit in (False, True):
            img = fn(hit)
            char_imgs.append(img)
            ids = [add_obj(chars, t, b) for t, b in obj_tiles_8x16(img)]
            out.append("    db " + ",".join(str(i) for i in ids))
    label("CharTiles")
    out += db_lines(b"".join(chars))
    label("CharTilesEnd")
    if len(obj) > 128 or len(chars) > 256:
        raise SystemExit("too many sprite tiles")

    label("PerspY")
    out += db_lines(bytes(min(255, round(screen_y(min(z, 280)))) for z in range(256)))
    label("PerspScale")
    out += db_lines(bytes(min(255, round(xscale64(min(z, 280)))) for z in range(256)))

    def nearest(vals, v):
        return min(range(len(vals)), key=lambda i: abs(vals[i] - v))
    label("PaddleSizeByZ")
    out += db_lines(bytes(nearest(PADDLE_WIDTHS, 16 * xscale64(min(z * 4, 250)) / 64) for z in range(64)))
    label("PuckSizeByZ")
    out += db_lines(bytes(nearest(PUCK_SIZES, 6 * xscale64(min(z * 4, 250)) / 64) for z in range(64)))

    consts = [
        "; generated by gbc/tools/makeassets.py",
        f"DEF Z_NEAR EQU {art.Z_NEAR}",
        f"DEF TABLE_HALF EQU {art.TABLE_HALF}",
        f"DEF CENTER_X EQU {art.CENTER_X}",
        f"DEF NUM_FONT_CHARS EQU {len(FONT_ORDER)}",
        f"DEF CHAR_ZERO EQU {FONT_ORDER.index('0')}",
        f"DEF CHAR_SPACE EQU {FONT_ORDER.index(' ')}",
        f"DEF TEXT_PALETTE EQU {art.TEXT_PALETTE}",
    ]
    with open(os.path.join(args.out, "consts.inc"), "w") as f:
        f.write("\n".join(consts + charmap) + "\n")
    with open(os.path.join(args.out, "assets.inc"), "w") as f:
        f.write("; generated by gbc/tools/makeassets.py -- do not edit\n" + "\n".join(out) + "\n")

    # sprite sheet preview: opponents with their palettes
    sheet = [[(0, 0, 0)] * (24 * 6 + 5) for _ in range(32)]
    for i, img in enumerate(char_imgs):
        pal = art.OBJ_PALETTES[3 + i // 2]
        for y in range(32):
            for x in range(24):
                v = img[y][x]
                sheet[y][i * 25 + x] = pal[v] if v else (12, 12, 14)
    write_png(os.path.join(args.out, "preview_sprites.png"), sheet, lambda c: c)
    for r in report:
        print(r)
    print(f"sprite tiles: {len(obj)} small, {len(chars)} opponents")


if __name__ == "__main__":
    main()
