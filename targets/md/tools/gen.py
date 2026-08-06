#!/usr/bin/env python3
"""Generate Mega Drive tile data, plane maps and CRAM palettes.

After the NES and Game Boy this platform feels roomy: 16 colours per palette
and a full 16-bit map entry per cell carrying tile, palette, priority and both
flip bits. Every SMPTE colour and an eight-step grey ramp fit in one palette,
so none of the degrading the other targets need happens here.

Colours are 9-bit BGR - three bits a channel, in bits 1..3 of each nibble.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import font  # noqa: E402

VW, VH = 40, 28                   # visible tiles, 320x224
PLANE_W = 64                      # plane is 64 cells wide in VRAM
SCREEN_W, SCREEN_H = 320, 224


def rgb(r, g, b):
    """3 bits a channel, held in bits 1..3 of each nibble."""
    return (b << 9) | (g << 5) | (r << 1)


BLACK = rgb(0, 0, 0)
WHITE = rgb(7, 7, 7)
YELLOW, CYAN, GREEN = rgb(7, 7, 0), rgb(0, 7, 7), rgb(0, 7, 0)
MAGENTA, RED, BLUE = rgb(7, 0, 7), rgb(7, 0, 0), rgb(0, 0, 7)

# Palette 0 carries the whole design: colour 0 is the transparent backdrop,
# 1..7 the SMPTE colours that are not black, and 8..15 an eight-step grey ramp.
# The ramp is the platform's full grey gamut - three bits a channel is eight
# levels and no more.
PAL_MAIN = [BLACK, WHITE, YELLOW, CYAN, GREEN, MAGENTA, RED, BLUE] + \
           [rgb(i, i, i) for i in range(8)]
# Palette 1 is the checkerboard's, so entries 1 and 2 can be swapped every
# frame without touching anything else on screen.
PAL_CHECK = [BLACK, WHITE, BLACK] + [BLACK] * 13
# Palette 2 is the ticker track: dim cells, red decade marks, white marker.
PAL_TRACK = [BLACK, rgb(2, 2, 2), RED, WHITE] + [BLACK] * 12
PAL_SPARE = [BLACK] * 16

PALETTES = [PAL_MAIN, PAL_CHECK, PAL_TRACK, PAL_SPARE]

# Colour indices within PAL_MAIN.
C_WHITE, C_YELLOW, C_CYAN, C_GREEN, C_MAGENTA, C_RED, C_BLUE = 1, 2, 3, 4, 5, 6, 7
SMPTE_IDX = [C_WHITE, C_YELLOW, C_CYAN, C_GREEN, C_MAGENTA, C_RED, C_BLUE, 0]
GREY0 = 8                         # 8..15, darkest to lightest

# --- tile numbers ---------------------------------------------------------
T_SOLID = 0                       # 0..15: solid colour index 0..15
T_STRIPE2, T_STRIPE4, T_STRIPE8 = 16, 17, 18
T_CHECK = 19
T_HATCH_CROSS, T_HATCH_V, T_HATCH_H = 20, 21, 22
T_XHAIR = 23
T_TICKCELL = 24                   # 4px mark at the left of the tile
# Font occupies 0x20..0x5F, indexed by ASCII. Graphics stay clear of it.
T_VLINE = 0x60                    # 0x60..0x67
T_HLINE = 0x68                    # 0x68..0x6F
T_RULE_T, T_RULE_T6 = 0x70, 0x71
T_RULE_B, T_RULE_B6 = 0x72, 0x73
T_RULE_L, T_RULE_L6 = 0x74, 0x75
T_RULE_R, T_RULE_R6 = 0x76, 0x77
# Line tiles in four colours, so the overscan rectangles can be colour-keyed.
# On the NES that was impossible - four colours meeting in one 16x16 attribute
# block - but here the constraint is only tile budget, and there is plenty.
T_LINE_C = 0x80                   # slot*16 + col for vertical, +8+row for horizontal
LINE_COLOURS = (C_YELLOW, C_CYAN, C_GREEN, C_RED)
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
    """8x8 of 0..15 -> 32 bytes, two pixels a byte, high nibble leftmost."""
    out = bytearray()
    for y in range(8):
        for x in range(0, 8, 2):
            out.append((tile[y][x] << 4) | tile[y][x + 1])
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
    tiles[T_CHECK] = check(4, 1, 2)          # palette 1's two entries
    tiles[T_HATCH_CROSS] = hatch(True, True, C_WHITE)
    tiles[T_HATCH_V] = hatch(True, False, C_WHITE)
    tiles[T_HATCH_H] = hatch(False, True, C_WHITE)
    tiles[T_XHAIR] = xhair(C_WHITE)
    tiles[T_TICKCELL] = tickcell(3)          # palette 2 entry 3 = white
    for i in range(8):
        tiles[T_VLINE + i] = vline(i, C_WHITE)
        tiles[T_HLINE + i] = hline(i, C_WHITE)
    tiles[T_RULE_T], tiles[T_RULE_T6] = rule('top', 3, 0, C_WHITE), rule('top', 6, 0, C_WHITE)
    tiles[T_RULE_B], tiles[T_RULE_B6] = rule('bottom', 3, 7, C_WHITE), rule('bottom', 6, 7, C_WHITE)
    tiles[T_RULE_L], tiles[T_RULE_L6] = rule('left', 3, 0, C_WHITE), rule('left', 6, 0, C_WHITE)
    tiles[T_RULE_R], tiles[T_RULE_R6] = rule('right', 3, 7, C_WHITE), rule('right', 6, 7, C_WHITE)
    for slot, colour in enumerate(LINE_COLOURS):
        for i in range(8):
            tiles[T_LINE_C + slot * 16 + i] = vline(i, colour)
            tiles[T_LINE_C + slot * 16 + 8 + i] = hline(i, colour)
    return b"".join(encode(t) for t in tiles)


class Screen:
    """A 40x28 map of 16-bit plane entries.

    One word carries tile, palette, priority and both flip bits, so unlike the
    NES there is no constraint to solve and unlike the Game Boy no second
    attribute plane to keep in step.
    """

    def __init__(self):
        self.cells = [[0] * VW for _ in range(VH)]

    def put(self, x, y, tile, pal=0, prio=0):
        if 0 <= x < VW and 0 <= y < VH:
            self.cells[y][x] = (prio << 15) | (pal << 13) | (tile & 0x7FF)

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
                out += bytes(((c >> 8) & 0xFF, c & 0xFF))   # big-endian
        return bytes(out)


# --- layouts --------------------------------------------------------------
# Row 0 title, rows 2..22 panel, row 26 the frame-ticker track.
PANEL_TOP, PANEL_ROWS = 2, 21
TICK_ROW = 26
P_MAIN, P_CHECK, P_TRACK = 0, 1, 2


def add_track(s):
    """60 cells of 4 pixels = 240 px = 30 tiles, decade marks every 5 tiles.

    Unlike the Game Boy, 4-pixel cells divide the 8-pixel tile exactly, so the
    marks land on tile boundaries and one marked tile does the job.
    """
    for x in range(30):
        s.put(x, TICK_ROW, T_SOLID + 1, P_TRACK)          # dim
        if x % 5 == 0:
            s.put(x, TICK_ROW, T_SOLID + 2, P_TRACK)      # decade mark
    s.put(38, 0, T_SOLID + 1, P_TRACK)                    # parity flash backing


def panel_bars():
    s = Screen()
    s.text(1, 0, "1 BARS")
    # 40 tiles, 8 bars, 5 tiles each - it divides exactly here.
    for i, idx in enumerate(SMPTE_IDX):
        s.fill(i * 5, PANEL_TOP, 5, 14, T_SOLID + idx, P_MAIN)
    # Eight steps, which is the platform's entire grey gamut: three bits a
    # channel is eight levels and no more.
    for i in range(8):
        s.fill(i * 5, 16, 5, 7, T_SOLID + GREY0 + i, P_MAIN)
    return s


def panel_hatch():
    s = Screen()
    s.text(1, 0, "2 HATCH")
    for y in range(PANEL_TOP, PANEL_TOP + PANEL_ROWS):
        for x in range(VW):
            v, h = x % 2 == 0, (y - PANEL_TOP) % 2 == 0
            t = (T_HATCH_CROSS if v and h else T_HATCH_V if v
                 else T_HATCH_H if h else T_SOLID)
            s.put(x, y, t, P_MAIN)
    return s


def panel_burst():
    s = Screen()
    s.text(1, 0, "3 BURST")
    for b, t in enumerate((T_STRIPE2, T_STRIPE4, T_STRIPE8, None)):
        y = PANEL_TOP + b * 5
        if t is None:
            for x in range(VW):
                s.fill(x, y, 1, 5, T_SOLID + (C_WHITE if x % 2 == 0 else 0), P_MAIN)
        else:
            s.fill(0, y, VW, 5, t, P_MAIN)
        s.text(0, y, str(2 ** b), P_MAIN)
    return s


def panel_check():
    s = Screen()
    s.text(1, 0, "4 CHECK")
    s.fill(0, PANEL_TOP, VW, PANEL_ROWS, T_CHECK, P_CHECK)
    return s


def panel_edge():
    s = Screen()
    s.text(1, 0, "5 EDGE")
    for i in range(8):
        s.fill(i * 5, PANEL_TOP, 5, 10, T_SOLID + GREY0 + i, P_MAIN)
    s.fill(0, 12, 20, 11, T_SOLID, P_MAIN)
    s.fill(20, 12, 20, 11, T_SOLID + C_WHITE, P_MAIN)
    s.fill(14, 18, 6, 4, T_SOLID + C_RED, P_MAIN)
    s.fill(20, 18, 6, 4, T_SOLID + C_BLUE, P_MAIN)
    return s


PANELS = [panel_bars, panel_hatch, panel_burst, panel_check, panel_edge]


def screen_inputtest():
    s = Screen()
    s.text(1, 0, "INPUT TEST")
    s.text(1, 2, "HOLD A CONTROL")
    for name, x, y in (("UP", 6, 6), ("DN", 6, 12), ("LT", 2, 9), ("RT", 10, 9),
                       ("A", 24, 11), ("B", 28, 10), ("C", 32, 9),
                       ("START", 16, 14), ("MODE", 16, 16),
                       ("X", 24, 7), ("Y", 28, 6), ("Z", 32, 5)):
        s.text(x, y, name, P_MAIN)
    s.text(1, 20, "RAW", P_MAIN)
    s.text(1, 22, "UNSEEN", P_MAIN)
    return s


def screen_overscan():
    s = Screen()
    s.text(1, 0, "OVERSCAN")
    insets = [(8, 5), (16, 11), (24, 16), (32, 22)]
    for slot, (ix, iy) in enumerate(insets):
        base = T_LINE_C + slot * 16
        for y in range(iy // 8, (SCREEN_H - iy + 7) // 8):
            s.put(ix // 8, y, base + ix % 8, P_MAIN)
            s.put((SCREEN_W - 1 - ix) // 8, y, base + (SCREEN_W - 1 - ix) % 8, P_MAIN)
        for x in range(ix // 8, (SCREEN_W - ix + 7) // 8):
            s.put(x, iy // 8, base + 8 + iy % 8, P_MAIN)
            s.put(x, (SCREEN_H - 1 - iy) // 8, base + 8 + (SCREEN_H - 1 - iy) % 8, P_MAIN)

    # The horizontal insets are tile-aligned but the vertical ones are not, so
    # the ruler gets its own baseline just inside the innermost box rather than
    # sharing its line.
    for x in range(4, 36):
        long = (x % 4 == 0)
        s.put(x, 3, T_RULE_T6 if long else T_RULE_T, P_MAIN)
        s.put(x, 24, T_RULE_B6 if long else T_RULE_B, P_MAIN)
    for y in range(3, 25):
        long = (y % 4 == 0)
        s.put(4, y, T_RULE_L6 if long else T_RULE_L, P_MAIN)
        s.put(35, y, T_RULE_R6 if long else T_RULE_R, P_MAIN)

    for i, (ix, iy) in enumerate(insets):
        pct = ["2.5", "5", "7.5", "10"][i]
        s.text(12, 8 + i * 2, f"{pct:>4}%  {ix:>2}/{iy:<2} PX", P_MAIN)
    s.text(12, 6, "INSET", P_MAIN)
    s.put(19, 16, T_XHAIR, P_MAIN)
    s.text(16, 18, "320X224", P_MAIN)
    return s


def pal_bytes():
    out = bytearray()
    for pal in PALETTES:
        for c in pal:
            out += bytes(((c >> 8) & 0xFF, c & 0xFF))
    return bytes(out)


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

    print(f"md: tiles {NUM_TILES * 32}, {len(PANELS)} panels of {VW}x{VH}, "
          f"2 single screens -> {out}")


if __name__ == "__main__":
    main()
