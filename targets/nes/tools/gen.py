#!/usr/bin/env python3
"""Generate NES CHR-ROM and the nametables for all three programs.

Why this is Python and not assembly tables: the NES colours backgrounds through
an attribute table at 16x16 granularity, three colours plus a shared background
per block. Every layout in this suite has to be checked against that limit, and
checking it by eye in a hand-written table is how NES projects end up with one
wrong block nobody notices. Here the layout is described in colour terms, the
attribute table is *derived*, and a block that needs a fourth colour raises
AttributeError with its coordinates instead of shipping.

Tile indices for text equal the character's ASCII code, so drawing a string is
copying its bytes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import font  # noqa: E402

W, H = 32, 30                     # tiles
SCREEN_W, SCREEN_H = 256, 240

# --- palette --------------------------------------------------------------
# NES colour indices. $0F is the black that stays black on every revision;
# $0D is a "blacker than black" that some displays and capture cards clip, so
# it is never used here.
BLACK, DGREY, LGREY, WHITE = 0x0F, 0x00, 0x10, 0x20
YELLOW, CYAN, GREEN, MAGENTA, RED, BLUE = 0x28, 0x2C, 0x2A, 0x24, 0x16, 0x12

# --- tile numbers ---------------------------------------------------------
T_BLANK = 0
T_SOLID = (1, 2, 3)               # solid colour 1, 2, 3
T_STRIPE2, T_STRIPE4, T_STRIPE8 = 4, 5, 6
T_CHECK = 7
T_HATCH_CROSS, T_HATCH_V, T_HATCH_H = 8, 9, 10
T_TICK3, T_TICK6 = 11, 12         # ruler ticks, from the top edge of the tile
T_TICK3B, T_TICK6B = 13, 14       # ... and from the bottom
T_TICK3L, T_TICK6L = 15, 16       # ... left
T_TICK3R, T_TICK6R = 17, 18       # ... right
# Everything from here up lives ABOVE the font, not below it. Text tiles are
# indexed by ASCII code (0x20..0x5F), so any graphics tile placed in that range
# is silently overwritten when the font is written - which cost an afternoon:
# the crosshair came out as '#', and the ruler ticks as '%' and '+'.
T_VLINE = 0x60                    # 0x60..0x67: vertical line at column 0..7
T_HLINE = 0x68                    # 0x68..0x6F: horizontal line at row 0..7
T_XHAIR = 0x70
# Ruler ticks share a tile with the innermost rectangle's line: at 8x8, a tick
# every 8 pixels means one per tile, and the tile it lands in is already
# carrying that line. Separate tick tiles would have nowhere to go.
T_RULE_T, T_RULE_T6 = 0x71, 0x72  # line on row 0, tick hanging down
T_RULE_B, T_RULE_B6 = 0x73, 0x74  # line on row 7, tick rising
T_RULE_L, T_RULE_L6 = 0x75, 0x76  # line on col 1, tick to the right
T_RULE_R, T_RULE_R6 = 0x77, 0x78  # line on col 6, tick to the left


def blank():
    return [[0] * 8 for _ in range(8)]


def tile_solid(c):
    return [[c] * 8 for _ in range(8)]


def tile_stripe(period, c=1):
    return [[c if (x % period) < period // 2 else 0 for x in range(8)] for _ in range(8)]


def tile_check(size=4, a=1, b=2):
    return [[a if ((x // size) + (y // size)) % 2 == 0 else b
             for x in range(8)] for y in range(8)]


def tile_vline(col, c=3):
    return [[c if x == col else 0 for x in range(8)] for _ in range(8)]


def tile_hline(row, c=3):
    return [[c if y == row else 0 for x in range(8)] for y in range(8)]


def tile_hatch(v=True, h=True, c=3):
    return [[c if ((v and x == 0) or (h and y == 0)) else 0
             for x in range(8)] for y in range(8)]


def tile_tick(length, edge, c=3):
    t = blank()
    for i in range(length):
        if edge == 'top':
            t[i][0] = c
        elif edge == 'bottom':
            t[7 - i][0] = c
        elif edge == 'left':
            t[0][i] = c
        else:
            t[0][7 - i] = c
    return t


def tile_rule(edge, length, pos, c=3):
    """The rectangle's line at row/col `pos`, plus a tick into the interior."""
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


