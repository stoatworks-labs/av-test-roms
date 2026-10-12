# Notes

Working notes for this repo: status, decisions, and the traps that have actually bitten.
Migrated out of Claude Code's memory on 2026-08-24, so they are written in the first
person and dated by when each thing was learned — that date is usually the useful part.

Cross-cutting notes that are not specific to this repo live in
[fleet-notes](https://github.com/stoatworks-labs/fleet-notes).

*av-test-roms — emulator test ROM suite (testcard/inputtest/overscan), all 7 targets built, public*

`~/Projects/av-test-roms` — three programs (`testcard` with countable motion,
`inputtest` mapping tester, `overscan`) built natively per console. MIT, all
original, no BIOS or commercial ROM. **PUBLIC and live** at `github.com/stoatworks-labs/av-test-roms`, pushed
2026-08-06 with 2 of 7 targets done; the README carries an honest status table
rather than implying the rest exist.

**All seven targets built.** Six verified in a real core: **GBA** (mGBA),
**NES** (fceumm/Nestopia/Mesen/QuickNES), **GB/GBC** (gambatte), **Mega Drive**
(PicoDrive + Genesis Plus GX), **Master System** (Genesis Plus GX), **Atari
2600** (Stella). **C64 is built-only** — every C64 emulator needs the KERNAL /
BASIC / CHARGEN ROMs and this repo ships no BIOS; obtaining a set was left as
the user's call.

**mGBA refuses the Game Boy ROMs** — its GB core identifies a ROM by the
Nintendo logo bitmap, deliberately zeroed here. gambatte does not care.

Per-platform traps that cost real time, all written up in each target's README:
GB **OAM writes outside vblank/hblank are silently dropped** (shadow OAM + DMA
from HRAM); MD **crt0 must unmask interrupts** or vsync spins forever, and ROMs
**must be padded to a power of two**; SMS **sprite_set clobbered the tile in D**
so every sprite came out blank, and register 6 must be 0xFB; NES **tiles
0x20-0x5F are the ASCII font** and graphics there are silently overwritten;
2600 **forgetting COLUPF** gives a black screen because reset zeroes it.

The design point, in `docs/DESIGN.md`: **a static test card cannot show a
dropped frame**, so every panel carries a marker advancing exactly one cell per
emulated frame. That makes a slow program a *correctness* bug — the GBA
checkerboard's CPU store loop ran at a third of frame rate and the ticker
repeated cells while the screenshot looked perfect. It is DMA now.

Related: [cartest system directory](https://github.com/stoatworks-labs/fleet-notes/blob/main/notes/reference_cartest_system_directory.md), [cartridge](https://github.com/stoatworks-labs/cartridge/blob/main/docs/NOTES.md) (`cartridge`)
