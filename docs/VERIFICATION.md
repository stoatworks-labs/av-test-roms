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
| NES | QuickNES | all three ROMs render, output cropped to 240x224 |
| Game Boy Color | gambatte | all three ROMs render in colour |
| Game Boy (DMG) | gambatte, CGB flag cleared in a scratch copy | bars degrade to four shades as designed |
| Mega Drive | PicoDrive | all three ROMs render; 39/39 ticker steps on every panel |

## mGBA refuses the Game Boy ROMs

Its GB core identifies a ROM by the Nintendo logo bitmap at `$0104`, which is
deliberately zero here. Confirmed rather than assumed: `rgbfix -f l` on a copy
makes mGBA accept the otherwise identical file. gambatte does not care.

## Three NES cores that could not be used, and why

Not a fault in the ROMs — worth recording so the next person does not repeat
the bisection.

`cartest` never calls `Core::SetSystemDirectory`, so
`RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY` hands back a null pointer. Cores that
want a system directory at load time then fail, in three different ways:

| Core | Symptom |
|---|---|
| **fceumm** | segfault (exit 139) while building the path for `nes.pal` |
| **Nestopia** | `retro_load_game` returns false — needs `NstDatabase.xml` |
| **Mesen** | `retro_load_game` returns false |

**Genesis Plus GX** fails the same way on the Mega Drive build. Padding the ROM
to a power of two fixed an *earlier* crash in the same function, so the two look
identical from outside; PicoDrive loads the padded image without complaint.

All three look identical to a malformed ROM from the outside, which is what
made it worth checking the iNES header byte by byte before suspecting the
harness. QuickNES needs no system files and loads the same ROM without
complaint.
