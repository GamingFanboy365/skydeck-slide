"""Skydeck Slide artwork, drawn in code (all original).

Palettes are shading ramps of one material each (dark -> light), every
surface gets texture (stipple noise, dithered gradients, grain), and sprites
get a dark outline with light coming from the top left.
"""
import math

# ---------------------------------------------------------------------------
# perspective (shared with the game through generated tables)
# ---------------------------------------------------------------------------
Z_NEAR = 192
TABLE_HALF = 48
PERSP_D = 288
Y_A, Y_B = 4, 12672
CENTER_X = 80


def screen_y(z):
    return Y_A + Y_B / (PERSP_D - z)


def xscale64(z):
    return 32 * PERSP_D / (PERSP_D - z)


def screen_x(x, z):
    return CENTER_X + x * xscale64(z) / 64


def z_at_y(y):
    return PERSP_D - Y_B / (y - Y_A)


# ---------------------------------------------------------------------------
# colours (5-bit RGB) grouped in ramps
# ---------------------------------------------------------------------------
C = {
    # night sky, darkest at the top
    "s0": (1, 1, 5), "s1": (3, 2, 9), "s2": (7, 3, 13), "moon": (31, 30, 23),
    # skyline
    "b0": (2, 1, 5), "b1": (5, 3, 10), "win": (31, 24, 9),
    # brick parapet
    "br0": (6, 2, 3), "br1": (12, 4, 4), "br2": (18, 7, 6), "mortar": (14, 10, 11),
    # wooden deck
    "w0": (5, 3, 3), "w1": (9, 6, 5), "w2": (13, 9, 7), "w3": (19, 14, 10),
    # table surface
    "t0": (0, 4, 8), "t1": (1, 8, 12), "t2": (5, 18, 21), "t3": (16, 28, 29),
    # copper rails
    "r0": (10, 3, 1), "r1": (21, 8, 2), "r2": (29, 17, 6), "r3": (31, 29, 19),
    # title logo
    "gold": (31, 25, 6), "orange": (30, 13, 3), "red": (17, 3, 4), "panel": (2, 1, 6),
    "cream": (31, 31, 22),
    # jungle (Tomo): sky, distant canopy, leaves, bark, bamboo, treehouse wood
    "jsky": (14, 24, 30), "jf1": (6, 15, 12), "jl0": (1, 5, 3), "jl1": (4, 13, 4),
    "jl2": (10, 21, 6), "bk0": (6, 3, 2), "bk1": (12, 7, 4), "bk2": (18, 12, 7),
    "bb0": (6, 8, 2), "bb1": (14, 18, 4), "bb2": (22, 26, 8), "bb3": (29, 30, 18),
    "jw0": (8, 5, 3), "jw1": (14, 9, 5), "jw2": (19, 13, 7), "jw3": (25, 19, 11),
    # sunset pier (Okta): sky, sea, rope, weathered pier wood
    "sk0": (8, 2, 12), "sk1": (24, 7, 15), "sk2": (31, 16, 6),
    "sea0": (2, 3, 10), "sea1": (6, 9, 19), "sea2": (13, 15, 24),
    "rp0": (9, 6, 3), "rp1": (19, 14, 7), "rp2": (26, 21, 12), "rp3": (31, 28, 19),
    "pw0": (6, 5, 6), "pw1": (12, 10, 10), "pw2": (17, 14, 12), "pw3": (23, 20, 16),
    # snow lodge (Pip): night, aurora, mountains, pines, ice rails, lodge wood
    "n0": (1, 2, 7), "n1": (3, 5, 13), "aur": (6, 26, 16), "snow": (30, 31, 31),
    "mt0": (9, 12, 20), "mt1": (18, 22, 28), "pine0": (1, 6, 6), "pine1": (4, 12, 10),
    "ice0": (6, 11, 18), "ice1": (13, 21, 27), "ice2": (21, 28, 31), "ice3": (31, 31, 31),
    "lw0": (4, 6, 11), "lw1": (9, 12, 18), "lw2": (14, 18, 24), "lw3": (24, 28, 31),
    # desert canyon (Zuri): noon sky, mesas, cacti, adobe, sandstone, bleached wood
    "dhud": (8, 4, 2), "dsky0": (12, 20, 31), "dsky1": (22, 27, 31),
    "m0": (14, 4, 2), "m1": (24, 10, 4), "m2": (30, 18, 9),
    "c0": (2, 8, 3), "c1": (6, 15, 5), "c2": (13, 22, 8),
    "a0": (15, 8, 4), "a1": (22, 14, 8), "a2": (27, 20, 12), "a3": (31, 26, 17),
    "ss0": (13, 6, 3), "ss1": (22, 12, 6), "ss2": (28, 19, 10), "ss3": (31, 27, 18),
    "bw0": (10, 8, 6), "bw1": (17, 14, 10), "bw2": (23, 20, 15), "bw3": (28, 26, 20),
    # volcano forge (Blaze): smoky red night, lava, basalt, obsidian, stone floor
    "v0": (2, 0, 1), "v1": (7, 1, 3), "v2": (14, 3, 4), "lavaY": (31, 28, 10),
    "rock0": (5, 3, 5), "rock1": (13, 8, 9), "rock2": (20, 14, 13), "lavaO": (31, 13, 2),
    "lavaR": (22, 3, 1),
    "ob0": (2, 1, 4), "ob1": (7, 4, 11), "ob2": (14, 10, 20), "ob3": (31, 16, 4),
    "st0": (4, 3, 3), "st1": (8, 6, 6), "st2": (12, 10, 9), "st3": (17, 14, 12),
    # moon base (Nova): space, earth, moon ground, metal panels, chrome rails
    "sp0": (0, 0, 2), "sp1": (2, 3, 8), "spd": (14, 14, 18), "white": (31, 31, 31),
    "eb": (5, 12, 27), "eg": (7, 20, 8),
    "mg0": (6, 6, 8), "mg1": (12, 12, 14), "mg2": (19, 19, 21), "mg3": (26, 26, 27),
    "pn0": (4, 5, 8), "pn1": (9, 11, 15), "pn2": (15, 18, 22), "pnl": (10, 28, 31),
    "ch0": (5, 6, 9), "ch1": (13, 15, 19), "ch2": (22, 24, 27), "ch3": (31, 31, 31),
    "fl0": (4, 4, 6), "fl1": (8, 9, 11), "fl2": (12, 13, 16), "fl3": (17, 18, 21),
    # hall of rivals: panelled wall, spotlight, trophies, marble podium, carpet
    "h0": (4, 2, 3), "h1": (9, 4, 4), "h2": (14, 7, 5), "h3": (20, 11, 7),
    "spot": (27, 22, 14), "spot2": (31, 29, 21),
    "tg0": (12, 7, 1), "tg1": (24, 17, 3), "tg2": (31, 27, 9),
    "mb0": (9, 9, 12), "mb1": (17, 17, 20), "mb2": (24, 24, 26), "mb3": (31, 31, 31),
    "cp0": (8, 1, 3), "cp1": (15, 2, 5), "cp2": (22, 5, 8),
    # chalkboard
    "cb0": (3, 10, 7), "cb1": (5, 13, 9), "chd": (16, 21, 18), "chk": (30, 31, 29),
}

PAL_SKY = ["s0", "s1", "s2", "moon"]            # also the text palette (text = colour 3)
PAL_SKYLINE = ["s2", "b0", "b1", "win"]
PAL_OUTER = ["w1", "w2", "r0", "r1"]           # deck meets rail
PAL_BRICK = ["br0", "br1", "br2", "mortar"]
PAL_INNER = ["t0", "t1", "r1", "r2"]           # rail meets table
PAL_WOOD = ["w0", "w1", "w2", "w3"]
PAL_TABLE = ["t0", "t1", "t2", "t3"]
PAL_RAIL = ["r0", "r1", "r2", "r3"]
PAL_LOGO = ["panel", "gold", "orange", "red"]
PAL_LOGO_HI = ["panel", "cream", "gold", "orange"]
PAL_FRAME_EDGE = ["panel", "r0", "r1", "r2"]

CITY_PALETTES = [PAL_SKY, PAL_SKYLINE, PAL_OUTER, PAL_BRICK, PAL_INNER, PAL_WOOD, PAL_TABLE, PAL_RAIL]
JUNGLE_PALETTES = [
    ["jl0", "jsky", "jf1", "cream"],        # 0 HUD, sky, distant canopy, clouds/sun
    ["jw1", "jw2", "bb0", "bb1"],           # 1 deck meets rail
    ["jsky", "jl0", "jl1", "jl2"],          # 2 leaves against the sky
    ["jl0", "bk0", "bk1", "bk2"],           # 3 bark and logs
    ["t0", "t1", "bb1", "bb2"],             # 4 rail meets table
    ["jw0", "jw1", "jw2", "jw3"],           # 5 treehouse deck
    PAL_TABLE,                              # 6
    ["bb0", "bb1", "bb2", "bb3"],           # 7 bamboo rails
]
BEACH_PALETTES = [
    ["sk0", "sk1", "sk2", "cream"],         # 0 HUD, sunset sky, sun
    ["sea0", "sea1", "sea2", "sk2"],        # 1 sea with sunset glints
    ["pw1", "pw2", "rp0", "rp1"],           # 2 deck meets rail
    ["sk2", "cream", "sea1", "sea0"],       # 3 sun and its reflection
    ["t0", "t1", "rp1", "rp2"],             # 4 rail meets table
    ["pw0", "pw1", "pw2", "pw3"],           # 5 pier planks
    PAL_TABLE,                              # 6
    ["rp0", "rp1", "rp2", "rp3"],           # 7 rope rails
]
SNOW_PALETTES = [
    ["n0", "n1", "aur", "snow"],            # 0 HUD, night sky, aurora
    ["n1", "mt0", "mt1", "snow"],           # 1 mountains
    ["mt1", "pine0", "pine1", "snow"],      # 2 pines in the snow
    ["lw1", "lw2", "ice0", "ice1"],         # 3 deck meets rail (snow banks use palette 1)
    ["t0", "t1", "ice1", "ice2"],           # 4 rail meets table
    ["lw0", "lw1", "lw2", "lw3"],           # 5 lodge deck
    PAL_TABLE,
    ["ice0", "ice1", "ice2", "ice3"],       # 7 ice rails
]
DESERT_PALETTES = [
    ["dhud", "dsky0", "dsky1", "cream"],    # 0 HUD, sky, sun
    ["dsky1", "m0", "m1", "m2"],            # 1 mesas
    ["m1", "c0", "c1", "c2"],               # 2 cacti
    ["a0", "a1", "a2", "a3"],               # 3 adobe wall
    ["t0", "t1", "ss1", "ss2"],             # 4 rail meets table
    ["bw0", "bw1", "bw2", "bw3"],           # 5 sun-bleached deck
    PAL_TABLE,
    ["ss0", "ss1", "ss2", "ss3"],           # 7 sandstone rails
]
VOLCANO_PALETTES = [
    ["v0", "v1", "v2", "lavaY"],            # 0 HUD, smoky sky
    ["v1", "rock0", "rock1", "lavaO"],      # 1 volcano with glowing flows
    ["lavaR", "lavaO", "lavaY", "rock0"],   # 2 lava
    ["rock0", "rock1", "rock2", "lavaO"],   # 3 basalt wall
    ["t0", "t1", "ob1", "ob2"],             # 4 rail meets table
    ["st0", "st1", "st2", "st3"],           # 5 stone floor
    PAL_TABLE,
    ["ob0", "ob1", "ob2", "ob3"],           # 7 obsidian rails with ember cracks
]
MOON_PALETTES = [
    ["sp0", "sp1", "spd", "white"],         # 0 HUD, space, stars
    ["sp0", "eb", "eg", "white"],           # 1 the Earth
    ["mg0", "mg1", "mg2", "mg3"],           # 2 moon ground
    ["pn0", "pn1", "pn2", "pnl"],           # 3 base wall panels with lights
    ["t0", "t1", "ch1", "ch2"],             # 4 rail meets table
    ["fl0", "fl1", "fl2", "fl3"],           # 5 metal floor
    PAL_TABLE,
    ["ch0", "ch1", "ch2", "ch3"],           # 7 chrome rails
]
GAME_PALETTES = CITY_PALETTES
BOARD_PALETTE = 7
TITLE_PALETTES = [PAL_SKY, PAL_SKYLINE, PAL_LOGO, PAL_BRICK, PAL_LOGO_HI, PAL_WOOD,
                  PAL_FRAME_EDGE, PAL_RAIL]
TEXT_PALETTE = 0
TEXT_COLOUR = 3