def tile_xhair(c=3):
    t = blank()
    for i in range(8):
        t[3][i] = c
        t[i][3] = c
    return t


def tile_from_font(ch, c=1):
    rows = font.rows_1bpp(ch)
    return [[c if (rows[y] >> (7 - x)) & 1 else 0 for x in range(8)] for y in range(8)]


def encode(tile):
    """8x8 of 0..3 -> 16 bytes, plane 0 then plane 1."""
    lo, hi = [], []
    for y in range(8):
        a = b = 0
        for x in range(8):
            v = tile[y][x]
            a |= (v & 1) << (7 - x)
            b |= ((v >> 1) & 1) << (7 - x)
        lo.append(a)
        hi.append(b)
    return bytes(lo + hi)


def build_chr():
    tiles = [blank() for _ in range(256)]
    for code in font.ascii_range():
        tiles[code] = tile_from_font(chr(code))
    tiles[T_SOLID[0]] = tile_solid(1)
    tiles[T_SOLID[1]] = tile_solid(2)
    tiles[T_SOLID[2]] = tile_solid(3)
    tiles[T_STRIPE2] = tile_stripe(2)
    tiles[T_STRIPE4] = tile_stripe(4)
    tiles[T_STRIPE8] = tile_stripe(8)
    tiles[T_CHECK] = tile_check()
    tiles[T_HATCH_CROSS] = tile_hatch(True, True)
    tiles[T_HATCH_V] = tile_hatch(True, False)
    tiles[T_HATCH_H] = tile_hatch(False, True)
    tiles[T_TICK3], tiles[T_TICK6] = tile_tick(3, 'top'), tile_tick(6, 'top')
    tiles[T_TICK3B], tiles[T_TICK6B] = tile_tick(3, 'bottom'), tile_tick(6, 'bottom')
    tiles[T_TICK3L], tiles[T_TICK6L] = tile_tick(3, 'left'), tile_tick(6, 'left')
    tiles[T_TICK3R], tiles[T_TICK6R] = tile_tick(3, 'right'), tile_tick(6, 'right')
    for i in range(8):
        tiles[T_VLINE + i] = tile_vline(i)
        tiles[T_HLINE + i] = tile_hline(i)
    tiles[T_XHAIR] = tile_xhair()
    # Positions match the innermost rectangle: y=24 and y=215 fall on tile
    # rows 0 and 7, x=25 and x=230 on tile columns 1 and 6.
    tiles[T_RULE_T], tiles[T_RULE_T6] = tile_rule('top', 3, 0), tile_rule('top', 6, 0)
    tiles[T_RULE_B], tiles[T_RULE_B6] = tile_rule('bottom', 3, 7), tile_rule('bottom', 6, 7)
    tiles[T_RULE_L], tiles[T_RULE_L6] = tile_rule('left', 3, 1), tile_rule('left', 6, 1)
    tiles[T_RULE_R], tiles[T_RULE_R6] = tile_rule('right', 3, 6), tile_rule('right', 6, 6)
    # 8 KB: the same 256 tiles in both pattern tables, so sprites and
    # background can each be pointed at either without a second tile set.
    return b"".join(encode(t) for t in tiles) * 2


# --- screens --------------------------------------------------------------


