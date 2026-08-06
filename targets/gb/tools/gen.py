#!/usr/bin/env python3
"""Generate Game Boy tile data, tilemaps and Game Boy Color palettes.

The ROM is CGB-enhanced but DMG-compatible, which is the only honest way to
build a colour test card for this platform: a DMG has four greys and no more.

The trick that makes one layout serve both is in the colour bars. Bar i uses
the *tile* whose ink is colour index (i mod 4), and CGB palette i, whose entry
(i mod 4) is set to SMPTE colour i. On a Game Boy Color that is eight distinct
colours; on a DMG, where the attribute map is ignored entirely, it degrades to
the four shades 0,1,2,3 repeated - which is the DMG's whole gamut, with
adjacent bars still distinguishable. Nothing has to be drawn twice.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import font  # noqa: E402

VW, VH = 20, 18                   # visible tiles, 160x144
SCREEN_W, SCREEN_H = 160, 144

# --- CGB colours, BGR555 --------------------------------------------------
def rgb(r, g, b):
    return r | (g << 5) | (b << 10)

WHITE, BLACK = rgb(31, 31, 31), rgb(0, 0, 0)
LGREY, DGREY = rgb(21, 21, 21), rgb(10, 10, 10)
YELLOW, CYAN, GREEN = rgb(31, 31, 0), rgb(0, 31, 31), rgb(0, 31, 0)
MAGENTA, RED, BLUE = rgb(31, 0, 31), rgb(31, 0, 0), rgb(0, 0, 31)

SMPTE = [WHITE, YELLOW, CYAN, GREEN, MAGENTA, RED, BLUE, BLACK]

# --- tiles ----------------------------------------------------------------
T_SOLID = (0, 1, 2, 3)            # solid colour index 0..3
T_STRIPE2, T_STRIPE4, T_STRIPE8 = 4, 5, 6
T_CHECK = 7
T_HATCH_CROSS, T_HATCH_V, T_HATCH_H = 8, 9, 10
T_TICKCELL = 11                   # 2px mark at the left of the tile
T_XHAIR = 12
T_SPLIT01, T_SPLIT23 = 13, 14     # colour change halfway across the tile
T_TRACK, T_TRACK_M0, T_TRACK_M4 = 15, 16, 17
T_VLINE = 0x60                    # 0x60..0x67, line at column 0..7
T_HLINE = 0x68                    # 0x68..0x6F, line at row 0..7
T_RULE_T, T_RULE_T6 = 0x70, 0x71
T_RULE_B, T_RULE_B6 = 0x72, 0x73
T_RULE_L, T_RULE_L6 = 0x74, 0x75
T_RULE_R, T_RULE_R6 = 0x76, 0x77
# Font tiles are indexed by ASCII (0x20..0x5F). Graphics stay clear of that
# range - see targets/nes/README.md for what happens when they do not.


def blank():
    return [[0] * 8 for _ in range(8)]


def solid(c):
    return [[c] * 8 for _ in range(8)]


def stripe(period, c=3):
    return [[c if (x % period) < period // 2 else 0 for x in range(8)] for _ in range(8)]


def check(size=4, a=3, b=0):
    return [[a if ((x // size) + (y // size)) % 2 == 0 else b
             for x in range(8)] for y in range(8)]


def hatch(v=True, h=True, c=3):
    return [[c if ((v and x == 0) or (h and y == 0)) else 0
             for x in range(8)] for y in range(8)]


def vline(col, c=3):
    return [[c if x == col else 0 for x in range(8)] for _ in range(8)]


def hline(row, c=3):
    return [[c if y == row else 0 for x in range(8)] for y in range(8)]


def rule(edge, length, pos, c=3):
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


def tickcell(c=3):
    return [[c if x < 2 else 0 for x in range(8)] for _ in range(8)]


def split(a, b):
    """Left half colour a, right half colour b.

    160 pixels does not divide by 8 bars into whole tiles - each bar is 20px,
    so every other bar boundary lands in the middle of a tile. This is that
    boundary.
    """
    return [[a if x < 4 else b for x in range(8)] for _ in range(8)]


def track(mark_at=None):
    t = [[1] * 8 for _ in range(8)]
    if mark_at is not None:
        for y in range(8):
            t[y][mark_at] = 2
            t[y][mark_at + 1] = 2
    return t


def xhair(c=3):
    t = blank()
    for i in range(8):
        t[3][i] = c
        t[i][3] = c
    return t


def glyph(ch, c=3):
    rows = font.rows_1bpp(ch)
    return [[c if (rows[y] >> (7 - x)) & 1 else 0 for x in range(8)] for y in range(8)]


def encode(tile):
    """8x8 of 0..3 -> 16 bytes, low and high bitplane interleaved per row."""
    out = bytearray()
    for y in range(8):
        lo = hi = 0
        for x in range(8):
            v = tile[y][x]
            lo |= (v & 1) << (7 - x)
            hi |= ((v >> 1) & 1) << (7 - x)
        out += bytes((lo, hi))
    return bytes(out)


def build_tiles():
    tiles = [blank() for _ in range(256)]
    for code in font.ascii_range():          # font first, so a collision shows
        tiles[code] = glyph(chr(code))
    for i in range(4):
        tiles[T_SOLID[i]] = solid(i)
    tiles[T_STRIPE2], tiles[T_STRIPE4], tiles[T_STRIPE8] = stripe(2), stripe(4), stripe(8)
    tiles[T_CHECK] = check()
    tiles[T_HATCH_CROSS] = hatch(True, True)
    tiles[T_HATCH_V] = hatch(True, False)
    tiles[T_HATCH_H] = hatch(False, True)
    tiles[T_TICKCELL] = tickcell()
    tiles[T_XHAIR] = xhair()
    tiles[T_SPLIT01], tiles[T_SPLIT23] = split(0, 1), split(2, 3)
    tiles[T_TRACK] = track()
    tiles[T_TRACK_M0], tiles[T_TRACK_M4] = track(0), track(4)
    for i in range(8):
        tiles[T_VLINE + i] = vline(i)
        tiles[T_HLINE + i] = hline(i)
    tiles[T_RULE_T], tiles[T_RULE_T6] = rule('top', 3, 0), rule('top', 6, 0)
    tiles[T_RULE_B], tiles[T_RULE_B6] = rule('bottom', 3, 7), rule('bottom', 6, 7)
    tiles[T_RULE_L], tiles[T_RULE_L6] = rule('left', 3, 0), rule('left', 6, 0)
    tiles[T_RULE_R], tiles[T_RULE_R6] = rule('right', 3, 7), rule('right', 6, 7)
    return b"".join(encode(t) for t in tiles)


# --- screens --------------------------------------------------------------
class Screen:
    """A 20x18 tilemap plus a CGB attribute map.

    CGB attributes are per tile, not per 16x16 block as on the NES, so there is
    no constraint to solve here - a cell simply names its palette.
    """

    def __init__(self):
        # Default cells are colour index 0 on palette 7, whose entry 0 is
        # black. Defaulting to palette 0 made the surround take whatever entry
        # 0 that panel happened to use - white, on the colour bars.
        self.tiles = [[T_SOLID[0]] * VW for _ in range(VH)]
        self.attr = [[7] * VW for _ in range(VH)]

    def put(self, x, y, tile, pal=0):
        if 0 <= x < VW and 0 <= y < VH:
            self.tiles[y][x] = tile
            self.attr[y][x] = pal

    def text(self, x, y, s, pal=7):
        for i, ch in enumerate(s.upper()):
            self.put(x + i, y, ord(ch), pal)

    def fill(self, x, y, w, h, tile, pal=0):
        for j in range(h):
            for i in range(w):
                self.put(x + i, y + j, tile, pal)

    def emit(self):
        return (bytes(t for r in self.tiles for t in r),
                bytes(a for r in self.attr for a in r))


def pal_bytes(palettes):
    """8 palettes x 4 colours, little-endian BGR555."""
    out = bytearray()
    for p in palettes:
        for c in p:
            out += bytes((c & 0xFF, (c >> 8) & 0xFF))
    return bytes(out)


GREYS = (BLACK, DGREY, LGREY, WHITE)
# Palette 7 is the text palette on every screen: index 3 is white so a glyph,
# whose ink is index 3, comes out white without any per-screen thought.
TEXT_PAL = (BLACK, DGREY, LGREY, WHITE)


# --- layouts --------------------------------------------------------------
# Row 0 title, rows 2..14 panel, row 17 the frame-ticker track. The moving
# marker, the 1px/frame bar and the parity flash are sprites.
PANEL_TOP, PANEL_ROWS = 2, 13
TICK_ROW = 17
PAL_GREY, PAL_CHECK, PAL_TEXT = 6, 5, 7
PAL_TRACK = 4


def add_track(s):
    """60 cells of 2 pixels; decade marks every 10 cells, i.e. every 20 px.

    20 px against an 8 px tile repeats every 5 tiles, with marks landing at
    column 0 of the first tile and column 4 of the third. That is why there are
    two marked track tiles rather than one.
    """
    for x in range(15):                       # 15 tiles = 120 px = 60 cells
        m = x % 5
        t = T_TRACK_M0 if m == 0 else T_TRACK_M4 if m == 2 else T_TRACK
        s.put(x, TICK_ROW, t, PAL_TRACK)
    # A fixed grey box behind the parity flash. Without it the dark half of the
    # cycle is invisible and "inverting every frame" cannot be told apart from
    # "not being drawn".
    s.put(19, 0, T_SOLID[1], PAL_TRACK)


def panel_bars():
    s = Screen()
    s.text(1, 0, "1 BARS")
    # Five tiles per pair of bars: solid, solid, split, solid, solid.
    for p in range(4):
        a, b = (2 * p) % 4, (2 * p + 1) % 4
        sp = T_SPLIT01 if a == 0 else T_SPLIT23
        cols = [T_SOLID[a], T_SOLID[a], sp, T_SOLID[b], T_SOLID[b]]
        for i, t in enumerate(cols):
            s.fill(p * 5 + i, PANEL_TOP, 1, 9, t, p)
    for i in range(4):                        # four-step staircase, all a DMG has
        s.fill(i * 5, 11, 5, 4, T_SOLID[i], PAL_GREY)

    pals = [(BLACK,) * 4] * 8
    pals = [list(p) for p in pals]
    for p in range(4):
        a, b = (2 * p) % 4, (2 * p + 1) % 4
        pals[p][a] = SMPTE[2 * p]
        pals[p][b] = SMPTE[2 * p + 1]
    return s, pals


def panel_hatch():
    s = Screen()
    s.text(1, 0, "2 HATCH")
    for y in range(PANEL_TOP, PANEL_TOP + PANEL_ROWS):
        for x in range(VW):
            v, h = x % 2 == 0, (y - PANEL_TOP) % 2 == 0
            t = (T_HATCH_CROSS if v and h else T_HATCH_V if v
                 else T_HATCH_H if h else T_SOLID[0])
            s.put(x, y, t, PAL_TEXT)
    return s, None


def panel_burst():
    s = Screen()
    s.text(1, 0, "3 BURST")
    for b, t in enumerate((T_STRIPE2, T_STRIPE4, T_STRIPE8, None)):
        y = PANEL_TOP + b * 3
        if t is None:                          # 8 on / 8 off is whole tiles
            for x in range(VW):
                s.fill(x, y, 1, 4, T_SOLID[3] if x % 2 == 0 else T_SOLID[0], PAL_TEXT)
        else:
            s.fill(0, y, VW, 3, t, PAL_TEXT)
    return s, None


def panel_check():
    s = Screen()
    s.text(1, 0, "4 CHECK")
    s.fill(0, PANEL_TOP, VW, PANEL_ROWS, T_CHECK, PAL_CHECK)
    return s, None


def panel_edge():
    s = Screen()
    s.text(1, 0, "5 EDGE")
    for i in range(4):
        s.fill(i * 5, PANEL_TOP, 5, 6, T_SOLID[i], PAL_GREY)
    s.fill(0, 8, 10, 7, T_SOLID[0], PAL_GREY)     # black
    s.fill(10, 8, 10, 7, T_SOLID[3], PAL_GREY)    # white
    pals = [list((BLACK,) * 4) for _ in range(8)]
    pals[0] = [RED, RED, RED, RED]
    s.fill(6, 11, 4, 3, T_SOLID[0], 0)
    pals[1] = [BLUE, BLUE, BLUE, BLUE]
    s.fill(10, 11, 4, 3, T_SOLID[0], 1)
    return s, pals


PANELS = [panel_bars, panel_hatch, panel_burst, panel_check, panel_edge]


def screen_inputtest():
    s = Screen()
    s.text(1, 0, "INPUT TEST")
    for name, x, y in (("UP", 3, 4), ("DN", 3, 8), ("LT", 1, 6), ("RT", 5, 6),
                       ("SEL", 8, 9), ("STA", 12, 9), ("B", 15, 6), ("A", 18, 6)):
        s.text(x, y, name, PAL_TEXT)
    s.text(1, 12, "RAW", PAL_TEXT)
    s.text(1, 14, "UNSEEN", PAL_TEXT)
    return s, None


def screen_overscan():
    s = Screen()
    s.text(1, 0, "OVERSCAN", PAL_TEXT)
    insets = [(4, 3), (8, 7), (12, 10), (16, 14)]
    for ix, iy in insets:
        for y in range(iy // 8, (SCREEN_H - iy + 7) // 8):
            s.put(ix // 8, y, T_VLINE + ix % 8, PAL_TEXT)
            s.put((SCREEN_W - 1 - ix) // 8, y, T_VLINE + (SCREEN_W - 1 - ix) % 8, PAL_TEXT)
        for x in range(ix // 8, (SCREEN_W - ix + 7) // 8):
            s.put(x, iy // 8, T_HLINE + iy % 8, PAL_TEXT)
            s.put(x, (SCREEN_H - 1 - iy) // 8, T_HLINE + (SCREEN_H - 1 - iy) % 8, PAL_TEXT)

    # On a 20-tile-wide screen the four insets land two to a tile, so ticks
    # cannot share a rectangle's line the way they do on the NES. The ruler
    # gets its own baseline just inside the innermost box instead.
    for x in range(2, 18):
        long = (x % 4 == 0)
        s.put(x, 2, T_RULE_T6 if long else T_RULE_T, PAL_TEXT)
        s.put(x, 15, T_RULE_B6 if long else T_RULE_B, PAL_TEXT)
    for y in range(2, 16):
        long = (y % 4 == 0)
        s.put(2, y, T_RULE_L6 if long else T_RULE_L, PAL_TEXT)
        s.put(17, y, T_RULE_R6 if long else T_RULE_R, PAL_TEXT)

    for i, (ix, iy) in enumerate(insets):
        pct = ["2.5", "5", "7.5", "10"][i]
        s.text(4, 5 + i, f"{pct:>4}% {ix:>2}/{iy:<2}", PAL_TEXT)
    s.put(9, 10, T_XHAIR, PAL_TEXT)
    s.text(6, 12, "160X144", PAL_TEXT)
    return s, None


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    (out / "tiles.bin").write_bytes(build_tiles())

    def finish(s, pals):
        base = [list((BLACK,) * 4) for _ in range(8)]
        if pals:
            base = [list(p) for p in pals]
        base[PAL_GREY] = list(GREYS)
        base[PAL_TEXT] = list(TEXT_PAL)
        base[PAL_TRACK] = [BLACK, DGREY, RED, WHITE]
        base[PAL_CHECK] = [BLACK, DGREY, LGREY, WHITE]
        return s.emit(), pal_bytes(base)

    maps, attrs, pals = [], [], []
    for build in PANELS:
        s, p = build()
        add_track(s)
        (m, a), pb = finish(s, p)
        maps.append(m)
        attrs.append(a)
        pals.append(pb)
    (out / "testcard_map.bin").write_bytes(b"".join(maps))
    (out / "testcard_attr.bin").write_bytes(b"".join(attrs))
    (out / "testcard_pal.bin").write_bytes(b"".join(pals))

    for name, build in (("inputtest", screen_inputtest), ("overscan", screen_overscan)):
        s, p = build()
        (m, a), pb = finish(s, p)
        (out / f"{name}_map.bin").write_bytes(m)
        (out / f"{name}_attr.bin").write_bytes(a)
        (out / f"{name}_pal.bin").write_bytes(pb)

    print(f"gb: tiles 4096, {len(PANELS)} panels of {VW}x{VH}, 2 single screens -> {out}")


if __name__ == "__main__":
    main()
