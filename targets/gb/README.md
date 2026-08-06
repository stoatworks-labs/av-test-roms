# Game Boy / Game Boy Color

160x144. Built with **RGBDS**. One ROM per program, CGB-enhanced and
DMG-compatible: the same binary runs on both and uses colour only where a Game
Boy Color is present.

| ROM | Bytes |
|---|---|
| `testcard.gb` | 32768 |
| `inputtest.gb` | 32768 |
| `overscan.gb` | 32768 |

Verified against **gambatte**, in Game Boy Color mode and — by clearing the CGB
flag in a scratch copy so the core boots it as a DMG — in monochrome mode too.

## mGBA will not load these, and that is the licensing stance biting

mGBA's Game Boy core identifies a ROM by its **Nintendo logo bitmap** at
`$0104`, and refuses anything without it. That bitmap is Nintendo's artwork, so
it is left zeroed here exactly as it is on the GBA target. gambatte and SameBoy
load these ROMs without complaint; mGBA does not.

This was confirmed rather than assumed: running `rgbfix -f l` on a copy makes
mGBA accept the identical ROM.

If you want these in mGBA, write the logo into **your own copy**:

```bash
rgbfix -f l dist/gb/testcard.gb
```

That is your decision to make about a file on your machine. It is not done in
the build, and the artwork is not in this repository.

## One layout, two machines

A DMG has four greys and no more, so a colour test card has to degrade rather
than be drawn twice. The colour bars do it like this:

Bar *i* uses the **tile** whose ink is colour index *i* mod 4, and CGB palette
*i*, whose entry *i* mod 4 holds SMPTE colour *i*. On a Game Boy Color that is
eight distinct colours. On a DMG the attribute map does not exist at all, so it
falls back to the four shades 0,1,2,3 repeated twice — the DMG's whole gamut,
with every adjacent pair still distinguishable. Nothing is drawn twice and
there is no second code path to keep in step.

The luma staircase is four steps for the same reason.

## What the platform cost the design

**The checkerboard does not invert on a DMG.** On CGB it is eight bytes a
frame through `BCPD`, inverting palette 5 only. A DMG has no per-tile palettes,
so the equivalent is rewriting `BGP` — which inverts the title and the ticker
track along with the pattern. It is left static there; the parity flash still
provides a per-frame inversion to look at.

**The ruler has its own baseline.** On a 20-tile-wide screen the four insets
(4, 8, 12, 16 px) land two to a tile, so ticks cannot share a rectangle's line
the way they do on the NES. The ruler sits just inside the innermost box
instead.

**160 does not divide by 8 bars into whole tiles.** Each bar is 20 px, so every
other bar boundary falls in the middle of a tile. That is what the `split`
tiles are for: five tiles per pair of bars, the middle one carrying the change.

## The trap that cost the most: OAM is not always writable

Sprites are staged in `ShadowOAM` and pushed across with a DMA routine that
runs from HRAM. That is the standard Game Boy idiom, and this is what happens
if you skip it.

Writing OAM directly only works during vblank or hblank. At any other time the
write is **silently dropped** — no fault, no side effect, nothing. A frame's
worth of sprite updates overruns vblank, so the later writes landed or did not
depending on which PPU mode the CPU happened to be in when they executed.

The symptom was that sprite slot 10 never appeared while slots 8 and 9 always
did. It survived every plausible explanation: the tile was correct in VRAM, the
palette was right, the OAM address arithmetic was right, and the generated code
disassembled exactly as intended. Writing a known-good sprite to slot 10 after
everything else still produced nothing, while slot 11 written immediately
afterwards appeared — which is the tell, because a *deterministic* bug cannot
do that. It was position in the frame, not slot number.

The DMA routine lives in HRAM because that is the only memory the CPU can reach
while the transfer runs. `OAMDMA_SIZE` is asserted against the routine's real
length so the reserved space cannot silently drift.

## Two smaller traps

**OAM stores y+16 and x+8.** Every "my sprite is invisible" bug on this
platform is that offset. `SetSprite` applies it.

**The DMG sprite palette default makes colour 3 black**, which on a black field
is indistinguishable from not drawing at all. `OBP_STD` is `%00011000` so
index 3 comes out white.
