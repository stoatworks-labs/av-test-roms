#!/usr/bin/env python3
"""Generate a C64 character set and the screen/colour maps for all three programs.

Hires text mode: 40x25 cells of 8x8, one bit per pixel. The foreground colour
comes from colour RAM per cell and the background is a single global register,
so a cell is two colours and a screen is seventeen.

That per-cell granularity is the whole shape of this target. It is finer than
the NES's 16x16 attribute block and coarser than the Mega Drive's per-cell
palette, and it lands exactly where the overscan rectangles need it not to -
see screen_overscan().
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import font  # noqa: E402

VW, VH = 40, 25
SCREEN_W, SCREEN_H = 320, 200

# VIC-II colour numbers. The palette is fixed in silicon; these are the ones
# that matter here.
BLACK, WHITE, RED, CYAN = 0, 1, 2, 3
PURPLE, GREEN, BLUE, YELLOW = 4, 5, 6, 7
ORANGE, BROWN, LTRED = 8, 9, 10
DGREY, MGREY, LTGREEN, LTBLUE, LGREY = 11, 12, 13, 14, 15

# SMPTE order as closely as the fixed palette allows. There is no magenta, so
# purple stands in for it - the nearest thing the machine has, and named as a
# substitution in ../README.md rather than passed off as magenta.
SMPTE = [WHITE, YELLOW, CYAN, GREEN, PURPLE, RED, BLUE, BLACK]

# Five greys, which is all of them: black, dark grey, mid grey, light grey,
# white.
GREYS = [BLACK, DGREY, MGREY, LGREY, WHITE]

# --- character numbers ----------------------------------------------------
C_BLANK = 0
C_SOLID = 1
C_STRIPE2, C_STRIPE4, C_STRIPE8 = 2, 3, 4
C_CHECK = 5
C_HATCH_CROSS, C_HATCH_V, C_HATCH_H = 6, 7, 8
C_XHAIR = 9
C_TICKCELL = 10                   # 4px mark at the left of the cell
C_HALF = 11                       # left half solid, for 4px ticker cells
# Font occupies 0x20..0x5F, indexed by ASCII, as on every other target.
C_VLINE = 0x60                    # 0x60..0x67
C_HLINE = 0x68                    # 0x68..0x6F
C_RULE_T, C_RULE_T6 = 0x70, 0x71
C_RULE_B, C_RULE_B6 = 0x72, 0x73
C_RULE_L, C_RULE_L6 = 0x74, 0x75
C_RULE_R, C_RULE_R6 = 0x76, 0x77
C_HLINE2 = 0x78                   # 0x78..0x7F: two horizontal lines in one cell
NUM_CHARS = 256


def blank():
    return [[0] * 8 for _ in range(8)]


def solid():
    return [[1] * 8 for _ in range(8)]


def stripe(period):
    return [[1 if (x % period) < period // 2 else 0 for x in range(8)] for _ in range(8)]


def check(size=4):
    return [[1 if ((x // size) + (y // size)) % 2 == 0 else 0
             for x in range(8)] for y in range(8)]


def hatch(v, h):
    return [[1 if ((v and x == 0) or (h and y == 0)) else 0
             for x in range(8)] for y in range(8)]


def vline(col):
    return [[1 if x == col else 0 for x in range(8)] for _ in range(8)]


def hline(row):
    return [[1 if y == row else 0 for x in range(8)] for y in range(8)]


def hline2(a, b):
    return [[1 if (y == a or y == b) else 0 for x in range(8)] for y in range(8)]


def rule(edge, length, pos):
    t = blank()
    step = 1 if edge in ('top', 'left') else -1
    if edge in ('top', 'bottom'):
        for x in range(8):
            t[pos][x] = 1
        for i in range(1, length + 1):
            if 0 <= pos + i * step < 8:
                t[pos + i * step][0] = 1
    else:
        for y in range(8):
            t[y][pos] = 1
        for i in range(1, length + 1):
            if 0 <= pos + i * step < 8:
                t[0][pos + i * step] = 1
    return t


def xhair():
    t = blank()
    for i in range(8):
        t[3][i] = 1
        t[i][3] = 1
    return t


def halfcell():
    return [[1 if x < 4 else 0 for x in range(8)] for _ in range(8)]


def glyph(ch):
    rows = font.rows_1bpp(ch)
    return [[(rows[y] >> (7 - x)) & 1 for x in range(8)] for y in range(8)]


def encode(ch):
    return bytes(sum(ch[y][x] << (7 - x) for x in range(8)) for y in range(8))


def build_charset():
    chars = [blank() for _ in range(NUM_CHARS)]
    for code in font.ascii_range():          # font first, so a collision shows
        chars[code] = glyph(chr(code))
    chars[C_SOLID] = solid()
    chars[C_STRIPE2], chars[C_STRIPE4], chars[C_STRIPE8] = stripe(2), stripe(4), stripe(8)
    chars[C_CHECK] = check()
    chars[C_HATCH_CROSS] = hatch(True, True)
    chars[C_HATCH_V] = hatch(True, False)
    chars[C_HATCH_H] = hatch(False, True)
    chars[C_XHAIR] = xhair()
    chars[C_TICKCELL] = halfcell()
    chars[C_HALF] = halfcell()
    for i in range(8):
        chars[C_VLINE + i] = vline(i)
        chars[C_HLINE + i] = hline(i)
    chars[C_RULE_T], chars[C_RULE_T6] = rule('top', 3, 0), rule('top', 6, 0)
    chars[C_RULE_B], chars[C_RULE_B6] = rule('bottom', 3, 7), rule('bottom', 6, 7)
    chars[C_RULE_L], chars[C_RULE_L6] = rule('left', 3, 0), rule('left', 6, 0)
    chars[C_RULE_R], chars[C_RULE_R6] = rule('right', 3, 7), rule('right', 6, 7)
    # Two rows in one cell. The 5% and 7.5% horizontal insets (y=10, y=15)
    # both land in character row 1, and the matching pair at the bottom
    # (y=189, y=184) both land in row 23. One cell has to carry both lines,
    # and since colour RAM is per cell those two rectangles share a colour.
    chars[C_HLINE2 + 0] = hline2(2, 7)
    chars[C_HLINE2 + 1] = hline2(0, 5)
    return b"".join(encode(c) for c in chars)


class Screen:
    def __init__(self, bg=BLACK):
        self.chars = [[C_BLANK] * VW for _ in range(VH)]
        self.colour = [[WHITE] * VW for _ in range(VH)]
        self.bg = bg

    def put(self, x, y, ch, col=WHITE):
        if 0 <= x < VW and 0 <= y < VH:
            self.chars[y][x] = ch
            self.colour[y][x] = col

    def text(self, x, y, s, col=WHITE):
        for i, c in enumerate(s.upper()):
            self.put(x + i, y, ord(c), col)

    def fill(self, x, y, w, h, ch, col=WHITE):
        for j in range(h):
            for i in range(w):
                self.put(x + i, y + j, ch, col)

    def emit(self):
        return (bytes(c for r in self.chars for c in r),
                bytes(c for r in self.colour for c in r))


# --- layouts --------------------------------------------------------------
# Row 0 title, rows 2..19 panel, row 23 the frame-ticker track.
PANEL_TOP, PANEL_ROWS = 2, 18
TICK_ROW = 23


def add_track(s):
    """60 cells of 4 pixels = 240 px = 30 character cells, two cells apiece."""
    for x in range(30):
        s.put(x, TICK_ROW, C_SOLID, DGREY)
        if x % 5 == 0:
            s.put(x, TICK_ROW, C_SOLID, RED)
    s.put(38, 0, C_SOLID, DGREY)          # parity flash backing


def panel_bars():
    s = Screen()
    s.text(1, 0, "1 BARS")
    for i, col in enumerate(SMPTE):
        s.fill(i * 5, PANEL_TOP, 5, 12, C_SOLID, col)
    # Five steps, which is every grey the VIC-II has.
    for i, col in enumerate(GREYS):
        s.fill(i * 8, 14, 8, 6, C_SOLID, col)
    return s


def panel_hatch():
    s = Screen()
    s.text(1, 0, "2 HATCH")
    for y in range(PANEL_TOP, PANEL_TOP + PANEL_ROWS):
        for x in range(VW):
            v, h = x % 2 == 0, (y - PANEL_TOP) % 2 == 0
            ch = (C_HATCH_CROSS if v and h else C_HATCH_V if v
                  else C_HATCH_H if h else C_BLANK)
            s.put(x, y, ch, WHITE)
    return s


def panel_burst():
    s = Screen()
    s.text(1, 0, "3 BURST")
    for b, ch in enumerate((C_STRIPE2, C_STRIPE4, C_STRIPE8, None)):
        y = PANEL_TOP + b * 4
        if ch is None:
            for x in range(VW):
                s.fill(x, y, 1, 4, C_SOLID if x % 2 == 0 else C_BLANK, WHITE)
        else:
            s.fill(0, y, VW, 4, ch, WHITE)
        s.text(0, y, str(2 ** b), YELLOW)
    return s


def panel_check():
    s = Screen()
    s.text(1, 0, "4 CHECK")
    # Inverted by rewriting the eight bytes of the check character itself.
    # The charset lives in RAM, so every cell using it flips at once - eight
    # writes a frame, the cheapest inversion in the whole suite.
    s.fill(0, PANEL_TOP, VW, PANEL_ROWS, C_CHECK, WHITE)
    return s


def panel_edge():
    s = Screen()
    s.text(1, 0, "5 EDGE")
    for i, col in enumerate(GREYS):
        s.fill(i * 8, PANEL_TOP, 8, 9, C_SOLID, col)
    s.fill(0, 11, 20, 9, C_BLANK, BLACK)
    s.fill(20, 11, 20, 9, C_SOLID, WHITE)
    s.fill(14, 15, 6, 4, C_SOLID, RED)
    s.fill(20, 15, 6, 4, C_SOLID, BLUE)
    return s


PANELS = [panel_bars, panel_hatch, panel_burst, panel_check, panel_edge]


def screen_inputtest():
    s = Screen()
    s.text(1, 0, "INPUT TEST")
    s.text(1, 2, "JOYSTICK PORT 2", LGREY)
    for name, x, y in (("UP", 6, 5), ("DN", 6, 11), ("LT", 2, 8), ("RT", 10, 8),
                       ("FIRE", 16, 8)):
        s.text(x, y, name, LGREY)
    s.text(1, 15, "RAW", LGREY)
    s.text(1, 17, "UNSEEN", LGREY)
    s.text(1, 20, "PORT 1 IS THE OTHER COLUMN", DGREY)
    for name, x, y in (("UP", 28, 5), ("DN", 28, 11), ("LT", 24, 8), ("RT", 32, 8),
                       ("FIRE", 36, 8)):
        s.text(x, y, name, DGREY)
    return s


def screen_overscan():
    s = Screen()
    s.text(1, 0, "OVERSCAN", WHITE)
    insets = [(8, 5), (16, 10), (24, 15), (32, 20)]

    # Vertical arms first: each lands in its own column, so each can take its
    # own colour.
    cols = [YELLOW, CYAN, GREEN, RED]
    for i, (ix, _) in enumerate(insets):
        for y in range(1, VH - 1):
            s.put(ix // 8, y, C_VLINE + ix % 8, cols[i])
            s.put((SCREEN_W - 1 - ix) // 8, y,
                  C_VLINE + (SCREEN_W - 1 - ix) % 8, cols[i])

    # Horizontal arms. y=5 is row 0 alone and y=20 is row 2 alone, but y=10
    # and y=15 share row 1 - so that row uses a two-line character and one
    # colour for both. Colour RAM is per cell and there is no way round it.
    for x in range(1, VW - 1):
        s.put(x, 0, C_HLINE + 5, cols[0])
        s.put(x, 1, C_HLINE2 + 0, CYAN)          # 5% and 7.5% together
        s.put(x, 2, C_HLINE + 4, cols[3])
        s.put(x, 24, C_HLINE + 2, cols[0])
        s.put(x, 23, C_HLINE2 + 1, CYAN)
        s.put(x, 22, C_HLINE + 3, cols[3])

    for x in range(5, 35):
        long = (x % 4 == 0)
        s.put(x, 4, C_RULE_T6 if long else C_RULE_T, LGREY)
        s.put(x, 21, C_RULE_B6 if long else C_RULE_B, LGREY)
    for y in range(4, 22):
        long = (y % 4 == 0)
        s.put(5, y, C_RULE_L6 if long else C_RULE_L, LGREY)
        s.put(34, y, C_RULE_R6 if long else C_RULE_R, LGREY)

    for i, (ix, iy) in enumerate(insets):
        pct = ["2.5", "5", "7.5", "10"][i]
        s.text(12, 8 + i, f"{pct:>4}% {ix:>2}/{iy:<2} PX", cols[i])
    s.text(12, 6, "INSET", LGREY)
    s.put(19, 13, C_XHAIR, WHITE)
    s.text(16, 15, "320X200", WHITE)
    return s


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    (out / "charset.bin").write_bytes(build_charset())

    scr, col = [], []
    for build in PANELS:
        s = build()
        add_track(s)
        a, b = s.emit()
        scr.append(a)
        col.append(b)
    (out / "testcard_scr.bin").write_bytes(b"".join(scr))
    (out / "testcard_col.bin").write_bytes(b"".join(col))

    for name, build in (("inputtest", screen_inputtest), ("overscan", screen_overscan)):
        a, b = build().emit()
        (out / f"{name}_scr.bin").write_bytes(a)
        (out / f"{name}_col.bin").write_bytes(b)

    print(f"c64: charset 2048, {len(PANELS)} panels of {VW}x{VH}, "
          f"2 single screens -> {out}")


if __name__ == "__main__":
    main()
