# av-test-roms — orientation for another LLM (or a newcomer)

**What it is:** three test programs — `testcard`, `inputtest`, `overscan` —
built as native ROMs for as many consoles as Homebrew has a toolchain for.
Public, MIT, `github.com/stoatworks-labs/av-test-roms`. Written for
[cartridge](https://github.com/stoatworks-labs/cartridge) but not specific to
it.

`README.md` is the user-facing description and carries the honest status table.
This file is the *why*.

---

## The one idea

**This suite is about the video path, not about emulation accuracy.**

There are excellent accuracy suites already — blargg, Mesen, mooneye. This is
not one and must not drift into being one. It answers a different question:
*is the picture I am looking at the picture the core produced?* Frame pacing,
crop, colour, mapping. If a proposed feature is about whether a core emulates
something correctly, it belongs somewhere else.

That is why every testcard panel carries **countable motion**. A static test
card cannot show a dropped frame. A marker that advances exactly one cell per
emulated frame can, and the whole design follows from wanting that to be true.

## The rule that comes out of it

**An instrument that misreports is worse than no instrument.**

The GBA checkerboard originally inverted with a CPU store loop and ran at about
a third of frame rate, which made the frame ticker repeat cells. The picture
looked perfect in a screenshot. Any change that makes a program miss frames is
a correctness bug, not a performance nit — measure it with the ticker
(`docs/VERIFICATION.md`) before and after.

## Structure

```
docs/DESIGN.md      the three programs, specified once, platform-independent
tools/font.py       5x7 font shared by every tile-based target
tools/gbafix.py     GBA header complement
targets/<t>/        one directory per console, with its own README and Makefile
```

Code is **not** shared between targets and should not be. A 2600 races the beam
with 128 bytes of RAM; a Mega Drive has a display list. What is shared is
`docs/DESIGN.md` and the font. Each target's README documents what the platform
cost the design — those sections are the useful part of this repo and should be
written as each target lands.

## Traps, in the order they will cost you time

**Read verification pixels with a threshold.** mGBA converts RGB555 to RGB888,
so white arrives as (255, 251, 255). An equality test against pure white finds
nothing and looks exactly like a ROM that drew nothing.

**A core that rejects the ROM may well be the harness.** fceumm, Nestopia,
Mesen and Genesis Plus GX all failed to load anything, in three different ways,
for two frontend reasons: no system directory was ever set, and `GET_VARIABLE`
answered true with a null value that sloppy cores dereference. Fixed in
cartridge#1. The iNES and Mega Drive headers were correct the whole time —
check the harness before the third byte of a header.

**The GBA `.data` section must stay non-empty.** `__data_guard` in `crt0.s`
exists because an empty output section gets no LOAD segment, which leaves its
load address in IWRAM and makes `objcopy -O binary` emit an 83 MB file. It is
in its own `.data.guard` section because `--gc-sections` collects it otherwise.

**Game Boy OAM writes outside vblank/hblank are silently dropped.** Sprites go
through `ShadowOAM` and a DMA routine in HRAM. Without that, a frame's sprite
updates overrun vblank and the later ones land or not depending on PPU mode —
which presents as one specific sprite slot never appearing, and survives every
check of tile, palette, address and generated code. If a sprite is missing on
this target, suspect *when* it was written, not what.

**NES text tiles are indexed by ASCII, and that range is a minefield.** Glyphs
occupy tiles 0x20..0x5F so that drawing a string is copying its bytes. Any
graphics tile placed in that range is silently overwritten when the font is
written — the crosshair came out as `#` and the ruler ticks as `%` and `+`,
with no error anywhere. Graphics tiles live below 0x20 or at 0x60 and above,
and `build_chr` writes the font *first* so that a future collision shows up as
a wrong glyph rather than a missing graphic.

**The NES attribute solver is load-bearing.** `targets/nes/tools/gen.py` derives
the attribute table from per-cell colour demands and raises with tile
coordinates when a 16x16 block cannot be satisfied. When it raises, the layout
is wrong — do not widen the palettes to silence it without checking what the
block actually contains.

**The 2600 has no framebuffer and horizontal blank is 22.67 cycles.** Writes
made there are not seen. A colour bar cannot be narrower than one store, which
is fifteen pixels. Read `targets/a2600/README.md` before touching a kernel —
every constant in it is a cycle count.

**Forgetting COLUPF gives a black screen on the 2600**, because the reset loop
zeroes every TIA register including the playfield colour. Indistinguishable
from a kernel that never runs.

## Adding a target

1. Read `docs/DESIGN.md`. The three programs are specified there; do not
   redesign them per platform, adapt them and record what the platform cost.
2. `targets/<t>/Makefile` writes ROMs to `dist/<t>/`, and the target is added to
   `TARGETS_READY` in the top-level `Makefile`.
3. Verify in a real core and put the evidence in `docs/VERIFICATION.md`. A
   target that only assembles does not go in the README as verified — the
   status table is meant to be trustworthy.
