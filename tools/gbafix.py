#!/usr/bin/env python3
"""Patch the GBA cartridge header complement check, in place.

The BIOS verifies byte 0xBD against the header bytes 0xA0..0xBC. Emulators that
skip the BIOS do not care, but writing it correctly costs nothing and means the
only reason these ROMs will not boot on hardware is the missing Nintendo logo -
one documented reason instead of two.
"""

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: gbafix.py ROM", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    rom = bytearray(path.read_bytes())

    if len(rom) < 0xC0:
        print(f"{path}: {len(rom)} bytes, too short to hold a header", file=sys.stderr)
        return 1

    rom[0xBD] = (-(0x19 + sum(rom[0xA0:0xBD]))) & 0xFF

    # The header claims a 0x96 at 0xB2; if that is wrong the build produced
    # something that is not a cartridge image at all.
    if rom[0xB2] != 0x96:
        print(f"{path}: byte 0xB2 is {rom[0xB2]:#04x}, expected 0x96", file=sys.stderr)
        return 1

    path.write_bytes(bytes(rom))
    print(f"{path.name}: {len(rom)} bytes, complement {rom[0xBD]:#04x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
