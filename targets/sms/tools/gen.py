#!/usr/bin/env python3
"""Generate Master System tile data, name tables and CRAM palettes.

256x192 as 32x24 tiles of 8x8, 4 bits per pixel. Colour is 6-bit --BBGGRR:
two bits a channel, so four levels each and 64 colours in total. Every SMPTE
colour is expressible; the grey ramp is four steps, which is all of them.

Tiles are *planar*: four bitplanes interleaved a row at a time, four bytes per
row and 32 per tile. That is the one thing about this VDP worth getting from a
function rather than remembering.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import font  # noqa: E402

VW, VH = 32, 24
SCREEN_W, SCREEN_H = 256, 192


def rgb(r, g, b):
    """Two bits a channel: --BBGGRR."""
    return (b << 4) | (g << 2) | r


BLACK, WHITE = rgb(0, 0, 0), rgb(3, 3, 3)
YELLOW, CYAN, GREEN = rgb(3, 3, 0), rgb(0, 3, 3), rgb(0, 3, 0)
MAGENTA, RED, BLUE = rgb(3, 0, 3), rgb(3, 0, 0), rgb(0, 0, 3)

# Palette 0 holds the whole design. Entry 0 is the backdrop.
PAL_BG = [BLACK, WHITE, YELLOW, CYAN, GREEN, MAGENTA, RED, BLUE] + \
         [rgb(i, i, i) for i in range(4)] + \
         [rgb(1, 1, 1), RED, WHITE, BLACK]
# Palette 1 is sprites: entry 0 is transparent whatever it holds.
PAL_SPR = [BLACK, WHITE, RED, rgb(1, 1, 1)] + [BLACK] * 12

C_WHITE, C_YELLOW, C_CYAN, C_GREEN, C_MAGENTA, C_RED, C_BLUE = 1, 2, 3, 4, 5, 6, 7
SMPTE_IDX = [C_WHITE, C_YELLOW, C_CYAN, C_GREEN, C_MAGENTA, C_RED, C_BLUE, 0]
GREY0 = 8                          # 8..11, darkest to lightest
C_DIM = 12
C_TRACKRED = 13

# --- tile numbers ---------------------------------------------------------
T_SOLID = 0                        # 0..15: solid colour index 0..15
T_STRIPE2, T_STRIPE4, T_STRIPE8 = 16, 17, 18
T_CHECK = 19
T_HATCH_CROSS, T_HATCH_V, T_HATCH_H = 20, 21, 22
T_XHAIR = 23
T_TICKCELL = 24
# Font at 0x20..0x5F, indexed by ASCII, as on every other target.
T_RULE_T, T_RULE_T6 = 0x60, 0x61
T_RULE_B, T_RULE_B6 = 0x62, 0x63
T_RULE_L, T_RULE_L6 = 0x64, 0x65
T_RULE_R, T_RULE_R6 = 0x66, 0x67
T_LINE_C = 0x70                    # slot*16 + col vertical, +8+row horizontal
LINE_COLOURS = (C_YELLOW, C_CYAN, C_GREEN, C_RED)
T_HLINE2 = 0xB0                    # two horizontal lines, each its own colour
NUM_TILES = 0xC0


def blank():
    return [[0] * 8 for _ in range(8)]


def solid(c):
    return [[c] * 8 for _ in range(8)]


def stripe(period, c):
    return [[c if (x % period) < period // 2 else 0 for x in range(8)] for _ in range(8)]


def check(size, a, b):
    return [[a if ((x // size) + (y // size)) % 2 == 0 else b
             for x in range(8)] for y in range(8)]


def hatch(v, h, c):
    return [[c if ((v and x == 0) or (h and y == 0)) else 0
             for x in range(8)] for y in range(8)]


def vline(col, c):
    return [[c if x == col else 0 for x in range(8)] for _ in range(8)]


def hline(row, c):
    return [[c if y == row else 0 for x in range(8)] for y in range(8)]


def hline2(ra, ca, rb, cb):
    """Two rows in one tile, each with its own colour index.

    The 5% and 7.5% horizontal insets both land in tile row 1. On the C64 that
    forced the two rectangles to share a colour, because colour RAM is one
    entry per cell; here a tile is four bits per pixel, so the two lines simply
    take different indices and stay colour-keyed.
    """
    t = blank()
    for x in range(8):
        t[ra][x] = ca
        t[rb][x] = cb
    return t


def rule(edge, length, pos, c):
    t = blank()
    step = 1 if edge in ('top', 'left') else -1
    if edge in ('top', 'bottom'):
        for x in range(8):
            t[pos][x] = c
        for i in range(1, length + 1):
            if 0 <= pos + i * step < 8:
                t[pos + i * step][0] = c
    else:
        for y in range(8):
            t[y][pos] = c
        for i in range(1, length + 1):
            if 0 <= pos + i * step < 8:
                t[0][pos + i * step] = c
    return t


def xhair(c):
    t = blank()
    for i in range(8):
        t[3][i] = c
        t[i][3] = c
    return t


def tickcell(c):
    return [[c if x < 4 else 0 for x in range(8)] for _ in range(8)]


def glyph(ch, c):
    rows = font.rows_1bpp(ch)
    return [[c if (rows[y] >> (7 - x)) & 1 else 0 for x in range(8)] for y in range(8)]


def encode(tile):
    """8x8 of 0..15 -> 32 bytes: four bitplanes interleaved, a row at a time."""
    out = bytearray()
    for y in range(8):
        for plane in range(4):
            b = 0
            for x in range(8):
                if (tile[y][x] >> plane) & 1:
                    b |= 0x80 >> x
            out.append(b)
    return bytes(out)


def build_tiles():
    tiles = [blank() for _ in range(NUM_TILES)]
    for code in font.ascii_range():          # font first, so a collision shows
        tiles[code] = glyph(chr(code), C_WHITE)
    for i in range(16):
        tiles[T_SOLID + i] = solid(i)
    tiles[T_STRIPE2] = stripe(2, C_WHITE)
    tiles[T_STRIPE4] = stripe(4, C_WHITE)
    tiles[T_STRIPE8] = stripe(8, C_WHITE)
    tiles[T_CHECK] = check(4, 1, 14)         # entries 1 and 14, swapped to invert
    tiles[T_HATCH_CROSS] = hatch(True, True, C_WHITE)
    tiles[T_HATCH_V] = hatch(True, False, C_WHITE)
    tiles[T_HATCH_H] = hatch(False, True, C_WHITE)
    tiles[T_XHAIR] = xhair(C_WHITE)
    tiles[T_TICKCELL] = tickcell(1)
    tiles[T_RULE_T], tiles[T_RULE_T6] = rule('top', 3, 0, C_WHITE), rule('top', 6, 0, C_WHITE)
    tiles[T_RULE_B], tiles[T_RULE_B6] = rule('bottom', 3, 7, C_WHITE), rule('bottom', 6, 7, C_WHITE)
    tiles[T_RULE_L], tiles[T_RULE_L6] = rule('left', 3, 0, C_WHITE), rule('left', 6, 0, C_WHITE)
    tiles[T_RULE_R], tiles[T_RULE_R6] = rule('right', 3, 7, C_WHITE), rule('right', 6, 7, C_WHITE)
    for slot, colour in enumerate(LINE_COLOURS):
        for i in range(8):
            tiles[T_LINE_C + slot * 16 + i] = vline(i, colour)
            tiles[T_LINE_C + slot * 16 + 8 + i] = hline(i, colour)
    # y=9 and y=14 are both in tile row 1; y=182 and y=177 both in row 22.
    tiles[T_HLINE2 + 0] = hline2(1, C_CYAN, 6, C_GREEN)
    tiles[T_HLINE2 + 1] = hline2(1, C_GREEN, 6, C_CYAN)
    return b"".join(encode(t) for t in tiles)


def pal_bytes():
    return bytes(PAL_BG) + bytes(PAL_SPR)


class Screen:
    """A 32x24 name table of 16-bit entries.

    Bit 11 selects the palette, so only two are reachable per tile - but four
    bits per pixel means one tile can hold several colours from its palette,
    which is what keeps the overscan rectangles keyed.
    """

    def __init__(self):
        self.cells = [[0] * VW for _ in range(VH)]

    def put(self, x, y, tile, pal=0, prio=0):
        if 0 <= x < VW and 0 <= y < VH:
            self.cells[y][x] = (prio << 12) | (pal << 11) | (tile & 0x1FF)

    def text(self, x, y, s, pal=0):
        for i, ch in enumerate(s.upper()):
            self.put(x + i, y, ord(ch), pal)

    def fill(self, x, y, w, h, tile, pal=0):
        for j in range(h):
            for i in range(w):
                self.put(x + i, y + j, tile, pal)

    def emit(self):
        out = bytearray()
        for row in self.cells:
            for c in row:
                out += bytes((c & 0xFF, (c >> 8) & 0xFF))   # little-endian
        return bytes(out)


# --- layouts --------------------------------------------------------------
PANEL_TOP, PANEL_ROWS = 2, 17
TICK_ROW = 22


def add_track(s):
    """60 cells of 4 pixels = 240 px = 30 tiles, decade marks every 5."""
    for x in range(30):
        s.put(x, TICK_ROW, T_SOLID + C_DIM)
        if x % 5 == 0:
            s.put(x, TICK_ROW, T_SOLID + C_TRACKRED)
    s.put(30, 0, T_SOLID + C_DIM)          # parity flash backing


def panel_bars():
    s = Screen()
    s.text(1, 0, "1 BARS")
    for i, idx in enumerate(SMPTE_IDX):    # 32 tiles, 8 bars, 4 each
        s.fill(i * 4, PANEL_TOP, 4, 11, T_SOLID + idx)
    for i in range(4):                     # four greys, which is all of them
        s.fill(i * 8, 14, 8, 5, T_SOLID + GREY0 + i)
    return s


def panel_hatch():
    s = Screen()
    s.text(1, 0, "2 HATCH")
    for y in range(PANEL_TOP, PANEL_TOP + PANEL_ROWS):
        for x in range(VW):
            v, h = x % 2 == 0, (y - PANEL_TOP) % 2 == 0
            t = (T_HATCH_CROSS if v and h else T_HATCH_V if v
                 else T_HATCH_H if h else T_SOLID)
            s.put(x, y, t)
    return s


def panel_burst():
    s = Screen()
    s.text(1, 0, "3 BURST")
    for b, t in enumerate((T_STRIPE2, T_STRIPE4, T_STRIPE8, None)):
        y = PANEL_TOP + b * 4
        if t is None:
            for x in range(VW):
                s.fill(x, y, 1, 4, T_SOLID + (C_WHITE if x % 2 == 0 else 0))
        else:
            s.fill(0, y, VW, 4, t)
        s.text(0, y, str(2 ** b))
    return s


def panel_check():
    s = Screen()
    s.text(1, 0, "4 CHECK")
    s.fill(0, PANEL_TOP, VW, PANEL_ROWS, T_CHECK)
    return s


def panel_edge():
    s = Screen()
    s.text(1, 0, "5 EDGE")
    for i in range(4):
        s.fill(i * 8, PANEL_TOP, 8, 8, T_SOLID + GREY0 + i)
    s.fill(0, 11, 16, 8, T_SOLID)
    s.fill(16, 11, 16, 8, T_SOLID + C_WHITE)
    s.fill(11, 14, 5, 3, T_SOLID + C_RED)
    s.fill(16, 14, 5, 3, T_SOLID + C_BLUE)
    return s


PANELS = [panel_bars, panel_hatch, panel_burst, panel_check, panel_edge]


def screen_inputtest():
    s = Screen()
    s.text(1, 0, "INPUT TEST")
    for name, x, y in (("UP", 5, 5), ("DN", 5, 11), ("LT", 1, 8), ("RT", 9, 8),
                       ("1", 16, 8), ("2", 20, 8)):
        s.text(x, y, name)
    s.text(1, 14, "RAW")
    s.text(1, 16, "UNSEEN")
    s.text(1, 19, "PORT 2 IS THE RIGHT COLUMN")
    for name, x, y in (("UP", 25, 5), ("DN", 25, 11), ("LT", 23, 8), ("RT", 27, 8)):
        s.text(x, y, name)
    return s


def screen_overscan():
    s = Screen()
    s.text(1, 0, "OVERSCAN")
    insets = [(6, 4), (12, 9), (19, 14), (25, 19)]

    for slot, (ix, _) in enumerate(insets):
        base = T_LINE_C + slot * 16
        for y in range(1, VH - 1):
            s.put(ix // 8, y, base + ix % 8)
            s.put((SCREEN_W - 1 - ix) // 8, y, base + (SCREEN_W - 1 - ix) % 8)

    # Horizontal arms. y=4 is tile row 0 and y=19 is row 2, each alone; y=9 and
    # y=14 share row 1, so that row uses a two-line tile - and unlike the C64,
    # four bits per pixel let the two lines keep separate colours.
    for x in range(1, VW - 1):
        s.put(x, 0, T_LINE_C + 0 * 16 + 8 + 4)
        s.put(x, 1, T_HLINE2 + 0)
        s.put(x, 2, T_LINE_C + 3 * 16 + 8 + 3)
        s.put(x, 23, T_LINE_C + 0 * 16 + 8 + 3)
        s.put(x, 22, T_HLINE2 + 1)
        s.put(x, 21, T_LINE_C + 3 * 16 + 8 + 4)

    for x in range(4, 28):
        long = (x % 4 == 0)
        s.put(x, 3, T_RULE_T6 if long else T_RULE_T)
        s.put(x, 20, T_RULE_B6 if long else T_RULE_B)
    for y in range(3, 21):
        long = (y % 4 == 0)
        s.put(3, y, T_RULE_L6 if long else T_RULE_L)
        s.put(28, y, T_RULE_R6 if long else T_RULE_R)

    for i, (ix, iy) in enumerate(insets):
        pct = ["2.5", "5", "7.5", "10"][i]
        s.text(9, 7 + i * 2, f"{pct:>4}% {ix:>2}/{iy:<2}PX")
    s.text(9, 5, "INSET")
    s.put(15, 12, T_XHAIR)
    s.text(12, 14, "256X192")
    return s


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    (out / "tiles.bin").write_bytes(build_tiles())
    (out / "palettes.bin").write_bytes(pal_bytes())

    maps = []
    for build in PANELS:
        s = build()
        add_track(s)
        maps.append(s.emit())
    (out / "testcard_map.bin").write_bytes(b"".join(maps))

    for name, build in (("inputtest", screen_inputtest), ("overscan", screen_overscan)):
        (out / f"{name}_map.bin").write_bytes(build().emit())

    print(f"sms: tiles {NUM_TILES * 32}, {len(PANELS)} panels of {VW}x{VH}, "
          f"2 single screens -> {out}")


if __name__ == "__main__":
    main()
