# av-test-roms

> **AI-assisted project.** This codebase was created with [Claude](https://claude.com/claude-code)
> (Anthropic), directed and reviewed by a human author. Five of the seven
> targets are verified in the sense that the ROMs were run in an emulator core
> and the frames were looked at — GBA in mGBA, NES in fceumm/Nestopia/Mesen/
> QuickNES, Game Boy in gambatte, Mega Drive in PicoDrive and Genesis Plus GX,
> and Master System in Genesis Plus GX. **The C64 ROMs are built but have never
> been run**, for want of a C64 ROM set, and the Atari 2600 target is not
> started. **Nothing here has been run on real console hardware** — indeed the
> GBA ROMs cannot be, by design.

Test ROMs for emulators, built from source, for people who care about the
**video path** rather than about emulation accuracy.

Three programs — a moving test card, a controller mapping tester, and an
overscan display — built for as many consoles as have a toolchain in Homebrew.
Everything here is original work under MIT: no console BIOS, no commercial ROM,
nothing that needs either.

Written for [cartridge](https://github.com/stoatworks-labs/cartridge), which
runs a libretro core as an FFGL source inside Resolume, but there is nothing
cartridge-specific in them. They are ordinary ROMs and will run in anything.

---

## Status

Seven targets are planned. **Five are built and verified**; the rest are not
started, and this table is the honest state of it rather than a roadmap.

| Target | Toolchain | ROMs | Verified in |
|---|---|---|---|
| **Game Boy Advance** | `arm-none-eabi-gcc` | 3 | mGBA 0.11 ✅ |
| **NES** | `cc65` | 3 | fceumm, Nestopia, Mesen, QuickNES ✅ |
| **Game Boy / GBC** | `rgbds` | 3 | gambatte ✅ |
| **Mega Drive** | `m68k-elf-gcc` | 3 | PicoDrive, Genesis Plus GX ✅ |
| **Master System** | `sdcc` | 3 | Genesis Plus GX ✅ |
| Atari 2600 | `dasm` | — | not started |
| **Commodore 64** | `cc65` | 3 | built only — needs a C64 ROM set ⚠️ |

"Verified" means the ROM was run in that core and the resulting frames were
looked at — not merely that it assembled. See [docs/VERIFICATION.md](docs/VERIFICATION.md).

## Build

```bash
brew install cc65 rgbds dasm sdcc arm-none-eabi-gcc m68k-elf-gcc
make
```

`make toolchains` prints which of them you have. ROMs land in `dist/<target>/`.

## The three programs

Specified once, in [docs/DESIGN.md](docs/DESIGN.md), in terms of what they must
*show* — the code cannot be shared between a machine that races the beam with
128 bytes of RAM and one with a display list, but the design can.

**`testcard`** — colour bars, crosshatch, frequency burst, checkerboard and a
luma/chroma edge, cycling. What makes it worth having over a static card is
that every panel carries **countable motion**: a marker advancing exactly one
cell per emulated frame, a bar moving one pixel per frame, and a square
inverting every frame. A dropped or repeated frame is invisible in a static
pattern and obvious in these.

**`inputtest`** — the platform's own pad, drawn as a pad. Controls light while
held and **latch** once seen, so walking every button once shows you which one
never arrived — the actual failure when a frontend's mapping is wrong. The raw
port word is shown in hex, because when a control lands on the wrong bit, the
bit that moved tells you what it was mapped to.

**`overscan`** — nested safe-area insets, ruler ticks every 8 pixels from all
four edges, and asymmetric corner markers so a flipped output is obvious rather
than merely plausible. The output is a number: "the path is eating 6 pixels off
the left", not "it looks a bit off".

## Three things the suite found while being written

Both are in the target READMEs, and both are the reason this exists.

**A test card can lie about its own frame rate.** The GBA checkerboard first
inverted with a CPU store loop — 15360 writes a frame — and sustained about a
third of frame rate, so the ticker repeated cells instead of advancing one per
frame. An instrument whose frame counter is wrong is worse than no instrument.
It is DMA now, and holds 39/39 single-cell steps on every panel.

**Cores disagree about how much of the NES picture there is.** fceumm, Nestopia
and Mesen all return 256x240; QuickNES returns 240x224, cropping eight pixels
off each edge and swallowing the title row. Three agree and one does not, and
`overscan` puts a number on the difference. That is precisely the question this
suite exists to answer.

**One Game Boy binary can serve both machines.** Bar *i* uses the tile whose
ink is index *i* mod 4 and CGB palette *i*, so a Game Boy Color shows eight
colours and a DMG — where the attribute map does not exist — falls back to its
four shades twice over, adjacent bars still distinguishable. No second code
path, nothing drawn twice.

## Licensing, and what is deliberately missing

MIT, and every byte is original. Two consequences worth stating plainly:

- **The GBA ROMs will not boot on real hardware.** A GBA BIOS checks the
  Nintendo logo bitmap in the cartridge header before it runs anything. That
  bitmap is Nintendo's artwork, so the field is zeroed. They run in any
  emulator that skips the check.
- **mGBA will not load the Game Boy ROMs**, for the same reason: its GB core
  identifies a ROM *by* that logo. gambatte and SameBoy load them fine, and
  `rgbfix -f l` on your own copy makes mGBA accept it — your call, on your
  machine, not something this repo ships.
- **No cores are included**, and none will be. Cores have their own licences,
  several of them non-commercial. Get them the way you would for RetroArch.
