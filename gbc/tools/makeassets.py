#!/usr/bin/env python3
"""Generate all graphics for Skydeck Slide (original art, drawn in code).

Everything here is our own: the scene is drawn procedurally from the same
perspective maths the game uses, sprites come from gbc/art/sprites.txt, and
the font is defined below. Output goes to gbc/build/assets/ as RGBDS include
files, plus PNG previews (written with zlib, no third-party modules).

  python3 -I gbc/tools/makeassets.py [--out gbc/build/assets]
"""
import argparse
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------------------
# world and perspective (shared with the game code through consts.inc)
# ---------------------------------------------------------------------------
Z_NEAR = 192          # player's end of the table
TABLE_HALF = 48       # table half width in world units
PERSP_D = 288         # distance of the eye behind the far end
Y_A, Y_B = 4, 12672   # screen y = Y_A + Y_B / (PERSP_D - z)
CENTER_X = 80


def screen_y(z):
    return Y_A + Y_B / (PERSP_D - z)


def xscale64(z):
    """Screen pixels per world unit, times 64."""
    return 32 * PERSP_D / (PERSP_D - z)


def screen_x(x, z):
    return CENTER_X + x * xscale64(z) / 64


def z_at_y(y):
    return PERSP_D - Y_B / (y - Y_A)


# ---------------------------------------------------------------------------
# colours (GBC 5-bit RGB) and palettes
# ---------------------------------------------------------------------------
C = {
    "sky": (2, 2, 9), "haze": (7, 3, 13), "star": (31, 31, 22), "bldg": (5, 4, 11),
    "window": (31, 25, 8), "deck": (9, 8, 12), "deckd": (6, 5, 9),
    "surf": (1, 9, 12), "line": (7, 21, 23), "rail": (24, 9, 3), "railhi": (31, 20, 9),
    "white": (31, 31, 31), "gold": (31, 24, 4), "black": (0, 0, 0), "red": (26, 4, 6),
    "dark": (3, 2, 6),
}
BG_PALETTES = [
    ["sky", "haze", "bldg", "window"],       # 0 skyline
    ["sky", "haze", "star", "bldg"],         # 1 stars
    ["surf", "line", "rail", "railhi"],      # 2 table surface + rail
    ["deck", "deckd", "rail", "railhi"],     # 3 rooftop deck + rail
    ["sky", "white", "gold", "haze"],        # 4 text
    ["deck", "surf", "rail", "railhi"],      # 5 corner tiles (deck + rail + surface)
    ["sky", "gold", "red", "dark"],          # 6 title logo
    ["deck", "white", "gold", "deckd"],      # 7 text on the deck
]
# colours that may be merged when a tile does not fit any palette
SUBSTITUTE = {"line": "surf", "star": "haze", "window": "bldg", "deckd": "deck", "haze": "sky"}

OBJ_PALETTES = [
    [(0, 0, 0), (2, 4, 10), (8, 20, 31), (24, 30, 31)],     # 0 player paddle (blue)
    [(0, 0, 0), (12, 2, 2), (28, 6, 6), (31, 22, 20)],      # 1 opponent paddle (red)
    [(0, 0, 0), (4, 4, 4), (28, 28, 26), (31, 31, 31)],     # 2 puck
    [(0, 0, 0), (30, 26, 18), (6, 18, 6), (14, 10, 4)],     # 3 Tomo
    [(0, 0, 0), (31, 30, 28), (30, 14, 3), (6, 3, 3)],      # 4 Rusty
    [(0, 0, 0), (31, 31, 31), (20, 8, 26), (4, 2, 8)],      # 5 Okta
    [(0, 0, 0), (31, 31, 31), (31, 24, 4), (3, 2, 6)],      # 6 cursor/text sprites
    [(0, 0, 0), (8, 8, 8), (16, 16, 16), (24, 24, 24)],     # 7 spare
]

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


