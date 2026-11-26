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

GAME_PALETTES = [PAL_SKY, PAL_SKYLINE, PAL_OUTER, PAL_BRICK, PAL_INNER, PAL_WOOD, PAL_TABLE, PAL_RAIL]
TITLE_PALETTES = [PAL_SKY, PAL_SKYLINE, PAL_LOGO, PAL_BRICK, PAL_INNER, PAL_WOOD, PAL_TABLE, PAL_RAIL]
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


def draw_deck(cv, y0, y1):
    """Wooden planks with grain, staggered seams and nails."""
    plank = 6
    for y in range(y0, y1):
        ry = (y - y0) % plank
        row = (y - y0) // plank
        for x in range(cv.w):
            seam = (x + row * 23) % 40 == 0
            if ry == plank - 1 or seam:
                c = "w0"
            elif ry == 0:
                c = "w3" if noise(x, y, 11) < 0.6 else "w2"
            else:
                g = noise(x // 3, y, 12 + row % 3)
                c = "w1" if g < 0.25 else ("w3" if g > 0.93 else "w2")
            cv.set(x, y, c)
        for x in range(cv.w):
            if ry == 2 and ((x + row * 23) % 40 in (3, 37)):
                cv.set(x, y, "w0")                  # nail heads


def rail_width(z):
    return max(12, round(13 * xscale64(z) / 64))


def draw_crates(cv, x0, y0):
    """A small stack of wooden crates on the deck."""
    for bx, by, s in ((x0, y0 + 10, 14), (x0 + 14, y0 + 13, 11), (x0 + 4, y0, 10)):
        for y in range(by, by + s):
            for x in range(bx, bx + s):
                edge = x in (bx, bx + s - 1) or y in (by, by + s - 1)
                diag = abs((x - bx) - (y - by)) <= 0 and not edge
                if edge or diag:
                    c = "w0"
                elif y == by + 1 or x == bx + 1:
                    c = "w3"
                else:
                    c = "w2" if noise(x, y, 13) > 0.2 else "w1"
                cv.set(x, y, c)


def draw_table(cv):
    far_y = round(screen_y(0))
    near_y = cv.h
    left0 = screen_x(-TABLE_HALF, 0)
    right0 = screen_x(TABLE_HALF, 0)
    rw0 = rail_width(0)
    # far backboard: a thick copper bar with studs
    for y in range(far_y - 6, far_y):
        for x in range(round(left0 - rw0), round(right0 + rw0) + 1):
            ry = y - (far_y - 6)
            c = ("r0", "r2", "r3", "r2", "r1", "r0")[ry]
            if ry in (2, 3) and x % 10 == 5:
                c = "r3" if ry == 2 else "r0"
            cv.set(x, y, c)
    # table body
    for y in range(far_y, near_y):
        z = z_at_y(y + 0.5)
        lx = screen_x(-TABLE_HALF, z)
        rx = screen_x(TABLE_HALF, z)
        rw = rail_width(z)
        for x in range(cv.w):
            px = x + 0.5
            if lx <= px <= rx:
                # surface: darker toward the rails, a soft sheen down the middle
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
                    c = "r3" if f < 0.06 else "r2"
                elif f < 0.45:
                    c = "r2" if dither(x, y, 0.5 - f) else "r1"
                elif f < 0.85:
                    c = "r1" if noise(x, y, 14) > 0.12 else "r0"
                else:
                    c = "r0"
                cv.set(x, y, c)
        # studs along the rails every 24 depth units
    for zs in range(12, Z_NEAR, 24):
        y = round(screen_y(zs))
        rw = rail_width(zs)
        for side in (-1, 1):
            cx = screen_x(side * TABLE_HALF, zs) + side * rw * 0.55
            r = max(1, round(rw / 9))
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r:
                        cv.set(round(cx) + dx, y + dy, "r3" if dx + dy < 0 else "r0")
    # grid lines
    for zl in (48, 96, 144):
        y = round(screen_y(zl))
        for x in range(round(screen_x(-TABLE_HALF, zl)) + 1, round(screen_x(TABLE_HALF, zl))):
            if cv.get(x, y) in ("t1", "t0", "t2"):
                cv.set(x, y, "t2")
    for xl in (-24, 0, 24):
        for y in range(far_y, near_y):
            z = z_at_y(y + 0.5)
            cv.set(round(screen_x(xl, z) - 0.5), y, "t2")
    # centre ring
    cz, cy = 96, round(screen_y(96))
    rx_ = 12 * xscale64(cz) / 64
    for a in range(0, 360, 3):
        x = CENTER_X + rx_ * math.cos(math.radians(a))
        y = cy + rx_ * 0.35 * math.sin(math.radians(a))
        cv.set(round(x), round(y), "t2")
    # moon reflection near the far end
    for y in range(far_y + 3, far_y + 14):
        for x in range(CENTER_X + 6, CENTER_X + 22):
            d = ((x - (CENTER_X + 14)) / 7) ** 2 + ((y - (far_y + 8)) / 4) ** 2
            if d < 1 and dither(x, y, 0.7 * (1 - d)):
                cv.set(x, y, "t3")


def scene_game():
    cv = Canvas()
    draw_sky(cv, 8, 40)
    draw_skyline(cv, 40)
    draw_string_lights(cv, 27, 34)
    draw_parapet(cv, 38, 47)
    draw_deck(cv, 47, cv.h)
    draw_crates(cv, 2, 52)
    draw_table(cv)
    cv.rect(0, 0, cv.w, 8, "s0")               # HUD row
    return cv


def scene_title(text_font):
    cv = Canvas()
    draw_sky(cv, 0, 84, moon=None)
    draw_skyline(cv, 84, seed=5)
    draw_string_lights(cv, 70, 78)
    draw_parapet(cv, 82, 92)
    draw_deck(cv, 92, cv.h)
    # logo panel with a gold frame and the title in 3x letters
    x0, y0, x1, y1 = 8, 12, 152, 66
    for y in range(y0, y1):
        for x in range(x0, x1):
            frame = x in (x0, x1 - 1) or y in (y0, y1 - 1)
            inner = x in (x0 + 2, x1 - 3) or y in (y0 + 2, y1 - 3)
            cv.set(x, y, "gold" if frame else ("orange" if inner else "panel"))
    text_font(cv, "SKYDECK", 17, 17, 3, "gold", "red", "orange")
    text_font(cv, "SLIDE", 35, 42, 3, "gold", "red", "orange")
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


def tomo(hit):
    s = Sprite()
    # shell body with skin belly
    s.ellipse(12, 23, 9, 8, 2)
    s.ellipse(12, 24.5, 5, 5.5, 1)
    for y in (22, 25, 28):
        for x in range(9, 16):
            s.set(x, y, 3)
    # arms
    if hit:
        s.stroke([(4, 20), (2, 13)], 1.6, 1)
        s.stroke([(20, 20), (22, 14)], 1.6, 1)
    else:
        s.stroke([(4, 19), (3, 25)], 1.6, 1)
        s.stroke([(20, 19), (21, 25)], 1.6, 1)
    # head
    s.ellipse(12, 10, 6.5, 6, 1)
    s.outline()
    # shell plates (dark seams on the green)
    for x, y in ((6, 19), (7, 18), (17, 18), (18, 19), (5, 23), (19, 23), (6, 27), (18, 27)):
        s.set(x, y, 3)
    # face
    if hit:
        s.set(9, 9, 3); s.set(10, 9, 3); s.set(14, 9, 3); s.set(15, 9, 3)
        s.ellipse(12, 13, 1.6, 1.2, 3)
    else:
        for x in (9, 10, 14, 15):
            s.set(x, 10, 3)
        s.set(11, 13, 3); s.set(12, 13, 3); s.set(13, 13, 3)
    s.shade(1, 2, lambda x, y: x > 15 and y > 9 and y < 15)      # cheek shadow
    s.shade(2, 1, lambda x, y: (x - 8) ** 2 + (y - 18) ** 2 < 3)  # shell glint
    return s.px


def rusty(hit):
    s = Sprite()
    # tail
    s.stroke([(19, 28), (22, 22), (21, 16)], 2.2, 2)
    s.ellipse(21, 15, 2, 2, 1)
    # body and chest
    s.ellipse(12, 24, 6.5, 7, 2)
    s.ellipse(12, 25, 3.5, 5, 1)
    if hit:
        s.stroke([(6, 21), (3, 14)], 1.5, 2)
        s.ellipse(3, 13, 1.6, 1.6, 1)
    else:
        s.stroke([(6, 21), (5, 27)], 1.5, 2)
    s.stroke([(18, 21), (18, 27)], 1.5, 2)
    # head with ears
    s.ellipse(12, 11, 6.5, 5.5, 2)
    s.tri([(5, 9), (7, 1), (10, 7)], 2)
    s.tri([(19, 9), (17, 1), (14, 7)], 2)
    s.ellipse(12, 14, 3.5, 2.5, 1)     # muzzle
    s.outline()
    s.tri([(7, 4), (7, 2), (8.5, 4.5)], 3)
    s.tri([(17, 4), (17, 2), (15.5, 4.5)], 3)
    s.set(9, 10, 3); s.set(15, 10, 3)
    s.set(12, 13, 3)
    if hit:
        s.ellipse(12, 15.5, 1.4, 1, 3)
    s.shade(2, 1, lambda x, y: (x - 9) ** 2 + (y - 8) ** 2 < 2)   # fur highlight
    return s.px


def okta(hit):
    s = Sprite()
    # tentacles, curling outward
    arms = [((7, 20), (3, 26), (5, 30)), ((10, 21), (8, 28), (10, 31)),
            ((14, 21), (16, 28), (14, 31)), ((17, 20), (21, 26), (19, 30))]
    if hit:
        arms[0] = ((7, 19), (2, 15), (3, 10))
        arms[3] = ((17, 19), (22, 15), (21, 10))
    for pts in arms:
        s.stroke(list(pts), 1.4, 2)
    # head
    s.ellipse(12, 12, 8.5, 9, 2)
    s.outline()
    # eyes
    for ex in (8.5, 15.5):
        s.ellipse(ex, 12, 2.2, 2.6, 1)
        s.set(ex + (0 if hit else 0.5), 12.5 if not hit else 11, 3)
    if hit:
        s.ellipse(12, 17, 1.5, 1.2, 3)
    else:
        s.set(11, 17, 3); s.set(12, 17, 3); s.set(13, 17, 3)
    s.shade(2, 1, lambda x, y: (x - 8) ** 2 + (y - 6) ** 2 < 4)   # head highlight
    for x, y in ((15, 6), (17, 8), (6, 15)):
        s.set(x, y, 3)                                             # spots
    return s.px


CHARACTERS = [("tomo", tomo), ("rusty", rusty), ("okta", okta)]
