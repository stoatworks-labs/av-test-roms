# Commodore 64

320x200, 40x25 cells of 8x8 in hires text mode. Built with `cc65` (`ca65`/`ld65`).

| Program | Bytes |
|---|---|
| `testcard.prg` | 18705 |
| `inputtest.prg` | 10705 |
| `overscan.prg` | 10705 |

**Built, not core-verified.** See below — this is the one target in the suite
whose emulator needs a BIOS.

## Why this one is not verified in a core

Every C64 emulator needs the machine's **KERNAL, BASIC and CHARGEN ROMs**.
There is no way round it: a `.prg` is autostarted by BASIC, and even a
cartridge image relies on the KERNAL's reset sequence finding the CBM80
signature. VICE will boot to a black screen without them, which is exactly
what it does here:

```
Main: VICE system file directory: 'dist/c64/vice'.
Sysfile: Missing name for system file.
```

Those ROMs are Commodore's, and this repository's whole position is that it
ships no BIOS images and needs none. Downloading a set to verify locally is a
decision for whoever is doing the verifying, not something the build does.

What *is* verified: the ROMs assemble and link, the `.prg` carries the right
load address and BASIC stub (`SYS 2061` landing on the `JMP`), and the
character set and maps sit at the addresses `c64.cfg` places them at, checked
byte by byte in the output file.

To verify it yourself, put a VICE ROM set in `<system>/vice/` and:

```bash
cartest --core .../vice_x64sc_libretro.dylib --content dist/c64/testcard.prg \
        --system ~/Documents/Cartridge --frames 400 --out /tmp/c64.png
```

## What the platform cost the design

**There is no magenta.** The VIC-II palette is fixed in silicon and has no
magenta at all, so **purple** stands in for it in the colour bars. It is named
as a substitution here rather than passed off as the real thing.

**The grey ramp is five steps** — black, dark grey, mid grey, light grey,
white, which is every grey the machine has.

**Two overscan rectangles share a colour.** Colour RAM is one entry per 8x8
cell. The 5% and 7.5% horizontal insets are at y=10 and y=15, which both land
in character row 1, so one cell carries both lines and therefore one colour.
The vertical arms are all in separate columns and are properly colour-keyed.
This sits between the NES (no colour-keying at all, 16x16 blocks) and the Mega
Drive (fully colour-keyed, palette per cell).

## The cheapest inversion in the suite

The character set is in RAM at `$2000`, so inverting the checkerboard means
rewriting **the eight bytes of the checkerboard character** — every cell using
it flips at once, with no screen writes at all. Compare the GBA, which needs
sixteen DMA transfers a frame for the same effect.

## Two notes on the layout

`c64.cfg` places the character set at a fixed `$2000` rather than letting the
linker choose, because the VIC has to be able to see it: `MAIN` and `CHARSET`
are filled so the charset lands at exactly that address in the file, and `MAPS`
is not filled so the file ends where the data does.

A screen offset runs to 999 and will not fit in an index register, so every
indicator write in `inputtest` goes through a 16-bit pointer. That is what the
`write_cell` helper is for.

**Port 1 shares its lines with the keyboard matrix**, so it reads as pressed
whenever certain keys are down. That is a property of the machine rather than a
mapping fault, and `inputtest` says so on screen.
