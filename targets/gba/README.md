# Game Boy Advance

240x160, 16-bit colour, mode 3. Built with `arm-none-eabi-gcc`.

| ROM | Bytes |
|---|---|
| `testcard.gba` | 4048 |
| `inputtest.gba` | 3316 |
| `overscan.gba` | 3100 |

Verified against **mGBA 0.11** through `cartridge`'s `cartest` harness.

## It will not boot on real hardware

Bytes 0x04..0x9F of a GBA cartridge header hold the Nintendo logo bitmap, which
the BIOS compares against its own copy before it will run anything. That bitmap
is Nintendo's artwork, so it is not reproduced here and the field is zeroed.
These ROMs run in any emulator that skips the BIOS check, which is the default
in mGBA. The header's complement byte *is* computed correctly, so that is the
only reason they will not boot on a console rather than one of two.

## Three things worth knowing before editing

**`__data_guard` in `crt0.s` must stay.** Every table here is `const` and every
variable is zero-initialised, so `.data` comes out empty. An empty output
section gets no LOAD segment, which leaves its load address at the IWRAM
*virtual* address rather than the ROM one, and `objcopy -O binary` then spans
0x03000000 to the end of ROM and writes an 83 MB file whose header is four
megabytes in. A four-byte word keeps the section non-empty; it lives in its own
`.data.guard` section because `--gc-sections` collects it otherwise.

**The C is built Thumb.** Cartridge ROM is a 16-bit bus, so a 32-bit ARM
instruction costs two fetches. `crt0.s` stays ARM because reset arrives in ARM
state, hence `-mthumb-interwork`.

**libgcc is linked explicitly.** The ARM7TDMI has no divide instruction, so gcc
emits `__aeabi_idiv`/`__aeabi_idivmod` calls. `-nostdlib` drops libgcc along
with everything else, so `-lgcc` has to come back — it is the only library
linked.

## The checkerboard is DMA'd, and why that matters

Mode 3 has no palette, so inverting the checkerboard means rewriting all 128
rows: 15360 32-bit stores. Measured against this ROM's own frame ticker on
mGBA, the store loop that did that sustained about a third of frame rate — the
ticker repeated cells (22, 22, 23, 23, 23) instead of advancing one per frame.

That is worse than a slow test card. The ticker's entire purpose is to let you
count dropped frames, so a ticker that is wrong because of the test card makes
the instrument lie. Two 8-row phase buffers are now built once and blitted with
16 DMA transfers a frame, and every panel holds 39/39 single-cell steps.

On the tile-based targets in this suite the same inversion is one palette
write, which is why only this one needed it.

**The panel change costs one frame.** Switching panel redraws the whole screen,
and the ticker duly reports the hitch. That is the instrument working, not a
fault — but it is why panel changes are 128 frames apart and why holding a
panel by hand (any button; `START` resumes cycling) is the way to photograph
one.
