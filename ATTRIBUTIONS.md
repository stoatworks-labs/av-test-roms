# Attributions

Every byte of the ROMs in this repository is original work, MIT licensed. No
console BIOS, no commercial ROM and no emulator core is included or required to
build.

## Build tools

None of these are redistributed here; they are installed from Homebrew.

| Tool | Used for | Licence |
|---|---|---|
| [cc65](https://cc65.github.io/) | NES, C64 (6502) | zlib |
| [RGBDS](https://rgbds.gbdev.io/) | Game Boy / GBC | MIT |
| [dasm](https://dasm-assembler.github.io/) | Atari 2600 | GPLv2 |
| [SDCC](https://sdcc.sourceforge.net/) | Master System / Game Gear (Z80) | GPLv2 |
| GNU `arm-none-eabi` toolchain | Game Boy Advance | GPLv3 with runtime exception |
| GNU `m68k-elf` toolchain | Mega Drive | GPLv3 with runtime exception |

## Verification

Cores are downloaded by the person doing the verifying and are **not**
redistributed here. Their licences are between you and their authors.

| Core | Used to verify | Licence |
|---|---|---|
| [mGBA](https://mgba.io/) | Game Boy Advance | MPL-2.0 |
| [QuickNES](https://github.com/libretro/QuickNES_Core) | NES | LGPLv2.1 |

The harness is `cartest` from
[cartridge](https://github.com/stoatworks-labs/cartridge), MIT.

## Reference

Hardware documentation used while writing these, none of it reproduced here:
the [NESdev Wiki](https://www.nesdev.org/wiki/), [GBATEK](https://problemkaputt.de/gbatek.htm),
and [Pan Docs](https://gbdev.io/pandocs/).