# ---------------------------------------------------------------------------
# canvas helpers
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, w=160, h=144, fill="sky"):
        self.w, self.h = w, h
        self.px = [[fill] * w for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def get(self, x, y):
        return self.px[y][x]

    def rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.px[y][x] = c

    def text(self, s, x, y, c, scale=1, shadow=None):
        for i, ch in enumerate(s):
            rows = glyph_rows(ch)
            for ry, row in enumerate(rows):
                for rx, bit in enumerate(row):
                    if bit:
                        for sy in range(scale):
                            for sx in range(scale):
                                px = x + i * 6 * scale + rx * scale + sx
                                py = y + ry * scale + sy
                                if shadow:
                                    self.set(px + 1, py + 1, shadow)
                                self.set(px, py, c)
            if shadow:   # redraw glyph over its own shadow
                for ry, row in enumerate(rows):
                    for rx, bit in enumerate(row):
                        if bit:
                            for sy in range(scale):
                                for sx in range(scale):
                                    self.set(x + i * 6 * scale + rx * scale + sx,
                                             y + ry * scale + sy, c)


def lcg(seed):
    while True:
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        yield seed


def draw_sky(cv, y0, y1, seed=7):
    rnd = lcg(seed)
    for y in range(y0, y1):
        for x in range(cv.w):
            cv.set(x, y, "sky")
    # haze bands near the horizon, dithered
    for y in range(max(y0, y1 - 14), y1):
        for x in range(cv.w):
            if (x + y) % 2 == 0 or y > y1 - 6:
                cv.set(x, y, "haze")
    for _ in range(26):
        x = next(rnd) % cv.w
        y = y0 + next(rnd) % max(1, (y1 - y0 - 16))
        cv.set(x, y, "star")


def draw_skyline(cv, base_y, seed=3):
    rnd = lcg(seed)
    x = 0
    while x < cv.w:
        w = 8 + next(rnd) % 14
        h = 6 + next(rnd) % 18
        for yy in range(base_y - h, base_y):
            for xx in range(x, min(cv.w, x + w)):
                cv.set(xx, yy, "bldg")
        # windows on a 3x3 grid, some lit
        for yy in range(base_y - h + 2, base_y - 1, 3):
            for xx in range(x + 2, x + w - 1, 3):
                if next(rnd) % 3 == 0:
                    cv.set(xx, yy, "window")
        x += w + next(rnd) % 3


def rail_width(z):
    return max(13, round(14 * xscale64(z) / 64))


def draw_table(cv):
    """Rooftop deck, the table in perspective, rails and grid lines."""
    far_y = round(screen_y(0))
    near_y = cv.h
    cv.rect(0, 40, cv.w, cv.h, "deck")
    # deck planks: darker lines every 8 rows (perspective-free, it is decoration)
    for y in range(44, cv.h, 9):
        for x in range(cv.w):
            if cv.get(x, y) == "deck":
                cv.set(x, y, "deckd")
    # far backboard rail across the end of the table
    left0 = round(screen_x(-TABLE_HALF, 0))
    right0 = round(screen_x(TABLE_HALF, 0))
    rw0 = rail_width(0)
    cv.rect(left0 - rw0, far_y - 5, right0 + rw0 + 1, far_y, "rail")
    cv.rect(left0, far_y - 1, right0 + 1, far_y, "railhi")
    for y in range(far_y, near_y):
        z = z_at_y(y + 0.5)
        lx = screen_x(-TABLE_HALF, z)
        rx = screen_x(TABLE_HALF, z)
        rw = rail_width(z)
        for x in range(cv.w):
            if lx <= x + 0.5 <= rx:
                cv.set(x, y, "surf")
            elif lx - rw <= x + 0.5 < lx or rx < x + 0.5 <= rx + rw:
                inner = (lx - 2 <= x + 0.5 < lx) or (rx < x + 0.5 <= rx + 2)
                cv.set(x, y, "railhi" if inner else "rail")
    # grid: depth lines every 48 units, side lines at x = -24, 0, 24
    for zl in (48, 96, 144):
        y = round(screen_y(zl))
        for x in range(round(screen_x(-TABLE_HALF, zl)) + 1, round(screen_x(TABLE_HALF, zl))):
            cv.set(x, y, "line")
    for xl in (-24, 0, 24):
        for y in range(far_y, near_y):
            z = z_at_y(y + 0.5)
            cv.set(round(screen_x(xl, z) - 0.5), y, "line")
    # centre spot
    cy = round(screen_y(96))
    for dx in (-2, -1, 0, 1, 2):
        cv.set(CENTER_X + dx, cy - 1, "line")
        cv.set(CENTER_X + dx, cy + 1, "line")


def scene_game():
    cv = Canvas()
    draw_sky(cv, 0, 40)
    draw_skyline(cv, 40)
    draw_table(cv)
    cv.rect(0, 0, cv.w, 8, "sky")          # HUD row, written by the game
    return cv


def scene_title():
    cv = Canvas()
    draw_sky(cv, 0, 88, seed=11)
    draw_skyline(cv, 88, seed=5)
    cv.rect(0, 88, cv.w, cv.h, "deck")
    for y in range(92, cv.h, 9):
        cv.rect(0, y, cv.w, y + 1, "deckd")
    # logo: two words in the 5x7 font at 3x, gold on a dark slab
    cv.rect(8, 14, 152, 70, "dark")
    cv.text("SKYDECK", 17, 18, "gold", scale=3, shadow="red")
    cv.text("SLIDE", 35, 44, "gold", scale=3, shadow="red")
    return cv


# ---------------------------------------------------------------------------
# tiles, palettes, maps
# ---------------------------------------------------------------------------
def tile_colors(cv, tx, ty):
    return [[cv.get(tx * 8 + x, ty * 8 + y) for x in range(8)] for y in range(8)]


def fit_palette(pix, palettes, where):
    cols = {c for row in pix for c in row}
    for attempt in range(len(SUBSTITUTE) + 1):
        for i, pal in enumerate(palettes):
            if cols <= set(pal):
                return i, pix
        # merge one substitutable colour and retry
        for a, b in SUBSTITUTE.items():
            if a in cols:
                pix = [[b if c == a else c for c in row] for row in pix]
                cols = {c for row in pix for c in row}
                break
    raise SystemExit(f"tile {where} colours {sorted(cols)} fit no palette")


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


def build_screen(cv, first_slot):
    """Turn a canvas into tiles + map + attributes. Tile slots start at first_slot."""
    ts = TileSet()
    raw = []
    for ty in range(18):
        for tx in range(20):
            pal, pix = fit_palette(tile_colors(cv, tx, ty), BG_PALETTES, (tx, ty))
            idx = [[BG_PALETTES[pal].index(c) for c in row] for row in pix]
            t, flip = ts.add(idx)
            raw.append((t, flip, pal))
    tmap, amap = bytearray(), bytearray()
    for t, flip, pal in raw:
        slot = first_slot + t
        bank = 0 if slot < 256 else 1
        tmap.append(slot & 0xFF)
        amap.append(pal | flip | (bank << 3))
    return ts.tiles, tmap, amap


def bg_tile_address(slot):
    """LCDC.4 = 0: tile 0-127 at $9000, 128-255 at $8800; slots >= 256 are VRAM bank 1."""
    n = slot & 0xFF
    return 1 if slot >= 256 else 0, (0x9000 + n * 16) if n < 128 else (0x8800 + (n - 128) * 16)


def chunks_for(tiles, first_slot):
    """Group consecutive tiles into (bank, address, data) runs that do not cross regions."""
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
def load_sprites(path):
    sprites = {}
    with open(path) as f:
        lines = [l.rstrip("\n") for l in f]
    i = 0
    while i < len(lines):
        l = lines[i].strip()
        if l.startswith("sprite "):
            _, name, size = l.split()
            w, h = (int(v) for v in size.split("x"))
            rows = [r.ljust(w, ".")[:w] for r in lines[i + 1:i + 1 + h]]
            sprites[name] = [[0 if c == "." else int(c) for c in r] for r in rows]
            i += 1 + h
        else:
            i += 1
    return sprites


def obj_tiles_8x16(img):
    """Cut an image (w multiple of 8, h multiple of 16) into 8x16 columns, left to right, top to bottom."""
    h = len(img)
    w = len(img[0])
    out = []
    for oy in range(0, h, 16):
        for ox in range(0, w, 8):
            top = [row[ox:ox + 8] for row in img[oy:oy + 8]]
            bot = [row[ox:ox + 8] for row in img[oy + 8:oy + 16]]
            out.append((top, bot))
    return out


PADDLE_WIDTHS = [8, 10, 12, 14, 16, 18, 21, 24]
PUCK_SIZES = [3, 4, 5, 6, 7, 8]


def paddle_image(w):
    h = 3 if w < 14 else 4
    cols = (w + 7) // 8
    img = [[0] * (cols * 8) for _ in range(16)]
    x0 = (cols * 8 - w) // 2
    for y in range(h):
        for x in range(w):
            edge = x in (0, w - 1) or y == h - 1
            img[y][x0 + x] = 1 if edge else (3 if y == 0 else 2)
    return img, cols, x0


def puck_image(d):
    img = [[0] * 8 for _ in range(16)]
    r = d / 2
    for y in range(d):
        for x in range(d):
            dx, dy = x + 0.5 - r, y + 0.5 - r
            if dx * dx + dy * dy <= r * r + 0.3:
                edge = dx * dx + dy * dy > (r - 1) ** 2
                hi = dx < 0 and dy < 0 and d >= 5 and not edge
                img[y + (8 - d) // 2][x + (8 - d) // 2] = 3 if hi else (1 if edge else 2)
    return img


# ---------------------------------------------------------------------------
# output
# ---------------------------------------------------------------------------
def rgb15(c):
    r, g, b = c
    return r | g << 5 | b << 10


def db_lines(data, per=16):
    return ["    db " + ",".join(f"${b:02X}" for b in data[i:i + per]) for i in range(0, len(data), per)]


def write_png(path, cv_or_rows, colors):
    rows = cv_or_rows
    h = len(rows)
    w = len(rows[0])
    raw = bytearray()
    for r in rows:
        raw.append(0)
        for c in r:
            rr, gg, bb = colors[c]
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

    # palettes
    label("BgPalettes")
    for pal in BG_PALETTES:
        out.append("    dw " + ",".join(f"${rgb15(C[c]):04X}" for c in pal))
    label("ObjPalettes")
    for pal in OBJ_PALETTES:
        out.append("    dw " + ",".join(f"${rgb15(c):04X}" for c in pal))

    # font: bank 0, BG slots 0.. (white on palette colour 0)
    font_tiles = []
    for ch in FONT_ORDER:
        t = [[0] * 8 for _ in range(8)]
        for y, row in enumerate(glyph_rows(ch)):
            for x, b in enumerate(row):
                if b:
                    t[y][x + 1] = 1
        font_tiles.append(t)
    label("FontTiles")
    data = b"".join(encode_2bpp(t) for t in font_tiles)
    out += db_lines(data)
    label("FontTilesEnd")
    out.append(f"DEF FONT_FIRST_SLOT EQU 0")
    charmap = [f'    CHARMAP "{ch}", {i}' for i, ch in enumerate(FONT_ORDER)]

    # screens: tiles start after the font
    first = 64
    previews = {}
    for name, cv in (("Game", scene_game()), ("Title", scene_title())):
        tiles, tmap, amap = build_screen(cv, first)
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
        previews[name] = (cv, len(tiles))

    # sprites (OBJ tiles, 8x16 mode, VRAM bank 0 from $8000)
    obj = []          # list of 16-byte tiles in order

    def add_obj(top, bot):
        n = len(obj)
        obj.append(encode_2bpp(top))
        obj.append(encode_2bpp(bot))
        return n

    label("PaddleSprites")   # per size: count, x offset of first column, then tile numbers
    for w in PADDLE_WIDTHS:
        img, cols, x0 = paddle_image(w)
        ids = [add_obj(t, b) for t, b in obj_tiles_8x16(img)]
        out.append(f"    db {cols}, {-(cols * 8) // 2 & 0xFF}, " + ",".join(str(i) for i in ids)
                   + ",0" * (3 - cols))
    label("PuckSprites")
    for d in PUCK_SIZES:
        img = puck_image(d)
        (t, b), = obj_tiles_8x16(img)
        out.append(f"    db {add_obj(t, b)}")
    sprites = load_sprites(os.path.join(ROOT, "art", "sprites.txt"))
    label("CharSprites")       # each frame: 6 tiles (2 wide x 2 tall of 8x16, 16x32)
    for name in ("tomo_idle", "tomo_hit", "rusty_idle", "rusty_hit", "okta_idle", "okta_hit"):
        img = sprites[name] + [[0] * 16 for _ in range(32 - len(sprites[name]))]
        ids = [add_obj(t, b) for t, b in obj_tiles_8x16(img)]
        out.append("    db " + ",".join(str(i) for i in ids))
    if len(obj) > 256:
        raise SystemExit("too many OBJ tiles")
    label("ObjTiles")
    out += db_lines(b"".join(obj))
    label("ObjTilesEnd")

    # perspective tables, z = 0..255
    label("PerspY")
    out += db_lines(bytes(min(255, round(screen_y(min(z, 280)))) for z in range(256)))
    label("PerspScale")
    out += db_lines(bytes(min(255, round(xscale64(min(z, 280)))) for z in range(256)))

    def nearest(vals, v):
        return min(range(len(vals)), key=lambda i: abs(vals[i] - v))
    label("PaddleSizeByZ")     # indexed by z/4
    out += db_lines(bytes(nearest(PADDLE_WIDTHS, 16 * xscale64(min(z * 4, 250)) / 64) for z in range(64)))
    label("PuckSizeByZ")
    out += db_lines(bytes(nearest(PUCK_SIZES, 6 * xscale64(min(z * 4, 250)) / 64) for z in range(64)))

    consts = [
        "; generated by gbc/tools/makeassets.py",
        f"DEF Z_NEAR EQU {Z_NEAR}",
        f"DEF TABLE_HALF EQU {TABLE_HALF}",
        f"DEF CENTER_X EQU {CENTER_X}",
        f"DEF NUM_FONT_CHARS EQU {len(FONT_ORDER)}",
        f"DEF CHAR_ZERO EQU {FONT_ORDER.index('0')}",
        f"DEF CHAR_SPACE EQU {FONT_ORDER.index(' ')}",
    ]
    with open(os.path.join(args.out, "consts.inc"), "w") as f:
        f.write("\n".join(consts + charmap) + "\n")
    with open(os.path.join(args.out, "assets.inc"), "w") as f:
        f.write("; generated by gbc/tools/makeassets.py -- do not edit\n" + "\n".join(out) + "\n")

    for name, (cv, n) in previews.items():
        write_png(os.path.join(args.out, f"preview_{name.lower()}.png"), cv.px, C)
        print(f"{name}: {n} unique tiles")
    print(f"OBJ tiles: {len(obj)}")


if __name__ == "__main__":
    main()