class Screen:
    """A nametable plus the attribute table derived from it.

    A cell records a *demand*: which palette entry it paints with, and what
    colour that entry has to be - e.g. {1: YELLOW} for a tile whose ink is
    index 1 and which wants to come out yellow. The solver then picks, per
    16x16 block, a palette satisfying every demand inside it.

    Stating it as (index -> colour) rather than a bare set of colours is what
    makes the check worth anything: the tile has already committed to an index,
    so a palette that merely contains yellow somewhere is not good enough.
    """

    def __init__(self):
        self.tiles = [[T_BLANK] * W for _ in range(H)]
        self.want = [[dict() for _ in range(W)] for _ in range(H)]

    def put(self, x, y, tile, demand=None):
        if 0 <= x < W and 0 <= y < H:
            self.tiles[y][x] = tile
            if demand:
                self.want[y][x].update(demand)

    def text(self, x, y, s, colour=WHITE):
        for i, ch in enumerate(s.upper()):
            self.put(x + i, y, ord(ch), {1: colour})

    def hrun(self, x, y, n, tile, demand=None):
        for i in range(n):
            self.put(x + i, y, tile, demand)

    def vrun(self, x, y, n, tile, demand=None):
        for i in range(n):
            self.put(x, y + i, tile, demand)

    def fill(self, x, y, w, h, tile, demand=None):
        for j in range(h):
            self.hrun(x, y + j, w, tile, demand)

    def solve_attributes(self, palettes):
        attr = bytearray(64)
        for by in range(0, H, 2):
            for bx in range(0, W, 2):
                need = {}
                for dy in range(2):
                    for dx in range(2):
                        if by + dy < H and bx + dx < W:
                            for idx, col in self.want[by + dy][bx + dx].items():
                                if need.setdefault(idx, col) != col:
                                    raise AttributeError(
                                        f"block at tile ({bx},{by}): palette index "
                                        f"{idx} is wanted as both {need[idx]:#04x} "
                                        f"and {col:#04x}")
                choice = None
                for pi, pal in enumerate(palettes):
                    if all(pal[i - 1] == c for i, c in need.items()):
                        choice = pi
                        break
                if choice is None:
                    raise AttributeError(
                        f"block at tile ({bx},{by}) demands "
                        f"{ {i: f'{c:#04x}' for i, c in need.items()} }; no palette "
                        f"in { [[f'{c:#04x}' for c in p] for p in palettes] } supplies it")
                # An attribute byte covers 32x32 pixels as four 16x16 quadrants.
                attr[(by // 4) * 8 + (bx // 4)] |= \
                    choice << (((by % 4) // 2) * 4 + ((bx % 4) // 2) * 2)
        return bytes(attr)

    def emit(self, palettes):
        nt = bytes(t for row in self.tiles for t in row)
        pal = bytes([BLACK, palettes[i][0], palettes[i][1], palettes[i][2]]
                    for i in range(4)) if False else b"".join(
            bytes([BLACK, p[0], p[1], p[2]]) for p in palettes)
        return nt + self.solve_attributes(palettes), pal


# --- layouts --------------------------------------------------------------
# Row 0 is the status line, rows 2..25 the panel. The motion elements are all
# sprites (see testcard.s): the NES cannot scroll part of a background without
# a mid-frame interrupt, and NROM has none.

PANEL_TOP, PANEL_ROWS = 2, 24


def panel_bars():
    s = Screen()
    s.text(1, 0, "1 BARS")
    bars = [(T_SOLID[0], {1: WHITE}),   (T_SOLID[1], {2: YELLOW}),
            (T_SOLID[2], {3: CYAN}),    (T_SOLID[0], {1: GREEN}),
            (T_SOLID[1], {2: MAGENTA}), (T_SOLID[2], {3: RED}),
            (T_SOLID[0], {1: BLUE}),    (T_BLANK, None)]
    for i, (tile, dem) in enumerate(bars):
        s.fill(i * 4, PANEL_TOP, 4, 16, tile, dem)
    # The NES background palette holds four greys and no more, so the luma
    # staircase is four steps here rather than the sixteen the bitmap targets
    # manage. See ../README.md.
    steps = [(T_BLANK, None), (T_SOLID[2], {3: DGREY}),
             (T_SOLID[1], {2: LGREY}), (T_SOLID[0], {1: WHITE})]
    for i, (tile, dem) in enumerate(steps):
        s.fill(i * 8, 18, 8, 8, tile, dem)
    return s, [(WHITE, YELLOW, CYAN), (GREEN, MAGENTA, RED),
               (BLUE, LGREY, DGREY), (WHITE, LGREY, DGREY)]


def panel_hatch():
    s = Screen()
    s.text(1, 0, "2 HATCH")
    ink = {3: WHITE}
    for y in range(PANEL_TOP, PANEL_TOP + PANEL_ROWS):
        for x in range(W):
            on_v, on_h = x % 2 == 0, (y - PANEL_TOP) % 2 == 0
            if on_v and on_h:
                s.put(x, y, T_HATCH_CROSS, ink)
            elif on_v:
                s.put(x, y, T_HATCH_V, ink)
            elif on_h:
                s.put(x, y, T_HATCH_H, ink)
    return s, [(WHITE, LGREY, WHITE)] * 4


def panel_burst():
    s = Screen()
    s.text(1, 0, "3 BURST")
    ink = {1: WHITE}
    bands = [(T_STRIPE2, "1"), (T_STRIPE4, "2"), (T_STRIPE8, "4"), (None, "8")]
    for b, (tile, label) in enumerate(bands):
        y = PANEL_TOP + b * 6
        if tile is None:                        # 8 on / 8 off is whole tiles
            for x in range(W):
                s.fill(x, y, 1, 6, T_SOLID[0] if x % 2 == 0 else T_BLANK,
                       ink if x % 2 == 0 else None)
        else:
            s.fill(0, y, W, 6, tile, ink)
    return s, [(WHITE, LGREY, DGREY)] * 4


def panel_check():
    s = Screen()
    s.text(1, 0, "4 CHECK")
    # Inverted by rewriting palette 0 entries 1 and 2 in vblank - two bytes,
    # against the GBA's 16 DMA transfers for the same effect.
    s.fill(0, PANEL_TOP, W, PANEL_ROWS, T_CHECK, {1: WHITE, 2: BLACK})
    return s, [(WHITE, BLACK, LGREY), (WHITE, LGREY, DGREY),
               (WHITE, LGREY, DGREY), (WHITE, LGREY, DGREY)]


def panel_edge():
    s = Screen()
    s.text(1, 0, "5 EDGE")
    steps = [(T_BLANK, None), (T_SOLID[2], {3: DGREY}),
             (T_SOLID[1], {2: LGREY}), (T_SOLID[0], {1: WHITE})]
    for i, (tile, dem) in enumerate(steps):
        s.fill(i * 8, PANEL_TOP, 8, 12, tile, dem)
    s.fill(0,  14, 16, 12, T_BLANK, None)
    s.fill(16, 14, 16, 12, T_SOLID[0], {1: WHITE})
    s.fill(10, 20, 6, 4, T_SOLID[1], {2: RED})
    s.fill(16, 20, 6, 4, T_SOLID[2], {3: BLUE})
    return s, [(WHITE, RED, BLUE), (WHITE, LGREY, DGREY),
               (WHITE, LGREY, DGREY), (WHITE, LGREY, DGREY)]


PANELS = [panel_bars, panel_hatch, panel_burst, panel_check, panel_edge]

# Row 27 is the frame-ticker track and row 25.. is clear of every panel, so the
# track is stamped on afterwards rather than repeated in each layout. The
# moving cell itself is a sprite; only the track and its decade marks are
# background.
TICK_ROW = 27


# Palette 3 is reserved on every testcard panel for the track: it needs red and
# dark grey together, which none of the panels' own palettes carry.
TICK_PALETTE = None  # set below, after the colour names exist


def add_ticker_track(s):
    s.hrun(0, TICK_ROW, W, T_SOLID[2], {3: DGREY})
    for i in range(0, 30, 5):                 # every 10 cells = 5 tiles = 40 px
        s.put(i, TICK_ROW, T_SOLID[1], {2: RED})


def screen_inputtest():
    s = Screen()
    s.text(1, 0, "INPUT TEST")
    s.text(1, 2, "HOLD A CONTROL", LGREY)
    # Buttons are boxed here and lit by sprites, so the background never
    # changes and there is no vblank budget question at all.
    layout = [("UP", 5, 8), ("DN", 5, 12), ("LT", 2, 10), ("RT", 8, 10),
              ("SEL", 12, 12), ("STA", 16, 12), ("B", 21, 10), ("A", 25, 10)]
    for pl in range(2):
        oy = pl * 0
        s.text(1 + pl * 16, 5, f"P{pl + 1}", WHITE)
    for name, x, y in layout:
        s.text(x, y, name, LGREY)
    s.text(1, 20, "RAW P1", LGREY)
    s.text(1, 22, "RAW P2", LGREY)
    s.text(1, 25, "UNSEEN", LGREY)
    # Two text palettes: white for headings, light grey for labels. A block
    # holding dim text needs LGREY at index 1, which the white palette has not
    # got - the attribute solver refuses the layout otherwise.
    return s, [(WHITE, LGREY, DGREY), (LGREY, DGREY, WHITE),
               (WHITE, LGREY, DGREY), (WHITE, LGREY, DGREY)]


def screen_overscan():
    s = Screen()
    s.text(1, 0, "OVERSCAN", WHITE)

    # Every rectangle is white. Colour-coding them the way the GBA build does
    # is impossible here: near a corner one 16x16 attribute block contains the
    # vertical arms of two rectangles and the horizontal arms of two others,
    # which is four colours in a block that can hold three. White costs the
    # colour key and keeps the geometry exact, which is the measurement that
    # matters. See ../README.md.
    ink = {3: WHITE}
    insets = [(6, 6), (12, 12), (19, 18), (25, 24)]
    for ix, iy in insets:
        for y in range(iy // 8, (SCREEN_H - iy) // 8):
            s.put(ix // 8, y, T_VLINE + ix % 8, ink)
            s.put((SCREEN_W - 1 - ix) // 8, y, T_VLINE + (SCREEN_W - 1 - ix) % 8, ink)
        for x in range(ix // 8, (SCREEN_W - ix) // 8):
            s.put(x, iy // 8, T_HLINE + iy % 8, ink)
            s.put(x, (SCREEN_H - 1 - iy) // 8, T_HLINE + (SCREEN_H - 1 - iy) % 8, ink)

    # Ruler ticks every 8 pixels, every fourth one doubled, hung off the
    # innermost rectangle - the only one whose lines sit where a tick tile can
    # also carry them.
    ix, iy = insets[3]
    for x in range(ix // 8, (SCREEN_W - ix) // 8):
        long = (x % 4 == 0)
        s.put(x, iy // 8, T_RULE_T6 if long else T_RULE_T, ink)
        s.put(x, (SCREEN_H - 1 - iy) // 8, T_RULE_B6 if long else T_RULE_B, ink)
    for y in range(iy // 8, (SCREEN_H - iy) // 8):
        long = (y % 4 == 0)
        s.put(ix // 8, y, T_RULE_L6 if long else T_RULE_L, ink)
        s.put((SCREEN_W - 1 - ix) // 8, y, T_RULE_R6 if long else T_RULE_R, ink)

    for i, (ix, iy) in enumerate(insets):
        pct = ["2.5%", "5%", "7.5%", "10%"][i]
        s.text(6, 10 + i * 2, f"{pct:<5}{ix:>3}/{iy:<3}PX", WHITE)
    s.text(6, 8, "INSET", LGREY)
    s.put(15, 18, T_XHAIR, ink)
    s.text(12, 20, "256X240", WHITE)
    return s, [(WHITE, LGREY, WHITE), (LGREY, DGREY, WHITE),
               (WHITE, LGREY, WHITE), (WHITE, LGREY, WHITE)]


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)

    (out / "chr.bin").write_bytes(build_chr())

    nts, pals = [], []
    for build in PANELS:
        s, pal = build()
        add_ticker_track(s)
        pal = list(pal)
        pal[3] = (WHITE, RED, DGREY)      # reserved; see add_ticker_track
        nt, p = s.emit(pal)
        nts.append(nt)
        pals.append(p)
    (out / "testcard_nt.bin").write_bytes(b"".join(nts))
    (out / "testcard_pal.bin").write_bytes(b"".join(pals))

    for name, build in (("inputtest", screen_inputtest), ("overscan", screen_overscan)):
        s, pal = build()
        nt, p = s.emit(pal)
        (out / f"{name}_nt.bin").write_bytes(nt)
        (out / f"{name}_pal.bin").write_bytes(p)

    print(f"nes: chr 8192, {len(PANELS)} testcard panels, 2 single screens -> {out}")


if __name__ == "__main__":
    main()
