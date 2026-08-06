#!/usr/bin/env python3
"""Generate Atari 2600 playfield tables, one triple of bytes per scanline.

The playfield is twenty bits across the left half of the screen, four pixels
each, and CTRLPF bit 0 mirrors it into the right half. So the horizontal grid
is 4 pixels and it is symmetric by construction - which suits nested insets
exactly, and suits nothing else in this suite at all.

Bit order is not uniform, which is the trap: PF0 runs 4..7 left to right, PF1
runs 7..0, and PF2 runs 0..7. bit_for() is the only place that knows.
"""

import sys
from pathlib import Path

VISIBLE = 192
PF_BITS = 20                      # 20 x 4 = 80 pixels, mirrored to 160
SCREEN_W, SCREEN_H = 160, 192


def bit_for(index):
    """Playfield bit `index` (0..19, left to right) -> (register, bit)."""
    if index < 4:
        return 0, 4 + index               # PF0: bits 4..7
    if index < 12:
        return 1, 7 - (index - 4)         # PF1: bits 7..0
    return 2, index - 12                  # PF2: bits 0..7


class Field:
    def __init__(self):
        self.rows = [[0, 0, 0] for _ in range(VISIBLE)]

    def set(self, index, y):
        if 0 <= y < VISIBLE and 0 <= index < PF_BITS:
            reg, bit = bit_for(index)
            self.rows[y][reg] |= 1 << bit

    def hline(self, y, first=0, last=PF_BITS - 1):
        for i in range(first, last + 1):
            self.set(i, y)

    def vline(self, index, y0, y1):
        for y in range(y0, y1 + 1):
            self.set(index, y)

    def emit(self):
        return tuple(bytes(r[i] for r in self.rows) for i in range(3))


def overscan():
    f = Field()
    # Insets are 4, 8, 12 and 16 pixels horizontally - which is playfield bits
    # 1, 2, 3 and 4, i.e. *adjacent*. Drawing all four vertical arms produces
    # one solid 16-pixel band, not four rectangles, because the playfield grid
    # is 4 pixels and the insets are 4 pixels apart.
    #
    # So only the two separable ones get vertical arms: 2.5% at bit 1 and 10%
    # at bit 4, with bits 2 and 3 left clear between them. All four horizontal
    # rules are drawn, because vertically there is no such limit - a playfield
    # register can change on any scanline, so 5, 10, 14 and 19 land exactly.
    for idx, y in ((1, 5), (2, 10), (3, 14), (4, 19)):
        f.hline(y, idx, PF_BITS - 1)
        f.hline(VISIBLE - 1 - y, idx, PF_BITS - 1)
    for idx, y in ((1, 5), (4, 19)):
        f.vline(idx, y, VISIBLE - 1 - y)

    # Ruler ticks every 8 pixels - two playfield bits - along the top and
    # bottom just inside the innermost rectangle, every fourth one doubled.
    for i in range(5, PF_BITS):
        if i % 2 == 0:
            length = 6 if i % 4 == 0 else 3
            for d in range(length):
                f.set(i, 22 + d)
                f.set(i, VISIBLE - 23 - d)
    return f


def panel_hatch():
    f = Field()
    for i in range(0, PF_BITS, 4):          # a vertical line every 16 pixels
        f.vline(i, 0, VISIBLE - 1)
    for y in range(0, VISIBLE, 16):         # and a horizontal one every 16 lines
        f.hline(y)
    return f


def panel_burst():
    """Pitches of 1, 2, 4 and 8 playfield bits: 8, 16, 32 and 64 pixels.

    The finest burst the other targets carry is one pixel. Here the playfield
    grid is four, so the finest possible is an 8-pixel pair - which is the
    honest statement of this machine's horizontal resolution.
    """
    f = Field()
    band = VISIBLE // 4
    for b, pitch in enumerate((1, 2, 4, 8)):
        for y in range(b * band, (b + 1) * band):
            for i in range(PF_BITS):
                if (i // pitch) % 2 == 0:
                    f.set(i, y)
    return f


def panel_check():
    f = Field()
    for y in range(VISIBLE):
        for i in range(PF_BITS):
            if ((i // 2) + (y // 16)) % 2 == 0:
                f.set(i, y)
    return f


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    for name, build in (("overscan", overscan), ("hatch", panel_hatch),
                        ("burst", panel_burst), ("check", panel_check)):
        pf0, pf1, pf2 = build().emit()
        (out / f"{name}_pf0.bin").write_bytes(pf0)
        (out / f"{name}_pf1.bin").write_bytes(pf1)
        (out / f"{name}_pf2.bin").write_bytes(pf2)
    print(f"a2600: 4 fields of {VISIBLE} scanlines x 3 playfield registers -> {out}")


if __name__ == "__main__":
    main()
