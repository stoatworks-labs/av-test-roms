# Mega Drive / Genesis

320x224 (H40), 68000. Built with `m68k-elf-gcc`.

| ROM | Bytes |
|---|---|
| `testcard.bin` | 32768 |
| `inputtest.bin` | 32768 |
| `overscan.bin` | 32768 |

Verified against **PicoDrive**. Genesis Plus GX could not be used — see below;
it is not the ROM.

## The roomiest target in the suite

After the NES and the Game Boy this platform is a holiday. Sixteen colours per
palette and a full 16-bit plane entry per cell carrying tile, palette, priority
and both flip bits, which means:

- **The colour bars are just the colour bars.** All eight SMPTE colours live in
  one palette. No degrading, no palette-index tricks, no split tiles.
- **The grey ramp is eight steps** — three bits a channel is eight levels and
  that is the platform's entire grey gamut, so the ramp *is* the gamut.
- **The overscan rectangles are colour-keyed**, the only target in the suite
  where they are. That is not generosity: on the NES four rectangles meeting
  near a corner need four colours in a 16x16 attribute block that holds three,
  and here the palette travels with the cell.
- **A panel change costs no frames.** 39/39 single-cell ticker steps on every
  panel *including* the windows containing a panel change — the plane map
  uploads inside vblank. The GBA, NES and Game Boy builds all drop one or two
  frames there.

Also: the header is plain ASCII with nobody else's artwork in it, so unlike
both Nintendo platforms in this suite these ROMs are simply correct rather than
deliberately incomplete.

## Two things that cost time

**Interrupts start masked and nothing tells you.** `crt0.s` sets the status
register to `0x2700` during setup, which masks all seven levels. Left there,
the level 6 vertical blank never arrives, `vblank_count` never increments and
`vsync()` spins forever. The screen shows the first frame's background
perfectly and not one sprite — which reads as a sprite bug and is not one. The
mask goes down to 0 immediately before `main`.

**A cartridge is a ROM chip, so its size is a power of two.** `tools/mdfix.py`
pads to one, minimum 32 KB, and writes the header's ROM-end field to match.
Genesis Plus GX segfaults inside `retro_load_game` on an image that is not
padded, before it prints anything at all — which is indistinguishable from a
bad header until you pad it and the crash moves.

## Genesis Plus GX still cannot load these

Padding fixed one crash; it segfaults again on the null system directory
`cartest` hands out, the same way fceumm does. PicoDrive does not care and
loads all three. See [docs/VERIFICATION.md](../../docs/VERIFICATION.md).

## Sprites

`sprite_set` applies the +128 coordinate offsets and maintains the **link
field**, which chains the sprite list: a sprite whose link is zero ends it, so
every slot links to the next and the last links back to zero. Getting that
wrong truncates the list silently at whatever slot broke the chain.

The 1px/frame bar is four one-cell sprites rather than one four-cell sprite,
because a multi-cell sprite takes consecutive tiles — and the tiles after solid
white are the other solid colours, so a four-cell bar comes out as a small
colour-bar pattern.
