# How these ROMs were verified

"Verified" here means the ROM was loaded into a real libretro core, run, and
the frames looked at. It does not mean it assembled.

The harness is `cartest` from
[cartridge](https://github.com/stoatworks-labs/cartridge), which loads a core,
steps it a fixed number of frames with no thread and no clock, and writes PNGs.
Being synchronous is what makes the frame counts below mean anything.

```bash
cartest --core ~/Documents/Cartridge/cores/mgba_libretro.dylib \
        --content dist/gba/testcard.gba --frames 40 --out /tmp/tc.png
```

## The ticker check

The interesting verification is not "does it draw the right picture" but "does
it draw it at the right *rate*". Every testcard panel advances one ticker cell
per frame, so dumping a frame sequence and reading the cell position back gives
a direct measurement:

```bash
cartest --core .../mgba_libretro.dylib --content dist/gba/testcard.gba \
        --frames 700 --seq /tmp/seq_
```

then, per frame, find the white cell and check it moved exactly one place.
On mGBA, after the checkerboard was moved to DMA:

| Panel | Single-cell steps |
|---|---|
| BARS | 34/35 |
| HATCH | 39/39 |
| BURST | 39/39 |
| CHECK | 39/39 |
| EDGE | 39/39 |

The same measurement on the Game Boy build, through gambatte: HATCH, BURST and
CHECK all 39/39, BARS 37/39 — that window contains a panel change, which on
this target switches the LCD off to upload a kilobyte and costs two frames
rather than one.

BARS is 34/35 on the GBA because that window contains a panel change, which redraws the
whole screen and costs one frame. The ticker reporting it is the instrument
working.

**Read the pixels with a threshold, not an equality.** mGBA converts its RGB555
framebuffer to RGB888, so "white" arrives as (255, 251, 255). An exact
comparison against (255, 255, 255) finds nothing and looks exactly like a ROM
that never drew anything.

## Cores used

| Target | Core | Result |
|---|---|---|
| GBA | mGBA 0.11-219 | all three ROMs render |
| NES | fceumm, Nestopia, Mesen | all three ROMs render at 256x240 |
| NES | QuickNES | all three render, cropped to 240x224 |
| Game Boy Color | gambatte | all three ROMs render in colour |
| Game Boy (DMG) | gambatte, CGB flag cleared in a scratch copy | bars degrade to four shades as designed |
| Mega Drive | PicoDrive, Genesis Plus GX | all three render; 39/39 ticker steps on every panel |
| Master System | Genesis Plus GX | all three render; 39/39 ticker steps, 38/39 across a panel change |
| Commodore 64 | none — needs a C64 ROM set | built and structurally checked only |

## mGBA refuses the Game Boy ROMs

Its GB core identifies a ROM by the Nintendo logo bitmap at `$0104`, which is
deliberately zero here. Confirmed rather than assumed: `rgbfix -f l` on a copy
makes mGBA accept the otherwise identical file. gambatte does not care.

## Four cores that could not load anything, and why

This one was the frontend, not the ROMs, and it cost a full pass through an
iNES header byte by byte before that became clear. Fixed in
[cartridge#1](https://github.com/stoatworks-labs/cartridge/pull/1); the
verification below used a `cartest` built from that branch.

| Core | Symptom |
|---|---|
| **fceumm** | segfault (exit 139) inside `retro_load_game` |
| **Genesis Plus GX** | segfault (exit 139) inside `retro_load_game` |
| **Nestopia** | `retro_load_game` returns false |
| **Mesen** | `retro_load_game` returns false |

Two causes, and the second is the interesting one:

1. Nothing ever called `Core::SetSystemDirectory`, so cores wanting a BIOS or
   database file got a null pointer. `cartest` now takes `--system`.
2. `GET_VARIABLE` answered **true** with `value = nullptr`. Many cores are
   written as `if( environ_cb( GET_VARIABLE, &var ) ) strcmp( var.value, ... )`
   and dereference the null the instant the call says true. Answering false
   makes them fall back to their own defaults.

All four failures present identically from the outside: a bad ROM.

## The crop table, which is the whole point

With every core loading, the same NES ROM through four of them:

| Core | Output |
|---|---|
| fceumm | 256x240 |
| Nestopia | 256x240 |
| Mesen | 256x240 |
| **QuickNES** | **240x224** |

QuickNES crops eight pixels off each edge and the top and bottom, which
swallows the title row. Three cores agree and one does not — and `overscan`
puts a number on exactly how much.
