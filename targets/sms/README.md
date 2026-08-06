# Master System

256x192 as 32x24 tiles, Z80. Built with SDCC's `sdasz80` and `sdldz80` — no C
and no runtime, just Z80.

| ROM | Bytes |
|---|---|
| `testcard.sms` | 32768 |
| `inputtest.sms` | 32768 |
| `overscan.sms` | 32768 |

Verified against **Genesis Plus GX**. Ticker: 39/39 single-cell steps on
HATCH, BURST and CHECK; 38/39 across a panel change.

## Where this sits between the others

Colour is 6-bit `--BBGGRR`: two bits a channel, four levels each, 64 in total.
Every SMPTE colour is expressible, so the bars are just the bars. The grey ramp
is **four steps**, which is the whole gamut.

The name table gives each cell a 16-bit entry, but only **bit 11** for the
palette — two palettes, not the Mega Drive's four. That does not cost anything
here, because four bits per pixel means one tile can carry several colours from
its palette. Which matters most in one place:

**The two-line overscan tile.** The 5% and 7.5% horizontal insets are at y=9
and y=14, both inside tile row 1. On the C64 that forced those two rectangles
to share a colour, because colour RAM is one entry per cell. Here the two lines
simply take different colour indices inside the same tile and stay properly
keyed. Same collision, different cost — that is the interesting difference
between the two machines.

**The checkerboard inverts with one CRAM byte.** The tile is drawn in entries 1
and 14, so rewriting entry 14 flips every cell using it.

## Three things about the toolchain and the VDP

**`sdasz80` wants `-Idir` attached**, and writes its `.rel` next to the source
however it is invoked — the explicit-outfile form in its own usage text does
not take. The Makefile assembles in place and moves the result.

**Everything is one absolute area with explicit origins.** Left as a
relocatable `_CODE`, the linker places it at address 0 and it lands squarely on
the reset vector: the ROM then starts with the program's first instruction
instead of `di / im 1 / jp init`.

**RAM is declared as equates, not a reserved area.** A `.ds` block inside the
absolute image makes `makebin` pad the file out to $C000.

## The bug worth remembering

`sprite_set` takes the tile in `D`, and the offset arithmetic needs a 16-bit
register pair — so an `ld d, #0` in the middle of it quietly destroyed the
tile number. Every sprite came out as **tile 0, which is blank**, and the
symptom was no sprites at all: no ticker marker, no scroll bar, nothing. That
looks exactly like sprites being disabled, and sent me through the sprite
attribute table base, the pattern base bit in register 6 and the palette before
the actual cause. `D` is pushed now.

(The pattern base *was* also wrong — register 6 must be `0xFB` to point sprite
tiles at $0000 where ours are, not the usual `0xFF` which selects $2000. Two
faults with one symptom, which is why the first fix appeared to do nothing.)
