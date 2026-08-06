# NES

256x240, NROM-256 (mapper 0), 32 KB PRG + 8 KB CHR. Built with `cc65`.

| ROM | Bytes |
|---|---|
| `testcard.nes` | 40976 |
| `inputtest.nes` | 40976 |
| `overscan.nes` | 40976 |

Verified against **QuickNES**. Three other NES cores could not load it for
reasons that turned out to be the harness rather than the ROM — see
[docs/VERIFICATION.md](../../docs/VERIFICATION.md) before assuming a header
fault.

## The layouts are generated, not written

`tools/gen.py` emits the CHR-ROM and every nametable. The reason is the
attribute table: the NES colours backgrounds at **16x16 granularity**, three
colours plus a shared background per block. Every layout has to be checked
against that, and checking it by eye in a hand-written table is how NES
projects end up with one wrong block nobody notices.

So a cell declares a *demand* — which palette index it paints with and what
colour that index has to be — and the attribute table is derived. A block that
cannot be satisfied raises `AttributeError` with its tile coordinates. It did,
twice, while this was being written: once for dim grey label text that no
palette carried at index 1, and once for the ticker track, which needs red and
dark grey together and now has palette 3 reserved for it on every panel.

Tile indices for text equal the character's ASCII code, so drawing a string is
copying its bytes with no translation table anywhere. That convention has one
sharp edge: **a graphics tile placed in 0x20..0x5F is silently overwritten**
when the font is written. The crosshair came out as `#` and the ruler ticks as
`%` and `+`, with no error from anything. Graphics tiles now live below 0x20 or
at 0x60 and above, and `build_chr` writes the font first so a future collision
shows up as a wrong glyph rather than a missing graphic.

## What the platform costs the design

**The luma staircase is four steps, not sixteen.** The NES background palette
holds four greys — `$0F`, `$00`, `$10`, `$20` — and that is all of them.
`$0D` is a "blacker than black" that some displays and capture cards clip, so
it is never used here.

**The overscan rectangles are all white.** Colour-coding them the way the GBA
build does is impossible: near a corner, one 16x16 attribute block contains the
vertical arms of two rectangles and the horizontal arms of two others, which is
four colours in a block that holds three. White costs the colour key and keeps
the geometry exact, and the geometry is the measurement that matters. The
insets themselves are at true pixel positions (6, 12, 19, 25), not rounded to
the tile grid.

**Every moving element is a sprite.** NROM has no scanline interrupt, and the
NES cannot scroll part of a background without one. The frame ticker, the
1px/frame bar and the parity flash are all OAM, which also means `inputtest`
never writes to the PPU outside the sprite DMA the runtime already does.

**Panel changes cost a black frame.** A kilobyte of nametable does not fit in
one vblank, so rendering is switched off for the transfer. The frame ticker
reports the hitch, which is the instrument working.

## The one ordering rule in the NMI

Sprite DMA, then the optional palette write, then the address and scroll reset
— in that order. Any write to `PPUADDR` corrupts the scroll position, so a
palette write placed after the reset shifts the whole screen sideways. The
checkerboard inverts by rewriting two palette bytes a frame, against the GBA
build's sixteen DMA transfers for the same effect; that is what a palette buys
you.