OBJ_PALETTES = [
    [(0, 0, 0), (2, 3, 9), (7, 17, 30), (22, 29, 31)],      # 0 player paddle (blue)
    [(0, 0, 0), (10, 1, 2), (26, 6, 6), (31, 22, 18)],      # 1 opponent paddle (red)
    [(0, 0, 0), (5, 5, 7), (22, 22, 24), (31, 31, 31)],     # 2 puck
    [(0, 0, 0), (29, 25, 15), (8, 19, 7), (2, 6, 3)],       # 3 Tomo: skin, shell, outline
    [(0, 0, 0), (31, 30, 26), (29, 13, 3), (7, 2, 2)],      # 4 Rusty: white, fur, outline
    [(0, 0, 0), (30, 26, 31), (19, 7, 25), (5, 1, 9)],      # 5 Okta: light, body, outline
    [(0, 0, 0), (12, 7, 3), (24, 15, 7), (31, 28, 18)],     # 6 Tomo extra (unused)
    [(0, 0, 0), (8, 8, 8), (16, 16, 16), (24, 24, 24)],     # 7 spare
]


# ---------------------------------------------------------------------------
# texture helpers
# ---------------------------------------------------------------------------
BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def noise(x, y, seed=0, period=16):
    """Cheap hash noise in [0,1). A small period keeps tiles repeating."""
    x %= period
    y %= period
    h = (x * 374761393 + y * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536


def dither(x, y, t):
    """True on a fraction t of pixels, ordered so gradients look smooth."""
    return BAYER4[y % 4][x % 4] < t * 16


class Canvas:
    def __init__(self, w=160, h=144, fill="s0"):
        self.w, self.h = w, h
        self.px = [[fill] * w for _ in range(h)]

    def set(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def get(self, x, y):
        return self.px[y][x]

    def rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.px[y][x] = c


# ---------------------------------------------------------------------------
# scene pieces
# ---------------------------------------------------------------------------
def draw_sky(cv, y0, y1, moon=(132, 20)):
    span = y1 - y0
    for y in range(y0, y1):
        t = (y - y0) / span
        for x in range(cv.w):
            if t < 0.45:
                c = "s1" if dither(x, y, t / 0.45 * 0.5) else "s0"
            else:
                c = "s2" if dither(x, y, (t - 0.45) / 0.55) else "s1"
            cv.set(x, y, c)
    # stars: a few bright, more faint
    for i in range(40):
        x = int(noise(i, 1, 3, 997) * cv.w)
        y = y0 + int(noise(i, 2, 3, 997) * span * 0.7)
        cv.set(x, y, "moon" if i % 4 == 0 else "s2")
        if i % 9 == 0:                       # a twinkle cross
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cv.set(x + dx, y + dy, "s2")
    if moon:
        mx, my = moon
        for y in range(my - 9, my + 10):
            for x in range(mx - 9, mx + 10):
                d = math.hypot(x - mx, y - my)
                if d <= 7.5:
                    shade = (x - mx) + (y - my) > 6 and dither(x, y, 0.5)
                    crater = False
                    cv.set(x, y, "s2" if crater or shade else "moon")
                elif d <= 9 and dither(x, y, 0.35):
                    cv.set(x, y, "s2")           # soft halo


def draw_skyline(cv, base_y, seed=3, water_tower=True):
    # far layer: lighter, no windows
    x = 0
    i = 0
    while x < cv.w:
        w = 10 + int(noise(i, 0, seed, 997) * 12)
        h = 10 + int(noise(i, 1, seed, 997) * 10)
        for yy in range(base_y - h, base_y):
            for xx in range(x, min(cv.w, x + w)):
                cv.set(xx, yy, "b1")
        x += w
        i += 1
    # near layer: dark, lit windows, roof details
    x = -4
    i = 0
    while x < cv.w:
        w = 9 + int(noise(i, 3, seed, 997) * 13)
        h = 6 + int(noise(i, 4, seed, 997) * 14)
        top = base_y - h
        for yy in range(top, base_y):
            for xx in range(x, min(cv.w, x + w)):
                cv.set(xx, yy, "b0")
        kind = int(noise(i, 5, seed, 997) * 4)
        if kind == 0:                         # antenna
            for yy in range(top - 6, top):
                cv.set(x + w // 2, yy, "b0")
            cv.set(x + w // 2, top - 7, "win")
        elif kind == 1:                       # stepped roof
            for yy in range(top - 3, top):
                for xx in range(x + 2, x + w - 2):
                    cv.set(xx, yy, "b0")
        for yy in range(top + 2, base_y - 1, 3):
            for xx in range(x + 2, x + w - 1, 3):
                if noise(xx, yy, seed + 9, 997) < 0.45:
                    cv.set(xx, yy, "win")
                    if noise(xx, yy, seed + 4, 997) < 0.3:
                        cv.set(xx + 1, yy, "win")
        x += w + int(noise(i, 6, seed, 997) * 3)
        i += 1
    if water_tower:
        tx, ty = 14, base_y - 22
        for yy in range(ty, ty + 9):          # tank with a lit band
            for xx in range(tx - 6 + (yy == ty), tx + 7 - (yy == ty)):
                cv.set(xx, yy, "b0")
        for xx in range(tx - 7, tx + 8):
            cv.set(xx, ty - 1 + (abs(xx - tx) // 3), "b0")   # cone roof
        for xx in range(tx - 5, tx + 6, 2):
            cv.set(xx, ty + 4, "b1")
        for yy in range(ty + 9, base_y):     # legs and a cross brace
            cv.set(tx - 5, yy, "b0")
            cv.set(tx + 5, yy, "b0")
            cv.set(tx, yy, "b0")
        for k in range(10):
            cv.set(tx - 5 + k, ty + 11 + k // 2, "b0")


def draw_string_lights(cv, y_top, y_sag, x0=0, x1=160, span=40):
    for sx in range(x0, x1, span):
        for x in range(sx, min(x1, sx + span)):
            t = (x - sx) / span
            y = y_top + (y_sag - y_top) * 4 * t * (1 - t)
            cv.set(x, round(y), "b0")
            if (x - sx) % 8 == 4:
                cv.set(x, round(y) + 1, "win")
                cv.set(x, round(y) + 2, "win")


def draw_parapet(cv, y0, y1):
    """Brick wall along the far edge of the roof, with a capstone."""
    for y in range(y0, y1):
        for x in range(cv.w):
            ry = y - y0
            if ry < 2:
                c = "br2" if ry == 0 or noise(x, y, 7) < 0.2 else "br1"
            else:
                row = (ry - 2) // 3
                off = 4 if row % 2 else 0
                if (ry - 2) % 3 == 2 or (x + off) % 8 == 7:
                    c = "mortar" if noise(x, y, 8) < 0.6 else "br0"
                else:
                    c = "br1"
                    if (ry - 2) % 3 == 0 and noise(x, y, 9) < 0.5:
                        c = "br2"
                    elif noise(x, y, 10) < 0.15:
                        c = "br0"
            cv.set(x, y, c)


WOOD_CITY = ("w0", "w1", "w2", "w3")
WOOD_JUNGLE = ("jw0", "jw1", "jw2", "jw3")
WOOD_PIER = ("pw0", "pw1", "pw2", "pw3")


def draw_deck(cv, y0, y1, wood=WOOD_CITY, plank=6):
    """Wooden planks with grain, staggered seams and nails."""
    w0, w1, w2, w3 = wood
    for y in range(y0, y1):
        ry = (y - y0) % plank
        row = (y - y0) // plank
        for x in range(cv.w):
            seam = (x + row * 23) % 40 == 0
            if ry == plank - 1 or seam:
                c = w0
            elif ry == 0:
                c = w3 if noise(x, y, 11) < 0.6 else w2
            else:
                g = noise(x // 3, y, 12 + row % 3)
                c = w1 if g < 0.25 else (w3 if g > 0.93 else w2)
            cv.set(x, y, c)
        for x in range(cv.w):
            if ry == 2 and ((x + row * 23) % 40 in (3, 37)):
                cv.set(x, y, w0)                    # nail heads


def rail_width(z):
    return max(12, round(13 * xscale64(z) / 64))


def draw_crates(cv, x0, y0, wood=WOOD_CITY):
    """A small stack of wooden crates on the deck."""
    w0, w1, w2, w3 = wood
    for bx, by, sz in ((x0, y0 + 10, 14), (x0 + 14, y0 + 13, 11), (x0 + 4, y0, 10)):
        for y in range(by, by + sz):
            for x in range(bx, bx + sz):
                edge = x in (bx, bx + sz - 1) or y in (by, by + sz - 1)
                diag = abs((x - bx) - (y - by)) <= 0 and not edge
                if edge or diag:
                    c = w0
                elif y == by + 1 or x == bx + 1:
                    c = w3
                else:
                    c = w2 if noise(x, y, 13) > 0.2 else w1
                cv.set(x, y, c)


# ---------------------------------------------------------------------------
# deck props, each drawn in a 4-tone ramp (dark .. light) so it shares the
# stage's deck palette: outline in the darkest tone, light from the top left
# ---------------------------------------------------------------------------
def _box(cv, x0, y0, w, h, ramp, seed=0):
    r0, r1, r2, r3 = ramp
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            edge = x in (x0, x0 + w - 1) or y in (y0, y0 + h - 1)
            if edge:
                c = r0
            elif y == y0 + 1 or x == x0 + 1:
                c = r3
            elif x > x0 + w - 4 or y > y0 + h - 3:
                c = r1
            else:
                c = r2 if noise(x, y, seed) > 0.15 else r1
            cv.set(x, y, c)


def _cylinder(cv, cx, top, rx, h, ramp, bands=(), seed=0):
    r0, r1, r2, r3 = ramp
    for y in range(top, top + h):
        for x in range(cx - rx, cx + rx + 1):
            f = (x - cx) / rx
            c = r3 if f < -0.45 else (r2 if f < 0.35 else r1)
            if abs(f) > 0.92 or y == top + h - 1:
                c = r0
            if (y - top) in bands:
                c = r0 if (y - top) % 2 else r1
            cv.set(x, y, c)
    for x in range(cx - rx, cx + rx + 1):                  # elliptical top
        for dy in range(-2, 2):
            if ((x - cx) / rx) ** 2 + (dy / 2) ** 2 <= 1:
                cv.set(x, top + dy, r3 if dy < 0 else r2)
    for x in range(cx - rx + 1, cx + rx):
        cv.set(x, top - 2, r0)


def prop_crates(cv, x, y, ramp):
    _box(cv, x, y + 10, 14, 14, ramp, 1)
    _box(cv, x + 14, y + 13, 11, 11, ramp, 2)
    _box(cv, x + 4, y, 10, 10, ramp, 3)
    r0 = ramp[0]
    for k in range(1, 13):                                  # cross bracing
        cv.set(x + k, y + 10 + k, r0)


def prop_barrel(cv, x, y, ramp):
    _cylinder(cv, x + 7, y + 2, 7, 20, ramp, bands=(3, 4, 15, 16))


def prop_totem(cv, x, y, ramp):
    r0, r1, r2, r3 = ramp
    _box(cv, x, y, 14, 34, ramp, 4)
    for fy in (y + 3, y + 14, y + 25):                     # three carved faces
        for dx in (3, 4, 9, 10):
            cv.set(x + dx, fy + 2, r0); cv.set(x + dx, fy + 3, r0)
        for dx in range(3, 11):
            cv.set(x + dx, fy, r3)                         # brow
            cv.set(x + dx, fy + 7, r0 if dx in (3, 10) or (dx + fy) % 2 else r1)   # teeth
        cv.set(x + 6, fy + 4, r1); cv.set(x + 7, fy + 4, r1)                      # nose
    for dx in range(-3, 17):                                # wings at the top
        cv.set(x + dx, y + 1, r2 if dx % 4 else r0)
        cv.set(x + dx, y + 2, r0)


def prop_drums(cv, x, y, ramp):
    _cylinder(cv, x + 6, y + 6, 6, 16, ramp, bands=(5, 6))
    _cylinder(cv, x + 17, y + 10, 5, 12, ramp, bands=(4, 5))
    r0 = ramp[0]
    for k in range(0, 16, 3):                               # lacing
        cv.set(x + 2 + (k % 6), y + 7 + k // 2, r0)


def prop_snowman(cv, x, y, ramp):
    r0, r1, r2, r3 = ramp
    for cy, r in ((y + 24, 9), (y + 12, 6.5), (y + 3, 4.5)):
        for yy in range(int(cy - r), int(cy + r) + 1):
            for xx in range(int(x + 9 - r), int(x + 9 + r) + 1):
                d = math.hypot(xx - (x + 9), yy - cy)
                if d <= r:
                    k = ((xx - x - 9) + (yy - cy)) / r
                    c = r0 if d > r - 1 else (r1 if k > 0.7 else (r2 if k > 0.1 else r3))
                    cv.set(xx, yy, c)
    cv.set(x + 7, y + 2, r0); cv.set(x + 11, y + 2, r0)     # coal eyes
    cv.set(x + 9, y + 4, r1); cv.set(x + 10, y + 4, r1)      # nose
    for k in range(6):                                       # stick arms
        cv.set(x + 2 - k, y + 11 - k // 2, r0)
        cv.set(x + 16 + k, y + 11 - k // 2, r0)
    for yy in (y + 10, y + 13, y + 20, y + 25):
        cv.set(x + 9, yy, r0)                                # buttons
    for xx in range(x + 4, x + 15):                          # hat
        cv.set(xx, y - 2, r0)
    for yy in range(y - 7, y - 2):
        for xx in range(x + 6, x + 13):
            cv.set(xx, yy, r0 if xx in (x + 6, x + 12) else r1)


def prop_sled(cv, x, y, ramp):
    r0, r1, r2, r3 = ramp
    _box(cv, x, y + 8, 24, 5, ramp, 5)
    for dx in range(0, 26):
        cv.set(x + dx, y + 16, r0)                           # runner
    cv.set(x + 25, y + 15, r0); cv.set(x + 26, y + 14, r0); cv.set(x + 26, y + 13, r0)
    for dx in (3, 11, 19):
        for dy in range(13, 16):
            cv.set(x + dx, y + dy, r0)
    for k in range(9):                                       # rope
        cv.set(x + 26 + k // 2, y + 12 - k, r1)


def prop_pots(cv, x, y, ramp):
    r0, r1, r2, r3 = ramp
    for cx, cy, r in ((x + 8, y + 16, 8), (x + 20, y + 20, 5.5)):
        for yy in range(int(cy - r), int(cy + r) + 1):
            for xx in range(int(cx - r), int(cx + r) + 1):
                d = math.hypot((xx - cx) * 1.1, yy - cy)
                if d <= r:
                    k = ((xx - cx) + (yy - cy)) / r
                    c = r0 if d > r - 1 else (r1 if k > 0.5 else (r3 if k < -0.6 else r2))
                    if abs(yy - cy + 2) < 1:
                        c = r0                               # painted band
                    cv.set(xx, yy, c)
        for xx in range(int(cx - r / 2), int(cx + r / 2) + 1):          # neck
            cv.set(xx, int(cy - r) - 1, r0)
            cv.set(xx, int(cy - r), r2)


def prop_wheel(cv, x, y, ramp):
    r0, r1, r2, r3 = ramp
    cx, cy = x + 12, y + 12
    for a in range(0, 360, 2):
        for rr in (10, 11):
            cv.set(cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a)),
                   r0 if rr == 11 else (r3 if 120 < a < 240 else r2))
    for a in range(0, 360, 45):
        for rr in range(2, 10):
            cv.set(cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a)), r1)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            cv.set(cx + dx, cy + dy, r0 if abs(dx) == 2 or abs(dy) == 2 else r2)


def prop_rope(cv, x, y, ramp):
    r0, r1, r2, r3 = ramp
    for i, rr in enumerate((11, 9, 7, 5)):
        for a in range(0, 360, 3):
            px = x + 12 + rr * math.cos(math.radians(a))
            py = y + 16 + rr * 0.45 * math.sin(math.radians(a))
            cv.set(px, py, r3 if (a // 9 + i) % 3 == 0 else r2)
            cv.set(px, py + 1, r0)


def prop_trap(cv, x, y, ramp):
    r0, r1, r2, r3 = ramp
    _box(cv, x, y + 6, 22, 16, ramp, 6)
    for dx in range(3, 20, 4):                               # slats
        for dy in range(8, 20):
            cv.set(x + dx, y + 6 + dy - 6, r0)
    for dx in range(0, 22):                                  # rounded lid
        cv.set(x + dx, y + 5 - (2 if 4 < dx < 18 else 0), r3)


def prop_anvil(cv, x, y, ramp):
    r0, r1, r2, r3 = ramp
    for yy in range(y + 8, y + 13):                          # face and horn
        for xx in range(x - (yy - y - 8), x + 24):
            cv.set(xx, yy, r3 if yy == y + 8 else (r2 if yy < y + 11 else r1))
    for yy in range(y + 13, y + 19):
        for xx in range(x + 8, x + 18):
            cv.set(xx, yy, r1)
    for yy in range(y + 19, y + 24):
        for xx in range(x + 4, x + 22):
            cv.set(xx, yy, r2 if yy == y + 19 else r1)
    for xx in range(x - 4, x + 24):
        cv.set(xx, y + 7, r0)
        cv.set(xx, y + 24, r0)


def prop_brazier(cv, x, y, ramp):
    r0, r1, r2, r3 = ramp
    for xx in range(x, x + 20):                              # bowl
        for yy in range(y + 8, y + 14):
            if abs(xx - x - 9.5) < 10 - (yy - y - 8) * 0.8:
                cv.set(xx, yy, r1 if yy > y + 9 else r0)
    for k in range(0, 9):                                    # glowing coals
        cv.set(x + 4 + k * 1.5, y + 7 - (k % 2), r3)
        cv.set(x + 5 + k * 1.5, y + 8, r2)
    for dx in (4, 15):                                       # legs
        for yy in range(y + 14, y + 24):
            cv.set(x + dx + (yy - y - 14) // 4 * (1 if dx > 9 else -1), yy, r0)


def prop_containers(cv, x, y, ramp):
    _box(cv, x, y + 4, 22, 20, ramp, 7)
    _box(cv, x + 4, y - 8, 16, 12, ramp, 8)
    r0 = ramp[0]
    for dx in range(3, 21, 3):                               # ribs
        for dy in range(6, 22):
            cv.set(x + dx, y + dy, r0)


def prop_dish(cv, x, y, ramp):
    r0, r1, r2, r3 = ramp
    for a in range(200, 341, 2):                             # dish
        for rr in range(4, 12):
            px = x + 12 + rr * math.cos(math.radians(a))
            py = y + 10 + rr * 0.6 * math.sin(math.radians(a))
            cv.set(px, py, r3 if rr > 9 else (r2 if a < 270 else r1))
    for k in range(10):
        cv.set(x + 12, y + 2 + k * 0 + k, r0)               # feed arm
    for yy in range(y + 11, y + 26):
        cv.set(x + 11, yy, r0); cv.set(x + 12, yy, r1)      # mast
    for xx in range(x + 6, x + 19):
        cv.set(xx, y + 26, r0)
    cv.set(x + 12, y + 1, r3)                                # beacon


STAGE_PROPS = {
    "jungle": (prop_totem, prop_drums), "snow": (prop_snowman, prop_sled),
    "city": (prop_crates, prop_barrel), "desert": (prop_pots, prop_wheel),
    "beach": (prop_rope, prop_trap), "volcano": (prop_anvil, prop_brazier),
    "moon": (prop_containers, prop_dish),
}


def draw_props(cv, stage, ramp):
    left, right = STAGE_PROPS[stage]
    for fn, x, y in ((left, 3, 54), (right, 128, 60)):
        layer = Canvas(cv.w, cv.h, fill=None)
        fn(layer, x, y, ramp)
        mask = {(xx, yy) for yy in range(cv.h) for xx in range(cv.w)
                if layer.px[yy][xx] is not None}
        if not mask:
            continue
        bottom = max(yy for _, yy in mask)
        xs = [xx for xx, _ in mask]
        cx, half = (min(xs) + max(xs)) / 2, (max(xs) - min(xs)) / 2 + 3
        for yy in range(bottom - 1, bottom + 4):              # contact shadow
            for xx in range(int(cx - half), int(cx + half) + 1):
                if ((xx - cx) / half) ** 2 + ((yy - bottom - 1) / 3) ** 2 <= 1 and \
                        dither(xx, yy, 0.6):
                    cv.set(xx, yy, ramp[0])
        for xx, yy in mask:
            cv.set(xx, yy, layer.px[yy][xx])
        for xx, yy in mask:                                   # outline against the deck
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (xx + dx, yy + dy) not in mask:
                    cv.set(xx + dx, yy + dy, ramp[0])


# The far backboard covers exactly tiles 5..14 of tile row 5 (y 40..47). Those
# tiles are drawn in the rail palette and flagged to sit in front of sprites, so
# the opponent stands behind the board. Its colour 0 is see-through: the two
# shadow rows above the board use it, everything else uses colours 1-3.
BOARD_X0, BOARD_X1 = 40, 120
BOARD_ROW = 5
BOARD_TILES = [(tx, BOARD_ROW) for tx in range(BOARD_X0 // 8, BOARD_X1 // 8)]


def draw_board(cv, rail, style):
    r0, r1, r2, r3 = rail
    for y in range(40, 48):
        ry = y - 42
        for x in range(BOARD_X0, BOARD_X1):
            if ry < 0:
                c = r0                               # see-through shadow
            else:
                c = (r3, r2, r2, r1, r2, r1)[ry]
                if style in ("copper", "chrome") and ry in (2, 3) and x % 10 == 5:
                    c = r3 if ry == 2 else r1        # studs
                elif style == "bamboo" and x % 13 == 0:
                    c = r1                           # node rings
                elif style == "bamboo" and x % 13 == 1 and ry < 4:
                    c = r3
                elif style == "rope" and ry > 0 and (x + ry) % 4 == 0:
                    c = r1                           # twist
                elif style == "ice" and noise(x, y, 53) < 0.08:
                    c = r3
                elif style == "stone" and ry in (2, 4) and noise(x, y, 54) < 0.5:
                    c = r1
                elif style == "obsidian" and noise(x // 2, y, 55) < 0.08:
                    c = r3
            cv.set(x, y, c)


def draw_table(cv, rail=("r0", "r1", "r2", "r3"), style="copper", glint=True):
    r0, r1, r2, r3 = rail
    far_y = round(screen_y(0))
    near_y = cv.h
    draw_board(cv, rail, style)
    for y in range(far_y, near_y):
        z = z_at_y(y + 0.5)
        lx = screen_x(-TABLE_HALF, z)
        rx = screen_x(TABLE_HALF, z)
        rw = rail_width(z)
        for x in range(cv.w):
            px = x + 0.5
            if lx <= px <= rx:
                edge = min(px - lx, rx - px)
                c = "t1"
                if edge < 4 and dither(x, y, 1 - edge / 4):
                    c = "t0"
                sheen = abs(px - (CENTER_X + 10 * (1 - z / Z_NEAR))) / (rx - lx)
                if sheen < 0.06 and dither(x, y, 0.15 * (1 - sheen / 0.06)):
                    c = "t2"
                cv.set(x, y, c)
            elif lx - rw <= px < lx or rx < px <= rx + rw:
                d = (lx - px) if px < lx else (px - rx)     # 0 at the inner edge
                f = d / rw
                if f < 0.12:
                    c = r3 if f < 0.06 else r2
                elif f < 0.45:
                    c = r2 if dither(x, y, 0.5 - f) else r1
                elif f < 0.85:
                    c = r1 if noise(x, y, 14) > 0.12 else r0
                else:
                    c = r0
                if style == "rope" and 0.12 <= f < 0.85 and (x + y) % 5 == 0:
                    c = r0                                  # rope twist
                elif style == "ice" and noise(x, y, 51) < 0.06:
                    c = r3                                  # frost sparkle
                elif style == "stone" and (y + int(d * 0.7)) % 5 == 0 and f > 0.1:
                    c = r0 if f > 0.5 else r1               # strata
                elif style == "obsidian" and f > 0.15 and noise(x // 2, y // 3, 52) < 0.07:
                    c = r3                                  # ember cracks
                cv.set(x, y, c)
    for zs in range(12, Z_NEAR, 24 if style != "bamboo" else 40):
        y = round(screen_y(zs))
        rw = rail_width(zs)
        for side in (-1, 1):
            if style in ("ice", "stone", "obsidian"):
                continue
            if style == "bamboo":                 # a dark node ring across the rail
                inner = screen_x(side * TABLE_HALF, zs)
                for k in range(rw):
                    cv.set(round(inner + side * (k + 0.5)), y, r0)
                    cv.set(round(inner + side * (k + 0.5)), y - 1, r3)
                continue
            cx = screen_x(side * TABLE_HALF, zs) + side * rw * 0.55
            r = max(1, round(rw / 9))
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r:
                        cv.set(round(cx) + dx, y + dy, r3 if dx + dy < 0 else r0)
    for zl in (48, 96, 144):
        y = round(screen_y(zl))
        for x in range(round(screen_x(-TABLE_HALF, zl)) + 1, round(screen_x(TABLE_HALF, zl))):
            if cv.get(x, y) in ("t1", "t0", "t2"):
                cv.set(x, y, "t2")
    for xl in (-24, 0, 24):
        for y in range(far_y, near_y):
            z = z_at_y(y + 0.5)
            cv.set(round(screen_x(xl, z) - 0.5), y, "t2")
    cz, cy = 96, round(screen_y(96))
    rx_ = 12 * xscale64(cz) / 64
    for a in range(0, 360, 3):
        x = CENTER_X + rx_ * math.cos(math.radians(a))
        y = cy + rx_ * 0.35 * math.sin(math.radians(a))
        cv.set(round(x), round(y), "t2")
    if glint:   # sky reflection near the far end
        for y in range(far_y + 3, far_y + 14):
            for x in range(CENTER_X + 6, CENTER_X + 22):
                d = ((x - (CENTER_X + 14)) / 7) ** 2 + ((y - (far_y + 8)) / 4) ** 2
                if d < 1 and dither(x, y, 0.7 * (1 - d)):
                    cv.set(x, y, "t3")


# ---------------------------------------------------------------------------
# stage 2: city rooftop at night (Rusty)
# ---------------------------------------------------------------------------
def scene_city():
    cv = Canvas()
    draw_sky(cv, 8, 40)
    draw_skyline(cv, 40)
    draw_string_lights(cv, 27, 34)
    draw_parapet(cv, 38, 48)
    draw_deck(cv, 48, cv.h)
    draw_props(cv, "city", WOOD_CITY)
    draw_table(cv)
    cv.rect(0, 0, cv.w, 8, "s0")               # HUD row
    return cv


scene_game = scene_city


# ---------------------------------------------------------------------------
# stage 1: jungle canopy treehouse in daylight (Tomo)
# ---------------------------------------------------------------------------
def leaf_clump(cv, cx, cy, rx, ry, seed):
    """A mass of leaves: overlapping blobs, lit from the top left, dark outline."""
    blobs = []
    for i in range(int(rx * ry / 10)):
        bx = cx + (noise(i, 1, seed, 991) - 0.5) * 2 * rx
        by = cy + (noise(i, 2, seed, 991) - 0.5) * 2 * ry
        r = 3 + noise(i, 3, seed, 991) * 4
        blobs.append((bx, by, r))
    blobs.sort(key=lambda b: b[1])
    for bx, by, r in blobs:
        for y in range(int(by - r - 1), int(by + r + 2)):
            for x in range(int(bx - r - 1), int(bx + r + 2)):
                d = math.hypot(x - bx, (y - by) * 1.3)
                if d <= r:
                    lit = (x - bx) + (y - by) < -r * 0.4
                    c = "jl2" if lit else ("jl1" if d < r - 1.2 else "jl0")
                    if c == "jl1" and noise(x, y, seed + 7) < 0.1:
                        c = "jl2"
                    cv.set(x, y, c)


def vine(cv, x, y0, length, seed):
    for k in range(length):
        xx = x + round(math.sin((k + seed) / 3.0) * 1.2)
        cv.set(xx, y0 + k, "jl1")
        if k % 5 == 2:
            cv.set(xx + 1, y0 + k, "jl2")
            cv.set(xx - 1, y0 + k + 1, "jl1")


def tree_trunk(cv, x0, x1, y0, y1):
    for y in range(y0, y1):
        for x in range(x0, x1):
            f = (x - x0) / (x1 - x0)
            c = "bk2" if f < 0.25 else ("bk1" if f < 0.7 else "bk0")
            if noise(x // 2, y, 21) < 0.18:
                c = "bk0"                         # bark grooves
            elif noise(x, y // 3, 22) < 0.06:
                c = "bk2"
            cv.set(x, y, c)


def scene_jungle():
    cv = Canvas(fill="jsky")
    # sky with a soft sun and puffy clouds
    for y in range(8, 40):
        for x in range(cv.w):
            cv.set(x, y, "jsky")
    for y in range(8, 26):
        for x in range(54, 76):
            d = math.hypot(x - 64, y - 15)
            if d < 6:
                cv.set(x, y, "cream")
            elif d < 9 and dither(x, y, 0.5 * (9 - d) / 3):
                cv.set(x, y, "cream")
    for cx, cy, w in ((100, 14, 22), (128, 20, 16), (36, 22, 14)):
        for y in range(cy - 5, cy + 4):
            for x in range(cx - w // 2, cx + w // 2):
                d = ((x - cx) / (w / 2)) ** 2 + ((y - cy) / 4.5) ** 2
                if d < 1 and (y < cy + 2 or dither(x, y, 0.5)):
                    cv.set(x, y, "cream")
    # distant canopy: rolling treetops
    for x in range(cv.w):
        top = 27 + 4 * math.sin(x / 7.0) + 2 * math.sin(x / 3.1 + 1)
        for y in range(int(top), 40):
            cv.set(x, y, "jf1" if y > top + 1 or dither(x, y, 0.6) else "jsky")
        if noise(x, 0, 31, 997) < 0.15:
            cv.set(x, int(top) + 3, "jl0")
    # big trees framing the scene, with leaves and vines
    tree_trunk(cv, 0, 16, 8, 48)
    tree_trunk(cv, 144, 160, 8, 48)
    leaf_clump(cv, 14, 12, 22, 9, 3)
    leaf_clump(cv, 146, 11, 24, 9, 5)
    leaf_clump(cv, 80, 8, 30, 4, 9)
    for x, l, sd in ((28, 16, 1), (34, 10, 4), (124, 18, 2), (131, 11, 6), (58, 9, 3), (99, 12, 8)):
        vine(cv, x, 14, l, sd)
    # log fence behind the table
    for y in range(40, 48):
        for x in range(16, 144):
            ry = y - 40
            c = ("bk2", "bk1", "bk1", "bk0", "bk2", "bk1", "bk1", "bk0")[ry]
            if x % 26 in (0, 1):
                c = "bk0" if ry % 4 == 3 else "bk1"   # log ends
            elif noise(x, y, 23) < 0.08:
                c = "bk0"
            cv.set(x, y, c)
    draw_deck(cv, 48, cv.h, WOOD_JUNGLE, plank=7)
    draw_props(cv, "jungle", WOOD_JUNGLE)
    draw_table(cv, ("bb0", "bb1", "bb2", "bb3"), "bamboo")
    cv.rect(0, 0, cv.w, 8, "jl0")
    return cv


# ---------------------------------------------------------------------------
# stage 3: sunset pier by the sea (Okta)
# ---------------------------------------------------------------------------
def palm(cv, x, base, height, lean, seed):
    top_x = x + lean
    for k in range(height):
        t = k / height
        xx = round(x + lean * t * t)
        for w in range(2 if t < 0.6 else 1 + (k % 2)):
            cv.set(xx + w, base - k, "sk0")
    ty = base - height
    for ang, length in ((-160, 13), (-120, 10), (-60, 11), (-20, 14), (-90, 7), (200, 9)):
        a = math.radians(ang)
        for k in range(length):
            droop = (k / length) ** 2 * 5
            px = top_x + math.cos(a) * k
            py = ty + math.sin(a) * k * 0.6 + droop
            cv.set(round(px), round(py), "sk0")
            if k % 2 == 0 and k > 2:
                cv.set(round(px), round(py) + 1, "sk0")


def scene_beach():
    cv = Canvas(fill="sk0")
    horizon = 24
    # sunset gradient: deep violet at the top through pink to orange
    for y in range(8, horizon):
        t = (y - 8) / (horizon - 8)
        for x in range(cv.w):
            if t < 0.45:
                c = "sk1" if dither(x, y, t / 0.45) else "sk0"
            else:
                c = "sk2" if dither(x, y, (t - 0.45) / 0.55) else "sk1"
            cv.set(x, y, c)
    for cx, cy, w in ((40, 12, 34), (116, 10, 26), (86, 16, 20)):   # thin cloud streaks
        for x in range(cx - w // 2, cx + w // 2):
            cv.set(x, cy, "sk0" if (x // 3) % 3 else "sk1")
            if abs(x - cx) < w // 3:
                cv.set(x, cy + 1, "sk1")
    # the sun, half under the horizon
    sx, sr = 108, 9
    for y in range(horizon - sr, horizon):
        for x in range(sx - sr, sx + sr + 1):
            d = math.hypot(x - sx, y - horizon)
            if d <= sr:
                cv.set(x, y, "cream" if d < sr - 1.5 else "sk2")
    # the sea, with the sun's reflection and glints
    for y in range(horizon, 40):
        t = (y - horizon) / (40 - horizon)
        for x in range(cv.w):
            c = "sea1" if t < 0.2 or dither(x, y, 0.35 * (1 - t)) else "sea0"
            if (x + 3 * y) % 11 == 0 and noise(x, y, 41) < 0.5:
                c = "sea2"                              # wave caps
            col = abs(x - sx)
            if col < sr - t * 4 and (y % 2 == 0) and noise(x, y, 42) < 0.8 - t * 0.5:
                c = "cream" if col < 3 and t < 0.5 else "sk2"
            cv.set(x, y, c)
    # an island on the horizon and two palms on the shore
    for x in range(14, 50):
        h = 4 * math.sin((x - 14) / 36 * math.pi)
        for y in range(round(horizon - h), horizon + 1):
            cv.set(x, y, "sk0")
    palm(cv, 6, 40, 26, 8, 1)
    palm(cv, 152, 40, 22, -7, 2)
    for gx, gy in ((70, 13), (78, 11), (132, 15)):            # gulls
        cv.set(gx - 1, gy, "sk0"); cv.set(gx, gy + 1, "sk0"); cv.set(gx + 1, gy, "sk0")
        cv.set(gx - 2, gy - 1, "sk0"); cv.set(gx + 2, gy - 1, "sk0")
    # pier railing: planks with posts
    for y in range(40, 48):
        for x in range(cv.w):
            ry = y - 40
            post = x % 20 in (0, 1, 2)
            if post:
                c = "pw3" if x % 20 == 0 else ("pw1" if x % 20 == 2 else "pw2")
            else:
                c = ("pw3", "pw2", "pw2", "pw0", "pw2", "pw1", "pw1", "pw0")[ry]
                if noise(x // 2, y, 43) < 0.1:
                    c = "pw1"
            cv.set(x, y, c)
    draw_deck(cv, 48, cv.h, WOOD_PIER, plank=5)
    draw_props(cv, "beach", WOOD_PIER)
    draw_table(cv, ("rp0", "rp1", "rp2", "rp3"), "rope")
    cv.rect(0, 0, cv.w, 8, "sk0")
    return cv



# ---------------------------------------------------------------------------
# stage 2: snow lodge under the aurora (Pip)
# ---------------------------------------------------------------------------
def pine(cv, x, base, h):
    for k in range(h):
        half = (k * 0.45) if k < h else 0
        y = base - h + k
        for dx in range(-round(half), round(half) + 1):
            snowy = (k % 4 == 0 and abs(dx) > half - 2) or (k < 2)
            cv.set(x + dx, y, "snow" if snowy else ("pine1" if dx < 0 else "pine0"))
    cv.set(x, base, "pine0")


def scene_snow():
    cv = Canvas(fill="n0")
    for y in range(8, 40):
        t = (y - 8) / 32
        for x in range(cv.w):
            cv.set(x, y, "n1" if dither(x, y, t * 0.9) else "n0")
    # aurora: two wavy ribbons, brighter at their crests
    for band, (yc, amp, ph) in enumerate(((11, 2, 0.0), (16, 2, 2.0))):
        for x in range(cv.w):
            yy = yc + amp * math.sin(x / 13 + ph) + 1.5 * math.sin(x / 5 + ph)
            for k in range(5):
                if int(yy) + k < 23 and dither(x, int(yy) + k, 0.8 - k * 0.16):
                    cv.set(x, int(yy) + k, "aur")
    for i in range(30):
        x, y = int(noise(i, 1, 61, 997) * cv.w), 8 + int(noise(i, 2, 61, 997) * 14)
        cv.set(x, y, "snow")
    # mountains with snowy peaks and blue shadow sides
    for x in range(cv.w):
        top = 27 + 3 * math.sin(x / 9) - 2 * abs(math.sin(x / 23 + 0.6))
        peak_x = (x / 23 + 0.6) % math.pi
        for y in range(int(top), 40):
            depth = y - top
            c = "snow" if depth < 2 else ("mt1" if peak_x < math.pi / 2 else "mt0")
            if depth > 6 and dither(x, y, 0.3):
                c = "mt0"
            cv.set(x, y, c)
    for x, h in ((8, 18), (22, 13), (136, 16), (150, 20), (124, 10), (34, 9)):
        pine(cv, x, 39, h)
    # snow bank behind the table
    for y in range(40, 48):
        for x in range(cv.w):
            ry = y - 40
            c = "snow" if ry < 2 + 2 * math.sin(x / 7) else ("mt1" if ry < 6 else "mt0")
            if noise(x, y, 62) < 0.06:
                c = "ice1"
            cv.set(x, y, c)
    draw_deck(cv, 48, cv.h, ("lw0", "lw1", "lw2", "lw3"), plank=7)
    for y in range(48, cv.h):                         # snow dusting along the planks
        for x in range(cv.w):
            if (y - 48) % 7 in (0, 1) and noise(x // 3, y, 65) < 0.45:
                cv.set(x, y, "lw3")
    draw_props(cv, "snow", ("lw0", "lw1", "lw2", "lw3"))
    draw_table(cv, ("ice0", "ice1", "ice2", "ice3"), "ice")
    cv.rect(0, 0, cv.w, 8, "n0")
    return cv


# ---------------------------------------------------------------------------
# stage 4: desert canyon at noon (Zuri)
# ---------------------------------------------------------------------------
def mesa(cv, x0, x1, top, base):
    for y in range(top, base):
        for x in range(x0 - (y - top) // 3, x1 + (y - top) // 3):
            ry = y - top
            c = "m2" if ry < 2 else ("m1" if (x - x0) < (x1 - x0) * 0.6 else "m0")
            if ry % 5 == 3 and noise(x, y, 63) < 0.7:
                c = "m0"                                  # rock layers
            cv.set(x, y, c)


def cactus(cv, x, base, h):
    for y in range(base - h, base):
        for dx in (-1, 0, 1):
            cv.set(x + dx, y, "c2" if dx < 0 else ("c1" if dx == 0 else "c0"))
    for side, ay in ((-1, base - h + 5), (1, base - h + 8)):
        for k in range(4):
            cv.set(x + side * (2 + k // 2), ay, "c1")
        for y in range(ay - 4, ay + 1):
            cv.set(x + side * 4, y, "c1")
            cv.set(x + side * 4 + side, y, "c0")


def scene_desert():
    cv = Canvas(fill="dsky0")
    for y in range(8, 40):
        t = (y - 8) / 32
        for x in range(cv.w):
            cv.set(x, y, "dsky1" if dither(x, y, t * t) else "dsky0")
    for y in range(8, 24):
        for x in range(116, 140):
            d = math.hypot(x - 128, y - 15)
            if d < 5:
                cv.set(x, y, "cream")
            elif d < 8 and dither(x, y, (8 - d) / 4):
                cv.set(x, y, "cream")
    mesa(cv, 10, 46, 20, 40)
    mesa(cv, 70, 92, 26, 40)
    mesa(cv, 118, 150, 18, 40)
    for x in range(cv.w):                                 # sand dunes at the foot
        top = 36 + 2 * math.sin(x / 11)
        for y in range(int(top), 40):
            cv.set(x, y, "m2" if y < top + 1 else "m1")
    cactus(cv, 58, 40, 12)
    cactus(cv, 104, 40, 9)
    # adobe wall with wooden beam ends
    for y in range(40, 48):
        for x in range(cv.w):
            ry = y - 40
            c = "a3" if ry == 0 else ("a2" if ry < 5 else "a1")
            if noise(x, y, 64) < 0.1:
                c = "a1"
            if x % 32 in (6, 7, 8) and ry in (2, 3):
                c = "a0"                                  # beam ends
            cv.set(x, y, c)
    draw_deck(cv, 48, cv.h, ("bw0", "bw1", "bw2", "bw3"), plank=6)
    draw_props(cv, "desert", ("bw0", "bw1", "bw2", "bw3"))
    draw_table(cv, ("ss0", "ss1", "ss2", "ss3"), "stone")
    cv.rect(0, 0, cv.w, 8, "dhud")
    return cv


# ---------------------------------------------------------------------------
# stage 6: volcano forge (Blaze)
# ---------------------------------------------------------------------------
def scene_volcano():
    cv = Canvas(fill="v0")
    # sky: a dark red night, glowing low down
    for y in range(8, 40):
        t = (y - 8) / 32
        for x in range(cv.w):
            cv.set(x, y, "v1" if dither(x, y, t * 1.1) else "v0")
    # smoke: billowing puffs lit from below by the lava
    puffs = []
    for i in range(26):
        cx = 52 + noise(i, 1, 71, 997) * 70 + i * 0.6
        cy = 10 + noise(i, 2, 71, 997) * 12
        r = 3 + noise(i, 3, 71, 997) * 4.5
        puffs.append((cx, cy, r))
    for cx, cy, r in sorted(puffs, key=lambda p: p[1]):
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                d = math.hypot(x - cx, (y - cy) * 1.15)
                if d <= r:
                    lit = (y - cy) / r                   # lower half catches the glow
                    c = "v2" if lit > 0.25 and dither(x, y, lit) else "v1"
                    if d > r - 1 and dither(x, y, 0.5):
                        c = "v0"
                    cv.set(x, y, c)
    for i in range(22):                                  # embers drifting up
        x = int(noise(i, 5, 72, 997) * cv.w)
        y = 9 + int(noise(i, 6, 72, 997) * 24)
        cv.set(x, y, "lavaY" if i % 3 == 0 else "lavaO")
    # distant jagged ridges with a rim of light
    for x in range(cv.w):
        top = 30 + 3 * math.sin(x / 9.0) + 2 * noise(x // 3, 0, 73, 997) * 2
        for y in range(int(top), 40):
            cv.set(x, y, "rock0")
        cv.set(x, int(top), "rock1")
    # the volcano: concave slopes, ragged edges, gullies, lit on the left
    for y in range(12, 40):
        t = (y - 12) / 28
        half = 8 + 62 * t ** 1.7
        rough = 2.5 * (noise(y, 1, 74, 997) - 0.5)
        x0, x1 = int(80 - half + rough), int(80 + half - rough)
        for x in range(x0, x1):
            f = (x - x0) / max(1, x1 - x0)
            c = "rock1" if f < 0.35 else "rock0"
            if f < 0.35 and dither(x, y, 0.35):
                c = "rock0"
            gully = (x * 3 + y * 5) % 17 == 0 or (x * 5 - y * 3) % 19 == 0
            if gully and y > 15:
                c = "rock0" if c == "rock1" else "rock1"
            cv.set(x, y, c)
    for y in range(12, 15):                              # glowing crater
        for x in range(73, 88):
            d = abs(x - 80.5) / (7.5 - (y - 12))
            if d < 1:
                cv.set(x, y, "lavaY" if y == 12 and d < 0.5 else "lavaO")
    for k in range(14):                                  # plume above the crater
        y = 11 - k * 0.5
        for x in range(76 - k // 3, 85 + k // 3):
            if dither(x, int(y), 0.5 - k * 0.03) and noise(x, k, 75) < 0.6:
                cv.set(x, int(y), "lavaO" if k < 4 else "v2")
    # lava flows: start along the crater rim and wander down the slopes
    for i, (x0, drift) in enumerate(((75, -1.0), (79, -0.35), (83, 0.45), (86, 1.05))):
        x = float(x0)
        for y in range(14, 34):
            x += drift * (0.6 + 0.8 * noise(i, y, 76, 997)) + 1.1 * math.sin(y / 2.5 + i * 2)  * 0.35
            xi = round(x)
            if dither(xi - 2, y, 0.35):
                cv.set(xi - 2, y, "lavaO")              # glow on the rock
            if dither(xi + 2, y, 0.35):
                cv.set(xi + 2, y, "lavaO")
            cv.set(xi, y, "lavaY" if (y + i) % 5 else "lavaO")
            cv.set(xi + (1 if drift > 0 else -1), y, "lavaO")
            if y > 26 and i % 2 == 0:                    # flows thin out lower down
                break
    # rocky ground at the foot, with a winding lava channel and pools
    for y in range(33, 40):
        for x in range(cv.w):
            c = "rock0" if noise(x // 2, y, 77) > 0.2 else "rock1"
            if y == 33 and noise(x, 0, 81, 997) < 0.5:
                continue                                 # broken skyline of rocks
            cv.set(x, y, c)
    for x in range(cv.w):
        yc = 36.5 + 1.6 * math.sin(x / 11.0) + 0.8 * math.sin(x / 4.3)
        for y in range(int(yc) - 1, int(yc) + 2):
            if 33 < y < 40:
                core = y == int(yc)
                cv.set(x, y, "lavaY" if core and noise(x, y, 82) < 0.6 else "lavaO")
        if noise(x, 1, 83, 997) < 0.1 and 34 < int(yc) - 2:
            cv.set(x, int(yc) - 2, "lavaO")              # glow on the banks
    for px, py in ((22, 35), (128, 36), (148, 34)):     # small pools
        for x in range(px - 3, px + 4):
            for y in range(py - 1, py + 2):
                if abs(x - px) + abs(y - py) * 2 < 4:
                    cv.set(x, y, "lavaY" if abs(x - px) < 2 and y == py else "lavaO")
    # basalt columns behind the table, glowing in the seams
    for y in range(40, 48):
        for x in range(cv.w):
            ry = y - 40
            col = x // 7
            top = 41 + (col * 3) % 3
            c = "rock1" if x % 7 < 2 else ("rock2" if x % 7 < 4 else "rock1")
            if x % 7 == 6:
                c = "lavaO" if noise(x, y, 79) < 0.35 else "rock0"     # glowing seam
            if y == top:
                c = "rock2"                                            # column caps
            elif y < top:
                c = "lavaO" if dither(x, y, 0.3) else "rock0"
            if ry == 7:
                c = "rock0"
            cv.set(x, y, c)
    draw_deck(cv, 48, cv.h, ("st0", "st1", "st2", "st3"), plank=8)
    for y in range(48, cv.h):                            # floor tiles: cracked stone
        for x in range(cv.w):
            if (x + (y // 8) * 4) % 16 == 0 or noise(x // 2, y // 2, 80) < 0.03:
                cv.set(x, y, "st0")
    draw_props(cv, "volcano", ("st0", "st1", "st2", "st3"))
    draw_table(cv, ("ob0", "ob1", "ob2", "ob3"), "obsidian")
    cv.rect(0, 0, cv.w, 8, "v0")
    return cv


# ---------------------------------------------------------------------------
# stage 7: moon base (Nova)
# ---------------------------------------------------------------------------
def scene_moon():
    cv = Canvas(fill="sp0")
    for y in range(8, 40):
        for x in range(cv.w):
            cv.set(x, y, "sp1" if dither(x, y, (y - 8) / 64) else "sp0")
    for i in range(50):
        x, y = int(noise(i, 1, 81, 997) * cv.w), 8 + int(noise(i, 2, 81, 997) * 26)
        cv.set(x, y, "white" if i % 3 == 0 else "spd")
    # the Earth, lit from the left
    ex, ey, er = 34, 20, 10
    for y in range(ey - er, ey + er + 1):
        for x in range(ex - er, ex + er + 1):
            d = math.hypot(x - ex, y - ey)
            if d <= er:
                land = noise(x // 2, y // 2, 82) < 0.4
                c = "eg" if land else "eb"
                if noise(x // 3, y, 83) < 0.12:
                    c = "white"                           # clouds
                if (x - ex) > er * 0.35 and dither(x, y, ((x - ex) / er - 0.35) * 1.6):
                    c = "sp0"                             # night side
                cv.set(x, y, c)
    # moon ground: grey with craters
    for x in range(cv.w):
        top = 33 + 2 * math.sin(x / 17) + math.sin(x / 5)
        for y in range(int(top), 40):
            c = "mg3" if y < top + 1 else ("mg2" if noise(x, y, 84) > 0.2 else "mg1")
            cv.set(x, y, c)
    for cx, cy, r in ((110, 37, 4), (140, 36, 3), (66, 38, 3)):
        for x in range(cx - r, cx + r + 1):
            cv.set(x, cy, "mg0" if abs(x - cx) < r else "mg1")
            cv.set(x, cy - 1, "mg3" if abs(x - cx) < r - 1 else "mg2")
    # base wall: panels with lights
    for y in range(40, 48):
        for x in range(cv.w):
            ry = y - 40
            c = "pn2" if ry == 0 else ("pn1" if ry < 7 else "pn0")
            if x % 20 in (0, 19):
                c = "pn0"
            if ry == 3 and x % 20 == 10:
                c = "pnl"                                 # status lights
            cv.set(x, y, c)
    draw_deck(cv, 48, cv.h, ("fl0", "fl1", "fl2", "fl3"), plank=8)
    draw_props(cv, "moon", ("fl0", "fl1", "fl2", "fl3"))
    draw_table(cv, ("ch0", "ch1", "ch2", "ch3"), "chrome")
    cv.rect(0, 0, cv.w, 8, "sp0")
    return cv


def scene_howto():
    cv = scene_city()
    cv.rect(0, 0, cv.w, 40, "s0")                      # text panel (rows 0-4)
    for x in range(cv.w):
        cv.set(x, 39, "s2")
    # arrows around the paddle (paddle drawn as a sprite at z 176, x -10)
    py = round(screen_y(176))
    px = round(screen_x(-10, 176))

    def arrow(x0, y0, dx, dy, n=9):
        for k in range(n):
            cv.set(x0 + dx * k, y0 + dy * k, "t3")
        tx, ty = x0 + dx * (n - 1), y0 + dy * (n - 1)
        for k in (1, 2):                               # arrow head
            cv.set(tx - dx * k + dy * k, ty - dy * k + dx * k, "t3")
            cv.set(tx - dx * k - dy * k, ty - dy * k - dx * k, "t3")
    arrow(px - 16, py, -1, 0)
    arrow(px + 16, py, 1, 0)
    arrow(px, py - 6, 0, -1, 8)
    # a bank shot: from the puck, off the right rail, toward the far end
    path = [(8, 150), (45, 96), (-12, 14)]
    for (x0, z0), (x1, z1) in zip(path, path[1:]):
        for k in range(0, 40):
            t = k / 40
            x, z = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t
            if k % 3 == 0:
                cv.set(round(screen_x(x, z)), round(screen_y(z)), "t3")
    bx, by = round(screen_x(45, 96)), round(screen_y(96))
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):   # bounce sparkle
        cv.set(bx - 4 + dx * 2, by + dy * 2, "t3")
    return cv


# ---------------------------------------------------------------------------
# glossary backdrops: the Hall of Rivals (opponent profiles) and a chalkboard
# (puck terms). Rows 7-17 become the text panel at run time.
# ---------------------------------------------------------------------------
HALL_PALETTES = [
    ["h0", "h1", "h2", "spot2"],            # 0 text panel, dark wall
    ["h1", "h2", "h3", "spot"],             # 1 panelled wall in the spotlight
    ["h0", "tg0", "tg1", "tg2"],            # 2 trophies
    ["h0", "h1", "h3", "tg1"],              # 3 shelves
    ["cp0", "cp1", "cp2", "mb1"],           # 4 carpet
    ["h0", "spot", "spot2", "h2"],          # 5 spotlight glow
    ["cp0", "cp2", "mb0", "mb1"],           # 6 carpet meets podium
    ["mb0", "mb1", "mb2", "mb3"],           # 7 marble podium (in front of the opponent)
]
CHALK_PALETTES = [
    ["cb0", "cb1", "chd", "chk"],           # 0 the board and its chalk (text palette)
    ["w0", "w1", "w2", "w3"],               # 1 wooden frame
    ["cb0", "w0", "w2", "chk"],             # 2 frame meets board
] + [["cb0", "cb1", "chd", "chk"]] * 5


def trophy(cv, x, base, h, kind):
    """A little cup or star on a plinth, shaded gold."""
    for y in range(base - 3, base):
        for xx in range(x - 3, x + 4):
            cv.set(xx, y, "tg0" if y == base - 1 else "tg1")
    if kind == "cup":
        for y in range(base - h, base - 3):
            w = 1 if y > base - h + 5 else 4 - (base - h + 5 - y) // 3
            for xx in range(x - w, x + w + 1):
                cv.set(xx, y, "tg2" if xx < x else ("tg1" if xx < x + w else "tg0"))
        for yy in range(base - h + 1, base - h + 4):
            cv.set(x - 5, yy, "tg1"); cv.set(x + 5, yy, "tg0")      # handles
    else:
        cy = base - h + 4
        for a in range(0, 360, 72):
            for k in range(5):
                cv.set(x + k * math.cos(math.radians(a - 90)), cy + k * math.sin(math.radians(a - 90)),
                       "tg2" if a < 144 else "tg1")
        for y in range(cy + 3, base - 3):
            cv.set(x, y, "tg1")


def scene_hall():
    cv = Canvas(fill="h1")
    # panelled wall: frames with bevels
    for y in range(8, 40):
        for x in range(cv.w):
            px, py = x % 32, (y - 8) % 16
            c = "h1"
            if px in (0, 31) or py in (0, 15):
                c = "h0"
            elif px == 1 or py == 1:
                c = "h3"
            elif px in (29, 30) or py == 14:
                c = "h0" if dither(x, y, 0.5) else "h1"
            elif noise(x // 2, y, 91) < 0.08:
                c = "h2"                                  # wood grain
            cv.set(x, y, c)
    # trophy shelves on both sides
    for sx in (6, 118):
        for x in range(sx, sx + 36):
            cv.set(x, 30, "h3"); cv.set(x, 31, "h1"); cv.set(x, 32, "h0")
        for i, kind in enumerate(("cup", "star", "cup")):
            trophy(cv, sx + 6 + i * 12, 30, 12 - (i % 2) * 2, kind)
    # spotlight from above onto the podium
    for y in range(8, 40):
        t = (y - 8) / 32
        half = 8 + 18 * t
        for x in range(int(80 - half), int(80 + half) + 1):
            d = abs(x - 80) / half
            if d < 0.92 and dither(x, y, 0.75 - d * 0.6):
                cv.set(x, y, "spot2" if d < 0.3 and dither(x, y, 0.5) else "spot")
    # carpet floor with a woven border
    for y in range(40, 56):
        for x in range(cv.w):
            c = "cp1"
            if (x + y) % 6 == 0:
                c = "cp2"
            if y in (41, 54):
                c = "cp2"
            if y in (40, 55):
                c = "cp0"
            cv.set(x, y, c)
    # marble podium: row 5 is in front of the opponent (board tiles)
    for y in range(40, 48):
        for x in range(BOARD_X0, BOARD_X1):
            ry = y - 40
            if ry < 2:
                c = "mb0"                                 # see-through shadow
            else:
                c = ("mb3", "mb2", "mb2", "mb1", "mb2", "mb1")[ry - 2]
                if noise(x // 2, y, 92) < 0.12:
                    c = "mb1"                             # veins
                if x in (BOARD_X0, BOARD_X1 - 1):
                    c = "mb1"
            cv.set(x, y, c)
    for y in range(48, 56):                               # podium front below
        for x in range(BOARD_X0 + 2, BOARD_X1 - 2):
            c = "mb2" if (x - BOARD_X0) % 16 < 14 else "mb1"
            if y == 48:
                c = "mb1"
            cv.set(x, y, c)
    for y in range(56, cv.h):
        for x in range(cv.w):
            cv.set(x, y, "h0")
    cv.rect(0, 0, cv.w, 8, "h0")
    return cv


def scene_chalk(glyph_rows):
    cv = Canvas(fill="cb0")
    # wooden frame along the top
    for y in range(0, 4):
        for x in range(cv.w):
            cv.set(x, y, ("w1", "w3", "w2", "w0")[y])
    # board with smudges
    for y in range(4, cv.h):
        for x in range(cv.w):
            cv.set(x, y, "cb1" if noise(x // 3, y // 2, 93) < 0.18 else "cb0")
    # chalk diagram: a little table in perspective with a bank shot
    def chalk_line(x0, y0, x1, y1, c="chk", dash=0):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for k in range(n + 1):
            if dash and (k // dash) % 2:
                continue
            t = k / n
            cv.set(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), c)
    chalk_line(62, 10, 98, 10)                            # far end
    chalk_line(62, 10, 36, 50)                            # rails
    chalk_line(98, 10, 124, 50)
    chalk_line(56, 30, 104, 30, "chd", 2)                 # centre line
    chalk_line(70, 44, 90, 44)                            # paddle
    chalk_line(70, 45, 90, 45)
    for a in range(0, 360, 30):                           # puck
        cv.set(round(84 + 2.5 * math.cos(math.radians(a))), round(38 + 1.6 * math.sin(math.radians(a))), "chk")
    chalk_line(84, 36, 110, 28, "chd", 2)                 # bank shot
    chalk_line(110, 28, 72, 12, "chd", 2)
    chalk_line(72, 12, 75, 12); chalk_line(72, 12, 74, 15)  # arrow head
    # labels, written in chalk
    def label(text, x, y):
        for i, ch in enumerate(text):
            for ry, row in enumerate(glyph_rows(ch)):
                for rx, bit in enumerate(row):
                    if bit:
                        cv.set(x + i * 6 + rx, y + ry, "chd")
    label("RAIL", 118, 20)
    label("PUCK", 8, 34)
    chalk_line(32, 37, 80, 38, "chd", 1)
    label("PADDLE", 98, 42)
    cv.rect(0, 0, cv.w, 0, "w0")
    return cv


STAGES = [("Jungle", scene_jungle, JUNGLE_PALETTES),
          ("Snow", scene_snow, SNOW_PALETTES),
          ("City", scene_city, CITY_PALETTES),
          ("Desert", scene_desert, DESERT_PALETTES),
          ("Beach", scene_beach, BEACH_PALETTES),
          ("Volcano", scene_volcano, VOLCANO_PALETTES),
          ("Moon", scene_moon, MOON_PALETTES)]


def logo_mask(glyph_rows, text, scale, shear):
    """Pixels of a word in the 5x7 font at `scale`, slanted (top leans right)."""
    h = 7 * scale
    mask = set()
    for i, ch in enumerate(text):
        for ry, row in enumerate(glyph_rows(ch)):
            for rx, bit in enumerate(row):
                if not bit:
                    continue
                for sy in range(scale):
                    for sx in range(scale):
                        y = ry * scale + sy
                        # slant in whole font-pixel steps so strokes stay solid
                        x = i * 6 * scale + rx * scale + sx + round((6 - ry) * shear * scale)
                        mask.add((x, y))
    return mask


def draw_logo_word(cv, mask, ox, oy):
    """Drop shadow, dark outline, then a cream-gold-orange fill with a shine."""
    h = max(y for _, y in mask) + 1
    grow = {(x + dx, y + dy) for x, y in mask for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    for x, y in grow:
        cv.set(ox + x + 2, oy + y + 2, "red")          # shadow
    for x, y in grow - mask:
        cv.set(ox + x, oy + y, "red")                  # outline
    for x, y in mask:
        t = y / h
        if t < 0.28:
            c = "cream" if t < 0.18 or dither(x, y, 0.5) else "gold"
        elif t < 0.62:
            c = "gold" if t < 0.52 or dither(x, y, 0.5) else "orange"
        else:
            c = "orange"
        if t < 0.28 and (x + y) % 29 == 0:           # a glint on the top band
            c = "cream"
        cv.set(ox + x, oy + y, c)


def draw_billboard(cv, x0, y0, x1, y1):
    """A rooftop billboard: copper frame with marquee bulbs, dark face, two legs."""
    for leg in (x0 + 18, x1 - 22):
        for y in range(y1, 84):
            for x in range(leg, leg + 4):
                cv.set(x, y, "b1" if x == leg else "b0")
        for y in range(y1 + 4, 84, 6):                # cross braces
            for x in range(leg - 2, leg + 6):
                cv.set(x, y, "b0")
    for y in range(y0, y1):
        for x in range(x0, x1):
            d = min(x - x0, x1 - 1 - x, y - y0, y1 - 1 - y)
            if d == 0:
                c = "r0"
            elif d == 1:
                lit = (x - x0) % 8 == 4 if y in (y0 + 1, y1 - 2) else (y - y0) % 8 == 4
                c = "r3" if lit else ("r2" if (x - x0 < 3 or y - y0 < 3) else "r1")
            elif d == 2:
                c = "r1"
            else:
                c = "panel"
            cv.set(x, y, c)


def draw_puck_streak(cv, cx, cy):
    for i, (dy, length) in enumerate(((-3, 12), (0, 18), (3, 10))):
        for k in range(length):
            if k % 4 != 3:
                cv.set(cx - 8 - k, cy + dy, "orange" if k > length // 2 else "gold")
    for y in range(cy - 5, cy + 6):
        for x in range(cx - 5, cx + 6):
            d = math.hypot(x - cx, y - cy)
            if d <= 5:
                c = "red" if d > 4 else ("cream" if (x - cx) + (y - cy) < -3 else "gold")
                cv.set(x, y, c)


def scene_title(glyph_rows):
    cv = Canvas()
    draw_sky(cv, 0, 84, moon=None)
    draw_skyline(cv, 84, seed=5, water_tower=False)
    draw_string_lights(cv, 76, 80)
    draw_billboard(cv, 8, 8, 152, 72)
    draw_parapet(cv, 82, 92)
    draw_deck(cv, 92, cv.h)
    top = logo_mask(glyph_rows, "SKYDECK", 3, 0.34)
    draw_logo_word(cv, top, 80 - (max(x for x, _ in top) + 1) // 2, 15)
    low = logo_mask(glyph_rows, "SLIDE", 3, 0.34)
    lw = max(x for x, _ in low) + 1
    lx = 80 - lw // 2 - 6
    draw_logo_word(cv, low, lx, 41)
    draw_puck_streak(cv, lx + lw + 14, 52)
    # dark panel behind the menu text (rows 12-17)
    cv.rect(0, 93, cv.w, 141, "s0")
    for x in range(cv.w):
        cv.set(x, 93, "s2")
        cv.set(x, 140, "s2")
    return cv


# ---------------------------------------------------------------------------
# opponents: drawn from shapes, then outlined. 24x32, colours 1/2/3.
# ---------------------------------------------------------------------------
class Sprite:
    def __init__(self, w=24, h=32):
        self.w, self.h = w, h
        self.px = [[0] * w for _ in range(h)]

    def set(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(self.h):
            for x in range(self.w):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    self.px[y][x] = c

    def tri(self, pts, c):
        (ax, ay), (bx, by), (cx_, cy_) = pts
        for y in range(self.h):
            for x in range(self.w):
                px, py = x + 0.5, y + 0.5
                d1 = (px - bx) * (ay - by) - (ax - bx) * (py - by)
                d2 = (px - cx_) * (by - cy_) - (bx - cx_) * (py - cy_)
                d3 = (px - ax) * (cy_ - ay) - (cx_ - ax) * (py - ay)
                neg = d1 < 0 or d2 < 0 or d3 < 0
                pos = d1 > 0 or d2 > 0 or d3 > 0
                if not (neg and pos):
                    self.px[y][x] = c

    def stroke(self, pts, r, c):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
            for i in range(n + 1):
                t = i / n
                self.ellipse(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, r, c)

    def outline(self, c=3):
        src = [row[:] for row in self.px]
        for y in range(self.h):
            for x in range(self.w):
                if src[y][x] == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        xx, yy = x + dx, y + dy
                        if 0 <= xx < self.w and 0 <= yy < self.h and src[yy][xx] not in (0, c):
                            self.px[y][x] = c
                            break

    def shade(self, c_from, c_to, test):
        """Recolour pixels of one colour where test(x, y) holds (lighting)."""
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] == c_from and test(x, y):
                    self.px[y][x] = c_to


# Shared finishing passes: form shading (dithered dark on the lower right of a
# part, light on the upper left) and small textures, so the characters read as
# solid, lit shapes rather than flat blobs. Only rows 0-25 show above the board.
# ---------------------------------------------------------------------------
# Opponents, 32x32 with six colours. Each is drawn with colour slots
#   1 outline   2 main   3 light            -> sprite layer A (OBJ palette 3)
#   4 shadow    5 accent 6 accent shadow    -> sprite layer B (OBJ palette 4)
# and split into the two layers afterwards. The bottom of each image runs
# behind the far board in a match, so faces and props sit in the upper part.
# ---------------------------------------------------------------------------
O, M, L, D, A, B = 1, 2, 3, 4, 5, 6


def form_shade(s, cx, cy, rx, ry, base, dark, light=None, hi=None):
    """Light from the top left: dithered shadow lower right, light and highlight upper left."""
    for y in range(s.h):
        for x in range(s.w):
            if s.px[y][x] != base:
                continue
            u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if u * u + v * v > 1.3:
                continue
            k = (u + v) / 2
            if k > 0.22 and dither(x, y, min(1, (k - 0.22) * 2.4)):
                s.px[y][x] = dark
            elif hi is not None and k < -0.62 and dither(x, y, min(1, (-0.62 - k) * 4)):
                s.px[y][x] = hi
            elif light is not None and k < -0.3 and dither(x, y, min(1, (-0.3 - k) * 2.6)):
                s.px[y][x] = light


def speckle(s, base, colour, test, rate=0.5, seed=0):
    for y in range(s.h):
        for x in range(s.w):
            if s.px[y][x] == base and test(x, y) and noise(x, y, seed, 997) < rate:
                s.px[y][x] = colour


def ring(s, cx, cy, r, c, a0=0, a1=360, step=6, sy=1.0):
    for a in range(a0, a1, step):
        s.set(cx + r * math.cos(math.radians(a)), cy + r * sy * math.sin(math.radians(a)), c)


def big():
    return Sprite(32, 32)


def tomo(hit):
    """Tomo, a sleepy old tortoise in round spectacles."""
    s = big()
    s.ellipse(16, 28, 15, 12, M)                         # shell dome behind the body
    s.ellipse(16, 29, 8.5, 9, L)                         # plastron
    arm_l = [(6, 22), (2, 13)] if hit else [(6, 22), (4, 30)]
    s.stroke(arm_l, 2.4, L)
    s.stroke([(26, 22), (28, 30)], 2.4, L)
    s.stroke([(16, 15), (16, 20)], 3.4, L)               # neck
    s.ellipse(16, 10, 8, 7, L)                           # head
    s.ellipse(16, 14, 5, 2.6, L)                         # jaw
    s.outline(O)
    form_shade(s, 16, 28, 15, 12, M, D, A)
    form_shade(s, 16, 10, 8, 7, L, B)
    form_shade(s, 16, 29, 8.5, 9, L, B)
    for y in (24, 28):                                   # plastron segments
        for x in range(9, 24):
            if s.px[y][x] in (L, B):
                s.px[y][x] = B
    for x in range(16, 17):
        for y in range(21, 32):
            if s.px[y][x] in (L, B):
                s.px[y][x] = B
    for cx, cy in ((4, 24), (28, 24), (7, 19), (25, 19)):          # shell plate seams
        ring(s, cx, cy, 3, O, 0, 360, 30)
    for y in (17, 19):                                   # neck wrinkles
        s.set(14, y, B); s.set(15, y, B); s.set(17, y, B); s.set(18, y, B)
    for ex in (12, 20):                                  # spectacles
        ring(s, ex, 9.5, 3, O, 0, 360, 15)
        s.set(ex - 1, 8, A)
    s.set(15, 9, O); s.set(16, 9, O); s.set(17, 9, O)    # bridge
    if hit:
        s.set(12, 10, O); s.set(20, 10, O)               # eyes open
        s.ellipse(16, 14, 1.8, 1.2, O)
    else:
        for x in (11, 12, 13, 19, 20, 21):
            s.set(x, 10, O)                              # heavy lids
        s.set(14, 14, O); s.set(15, 15, O); s.set(16, 15, O); s.set(17, 15, O); s.set(18, 14, O)
    cx, cy = arm_l[-1]
    for dx in (-1, 1):
        s.set(cx + dx, cy - 1 if hit else cy + 1, O)     # claws
    return s.px


def pip(hit):
    """Pip, a peppy penguin in a knitted beanie and scarf."""
    s = big()
    s.ellipse(16, 27, 11, 11, M)                         # body
    s.ellipse(16, 28.5, 7, 9, L)                         # belly
    if hit:
        s.stroke([(6, 22), (2, 12)], 2.0, M)
        s.stroke([(26, 22), (30, 12)], 2.0, M)
    else:
        s.stroke([(6, 21), (3, 31)], 2.0, M)
        s.stroke([(26, 21), (29, 31)], 2.0, M)
    s.ellipse(16, 11, 9, 8, M)                           # head
    s.ellipse(12.5, 12, 3, 3.5, L)                       # face patches
    s.ellipse(19.5, 12, 3, 3.5, L)
    s.ellipse(16, 14.5, 4.5, 2.2, L)
    s.ellipse(16, 5, 8.5, 4.5, A)                        # beanie
    s.ellipse(16, 0.8, 2.2, 1.8, L)                      # pompom
    s.outline(O)
    for x in range(8, 25):                               # beanie rib band
        if s.px[8][x] in (A, M):
            s.px[8][x] = B
        if s.px[6][x] == A and x % 2:
            s.px[6][x] = B
    for x in range(7, 26):                               # scarf
        for y in (18, 19, 20):
            if s.px[y][x]:
                s.px[y][x] = B if (x + y) % 4 == 0 else A
    s.stroke([(21, 20), (24, 27)], 1.2, A)               # scarf tail
    s.set(24, 28, B); s.set(23, 28, B)
    form_shade(s, 16, 27, 11, 11, M, O)
    form_shade(s, 16, 28.5, 7, 9, L, D)
    form_shade(s, 16, 11, 9, 8, M, O)
    s.set(10, 3, L); s.set(11, 3, L); s.set(9, 4, L)     # beanie shine
    for ex in (13, 19):                                  # big eyes
        s.ellipse(ex, 12, 1.5, 1.9, O)
        s.set(ex - 1, 11, L)
    s.tri([(14, 15), (18, 15), (16, 18.5 if hit else 17.5)], A)  # beak
    s.set(15, 15, B); s.set(16, 15, B)
    if hit:
        s.set(16, 17, O)
    return s.px


def rusty(hit):
    """Rusty, a cocky city fox: raised brow, smirk, tail tucked low behind him."""
    s = big()
    s.stroke([(24, 31), (29, 28), (30, 24)], 2.6, M)     # tail, low and to the side
    s.ellipse(30, 23.5, 2, 2, L)
    s.ellipse(16, 27, 10, 9, M)                          # body
    paw_l = (4, 12) if hit else (6, 30)
    s.stroke([(8, 22), paw_l], 2.2, M)
    s.stroke([(24, 22), (25, 30)], 2.2, M)
    s.ellipse(16, 12, 8.5, 7, M)                         # head
    s.tri([(6, 14), (8, 7), (12, 15)], M)                # cheek tufts
    s.tri([(26, 14), (24, 7), (20, 15)], M)
    s.tri([(7, 8), (9, 0), (13, 6)], M)                  # ears
    s.tri([(25, 8), (23, 0), (19, 6)], M)
    s.tri([(10, 12), (22, 12), (16, 20)], L)             # muzzle
    s.tri([(10, 20), (22, 20), (16, 30)], L)             # chest ruff
    s.outline(O)
    s.tri([(8.4, 3), (9, 0.5), (10.5, 3.6)], O)          # dark ear tips
    s.tri([(23.6, 3), (23, 0.5), (21.5, 3.6)], O)
    for x, y in ((10, 5), (11, 5), (21, 5), (22, 5)):
        s.set(x, y, L)                                   # inner ear
    form_shade(s, 16, 27, 10, 9, M, D, A)
    form_shade(s, 16, 12, 8.5, 7, M, D, A)
    form_shade(s, 16, 15, 6, 5, L, B)
    form_shade(s, 16, 25, 6, 5, L, B)
    speckle(s, M, D, lambda x, y: y > 21 and (x < 10 or x > 22), 0.4, 3)   # fur
    for x in range(11, 15):
        s.set(x, 10, O)                                  # half-lidded eyes
    for x in range(18, 22):
        s.set(x, 10, O)
    s.set(12, 11, O); s.set(19, 11, O)
    s.set(11, 8, O); s.set(12, 7, O); s.set(13, 7, O)    # one raised eyebrow
    s.set(19, 8, O); s.set(20, 8, O); s.set(21, 8, O)
    s.set(15, 14, O); s.set(16, 14, O); s.set(17, 14, O)  # nose
    s.set(16, 15, O)
    if hit:
        s.ellipse(16, 17.5, 1.6, 1, O)
    else:
        s.set(15, 17, O); s.set(16, 17, O); s.set(17, 17, O); s.set(18, 16, O)  # smirk
    px, py = paw_l
    for dx in (-1, 0, 1):                                # dark socks
        s.set(px + dx, py, O); s.set(px + dx, py - (1 if not hit else -1), O)
        s.set(25 + dx, 30, O); s.set(25 + dx, 29, O)
    return s.px


def zuri(hit):
    """Zuri, an alert meerkat lookout, one paw shading her eyes."""
    s = big()
    s.ellipse(16, 25, 7, 12, M)                          # body
    s.ellipse(16, 27, 4, 9, L)                           # belly
    if hit:
        s.stroke([(10, 18), (5, 9)], 1.8, M)             # swipe
    else:
        s.stroke([(10, 18), (8, 12), (11, 6)], 1.8, M)   # paw up at her brow
    s.stroke([(22, 18), (21, 24)], 1.8, M)
    s.stroke([(16, 12), (16, 16)], 3.0, M)               # neck
    s.ellipse(16, 8.5, 6.5, 6, M)                        # head
    s.ellipse(16, 12, 3, 2.4, L)                         # snout
    s.ellipse(9.5, 5.5, 2, 2, M)                         # ears
    s.ellipse(22.5, 5.5, 2, 2, M)
    s.outline(O)
    form_shade(s, 16, 25, 7, 12, M, D, A)
    form_shade(s, 16, 8.5, 6.5, 6, M, D, A)
    form_shade(s, 16, 27, 4, 9, L, B)
    for y in (16, 18, 20):                               # shoulder stripes
        s.set(11, y, D); s.set(21, y, D)
    for y in (24, 27, 30):                               # soft belly fur
        s.set(15, y, B); s.set(17, y + 1, B)
    s.ellipse(13, 8, 1.8, 2.3, O)                        # eye mask
    s.ellipse(19, 8, 1.8, 2.3, O)
    s.set(13, 7, L); s.set(19, 7, L)
    s.set(15, 12, O); s.set(16, 12, O); s.set(17, 12, O)
    if hit:
        s.set(16, 14, O)
        s.set(4, 8, O); s.set(6, 8, O)                   # claws
    else:
        s.set(10, 5, O); s.set(12, 5, O)                 # fingers at the brow
    s.set(20, 24, O); s.set(22, 24, O)
    return s.px


def okta(hit):
    """Okta, a smooth octopus trickster in a little top hat."""
    s = big()
    arms = [((9, 23), (3, 28), (5, 32)), ((12, 25), (9, 30), (12, 32)),
            ((20, 25), (23, 30), (20, 32)), ((23, 23), (29, 28), (27, 32))]
    if hit:
        arms[0] = ((9, 22), (2, 17), (3, 10))
        arms[3] = ((23, 22), (30, 17), (29, 10))
    for pts in arms:
        s.stroke(list(pts), 2.0, M)
    s.ellipse(16, 16, 11, 9.5, M)                        # mantle
    s.ellipse(16, 22, 8, 3.5, M)
    s.outline(O)
    for y in range(0, 7):                                # top hat, tipped to one side
        for x in range(14, 23):
            s.set(x, y, O)
    for x in range(11, 26):
        s.set(x, 7, O)                                   # brim
    for x in range(15, 22):
        s.set(x, 5, B)                                   # band
    s.set(15, 1, D); s.set(15, 2, D)                     # shine on the crown
    form_shade(s, 16, 16, 11, 9.5, M, D, L)
    for x, y in ((9, 11), (23, 12), (11, 19), (21, 19), (7, 15), (25, 16)):
        s.set(x, y, D)                                   # spots
        s.set(x + 1, y, L)
    for pts in arms:                                     # suckers
        (x0, y0), (x1, y1), (x2, y2) = pts
        for t in (0.3, 0.65):
            s.set(x0 + (x1 - x0) * t + 0.8, y0 + (y1 - y0) * t, B)
        s.set(x1 + (x2 - x1) * 0.5 + 0.8, y1 + (y2 - y1) * 0.5, B)
    for ex in (11.5, 20.5):                              # big eyes
        s.ellipse(ex, 15.5, 3, 3, A)
        for dx in (-1, 0, 1):
            s.set(ex + dx, 15.5, O)                      # bar pupils
        s.set(ex - 1, 14.5, A)
        ring(s, ex, 15.5, 3.6, O, 200, 340, 20)          # brows
    if hit:
        s.ellipse(16, 21, 2, 1.3, O)
    else:
        s.set(14, 20, O); s.set(15, 21, O); s.set(16, 21, O); s.set(17, 21, O); s.set(18, 20, O)
    return s.px


def blaze(hit):
    """Blaze, a hot-headed young dragon."""
    s = big()
    for side in (-1, 1):                                 # bat wings
        s.tri([(16 + side * 5, 18), (16 + side * 16, 2), (16 + side * 15, 24)], M)
    s.ellipse(16, 26, 9, 10, M)                          # body
    s.ellipse(16, 27, 5, 8, A)                           # belly plates
    claw = (4, 13) if hit else (7, 30)
    s.stroke([(10, 21), claw], 2.0, M)
    s.stroke([(22, 21), (25, 30)], 2.0, M)
    s.ellipse(16, 11, 7.5, 6.5, M)                       # head
    s.ellipse(16, 15, 5, 3.2, M)                         # snout
    s.tri([(10, 7), (6, -1), (13, 5)], A)                # horns
    s.tri([(22, 7), (26, -1), (19, 5)], A)
    s.outline(O)
    for side in (-1, 1):                                 # wing bones and membrane shade
        for k in range(1, 11):
            s.set(16 + side * (5 + k), 18 - k * 1.55, O)
        for k in range(1, 10):
            s.set(16 + side * (5 + k), 18 + k * 0.55, O)
        for y in range(4, 24):
            for x in range(32):
                if s.px[y][x] == M and (x - 16) * side > 9 and dither(x, y, 0.5):
                    s.px[y][x] = D
    for y in (21, 24, 27, 30):                           # belly plate lines
        for x in range(11, 22):
            if s.px[y][x] == A:
                s.px[y][x] = B
    form_shade(s, 16, 26, 9, 10, M, D, L)
    form_shade(s, 16, 11, 7.5, 6.5, M, D, L)
    form_shade(s, 16, 27, 5, 8, A, B)
    speckle(s, M, D, lambda x, y: (x + 2 * y) % 4 == 0 and y > 18, 0.7, 7)   # scales
    for x, y in ((11, 8), (12, 7), (20, 7), (21, 8)):    # brow ridges
        s.set(x, y, O)
    s.set(12, 10, A); s.set(13, 10, O); s.set(19, 10, O); s.set(20, 10, A)  # glowing eyes
    s.set(14, 15, O); s.set(18, 15, O)                   # nostrils
    if hit:
        s.ellipse(16, 18, 2.4, 1.5, O)
        s.set(14, 17, L); s.set(18, 17, L)               # fangs
        for x, y, c in ((16, 21, A), (15, 22, A), (17, 22, B), (16, 23, A), (14, 23, B),
                        (18, 23, A), (16, 24, B)):
            s.set(x, y, c)                               # a burst of flame
    else:
        s.set(14, 18, O); s.set(15, 18, O); s.set(16, 18, O); s.set(17, 18, O)
        s.set(13, 13, L); s.set(13, 12, L)               # smoke from a nostril
    px, py = claw
    s.set(px - 1, py + 1, A); s.set(px + 1, py + 1, A)
    return s.px


def nova(hit):
    """Nova, the cool champion: a cat in a glass space helmet with glowing eyes."""
    s = big()
    s.ellipse(16, 27, 11, 9, L)                          # suit
    arm_l = [(7, 23), (4, 13)] if hit else [(7, 23), (5, 31)]
    s.stroke(arm_l, 2.4, L)
    s.stroke([(25, 23), (27, 31)], 2.4, L)
    s.ellipse(16, 11, 6.5, 5.5, M)                       # head
    s.tri([(10, 9), (10, 2), (14, 6)], M)                # ears
    s.tri([(22, 9), (22, 2), (18, 6)], M)
    s.ellipse(16, 14, 3, 2, L)                           # muzzle
    s.outline(O)
    form_shade(s, 16, 27, 11, 9, L, D)
    form_shade(s, 16, 11, 6.5, 5.5, M, D)
    for x in range(6, 27):                               # collar ring
        if s.px[19][x]:
            s.px[19][x] = O if s.px[19][x] == O else D
    for y in range(20, 32):                              # suit seams
        for x in (11, 21):
            if s.px[y][x] in (L, D):
                s.px[y][x] = D
    s.ellipse(16, 25, 2.2, 2.2, B)                       # badge
    s.set(16, 25, A)
    for x in (13, 16, 19):
        s.set(x, 7, D); s.set(x, 8, D)                   # tabby stripes
    for ex in (13, 19):
        s.set(ex, 11, A); s.set(ex + (1 if ex < 16 else -1), 11, B)   # glowing eyes
    s.set(16, 13, O)
    if hit:
        s.set(16, 15, O)
    for side in (-1, 1):                                 # whiskers
        s.set(16 + side * 5, 13, O); s.set(16 + side * 6, 14, O)
    ring(s, 16, 11, 11, O, 0, 360, 4)                    # helmet
    ring(s, 16, 11, 10, A, 200, 260, 6)                  # glass glare
    ring(s, 16, 11, 8.5, A, 215, 235, 8)
    s.set(25, 16, B)
    if hit:
        cx, cy = arm_l[-1]
        s.set(cx, cy - 2, L); s.set(cx, cy - 3, L)       # thumbs up
    return s.px


def split_layers(px):
    """Slots 1-3 -> layer A (indices 1-3), slots 4-6 -> layer B (indices 1-3)."""
    la = [[v if v in (1, 2, 3) else 0 for v in row] for row in px]
    lb = [[v - 3 if v in (4, 5, 6) else 0 for v in row] for row in px]
    return la, lb


# Glossary pages: (title, opponent index or None, text). Text is word-wrapped
# to 18 columns; up to 10 lines, or 6 when the page shows an opponent.
BIOS = [
    "RETIRED CHAMPION OF THE JUNGLE CANOPY. SLOW TO MOVE, QUICK TO NAP. A GENTLE FIRST TEST.",
    "A YOUNG SPEEDSTER FROM THE SNOW LODGE. ALL ENERGY, NOT MUCH AIM. KEEP THE PUCK MOVING.",
    "RUNS THE ROOFTOP TABLES DOWNTOWN. FAST TALKER, FASTER HANDS. LOVES A WIDE ANGLE.",
    "A CANYON LOOKOUT WHO READS EVERY SHOT. A STRAIGHT ONE WON'T FOOL HER. USE THE RAILS.",
    "A PIER HUSTLER WITH A HAT FULL OF TRICKS. STEPS IN CLOSE TO STEAL YOUR SHOTS.",
    "HOT-HEADED AND HARD-HITTING. HIS RETURNS COME BACK FAST AND MEAN. STAY CALM.",
    "UNBEATEN ON THE MOON BASE. SEES WHERE THE PUCK WILL GO, AND IS ALREADY THERE.",
]
FULL_NAMES = ["TOMO THE TORTOISE", "PIP THE PENGUIN", "RUSTY THE FOX", "ZURI THE MEERKAT",
              "OKTA THE OCTOPUS", "BLAZE THE DRAGON", "NOVA THE SPACE CAT"]
TERMS = [
    "PUCK: THE DISC YOU SLIDE.", "PADDLE: WHAT YOU HIT IT WITH.",
    "RAIL: THE TABLE'S RAISED EDGE.", "BANK SHOT: A SHOT OFF THE RAIL.",
    "RALLY: A RUN OF RETURNS.", "SERVE: FIRST HIT AFTER A GOAL.",
    "LUNGE: STEPPING IN TO MEET A SHOT.", "GOAL: A PUCK PAST THE PADDLE.",
    "LEVEL: EACH RIVAL IS TOUGHER.",
]
# (title, stage shown at the top, opponent standing in it or None, text lines)
HALL_SCREEN = 9          # StageTable entries after the stages, title and how-to
CHALK_SCREEN = 10
GLOSSARY = [(FULL_NAMES[i], HALL_SCREEN, i, BIOS[i]) for i in range(7)] + [
    ("PUCK TERMS", CHALK_SCREEN, None, TERMS[0:3]),
    ("PUCK TERMS", CHALK_SCREEN, None, TERMS[3:6]),
    ("PUCK TERMS", CHALK_SCREEN, None, TERMS[6:9]),
]
QUOTES = [
    "SLOW AND STEADY... ZZZ... OH! MY SERVE?",
    "I SLIDE ON ICE ALL DAY. THIS IS NOTHING!",
    "NICE TABLE. SHAME YOU WON'T GET TO USE IT.",
    "I SAW YOUR SHOT COMING BEFORE YOU DID.",
    "EIGHT ARMS, ONE PUCK. DO THE MATH, FRIEND.",
    "THIS TABLE IS ABOUT TO GET SCORCHED!",
    "THE STARS SAID YOU'D GET THIS FAR. NOT FURTHER.",
]
STAGE_TITLES = ["JUNGLE CANOPY", "SNOW LODGE", "CITY ROOFTOP", "DESERT CANYON",
                "SUNSET PIER", "VOLCANO FORGE", "MOON BASE"]
# the splash card shown before each match: palette 0 cream text, palette 1 gold text
CARD_PALETTES = [
    [(2, 2, 8), (5, 5, 14), (31, 24, 6), (31, 31, 22)],
    [(2, 2, 8), (5, 5, 14), (31, 24, 6), (31, 24, 6)],
] + [[(2, 2, 8), (5, 5, 14), (31, 24, 6), (31, 31, 22)]] * 6

CHARACTERS = [("tomo", tomo), ("pip", pip), ("rusty", rusty), ("zuri", zuri),
              ("okta", okta), ("blaze", blaze), ("nova", nova)]
NAMES = ["TOMO ", "PIP  ", "RUSTY", "ZURI ", "OKTA ", "BLAZE", "NOVA "]
# each opponent's sprite palette (colour 1 light, 2 main, 3 outline/dark),
# copied into OBJ palette 3 when their match starts
CHAR_PALETTES = [   # per opponent: (layer A colours 1-3, layer B colours 1-3)
    [((2, 5, 2), (9, 18, 6), (27, 23, 13)), ((5, 11, 4), (16, 25, 9), (18, 14, 8))],      # Tomo
    [((2, 2, 6), (7, 9, 18), (31, 31, 31)), ((17, 19, 26), (31, 17, 3), (20, 7, 2))],     # Pip
    [((6, 2, 2), (28, 12, 3), (31, 30, 26)), ((18, 6, 2), (31, 22, 10), (21, 18, 17))],   # Rusty
    [((6, 3, 1), (23, 15, 8), (31, 28, 19)), ((14, 8, 3), (29, 22, 13), (24, 20, 12))],   # Zuri
    [((5, 1, 9), (20, 8, 26), (28, 17, 31)), ((12, 4, 18), (31, 31, 31), (31, 19, 25))],  # Okta
    [((7, 1, 2), (27, 6, 4), (31, 15, 7)), ((16, 3, 3), (31, 26, 8), (26, 14, 3))],       # Blaze
    [((4, 4, 10), (17, 16, 27), (30, 31, 31)), ((10, 9, 19), (12, 28, 31), (19, 21, 26))],  # Nova
]
