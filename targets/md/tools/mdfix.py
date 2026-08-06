#!/usr/bin/env python3
"""Patch the Mega Drive header checksum, in place.

The checksum is the 16-bit sum of every word from $200 to the end of the ROM.
A real console does not check it, but Sega's own tools wrote it and some
flashcarts and validators still look, so writing it correctly costs nothing.
"""

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: mdfix.py ROM", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    rom = bytearray(path.read_bytes())

    if len(rom) < 0x200:
        print(f"{path}: {len(rom)} bytes, too short to hold a header", file=sys.stderr)
        return 1
    if rom[0x100:0x110] != b"SEGA MEGA DRIVE ":
        print(f"{path}: no SEGA header at $100 - this is not a cartridge image",
              file=sys.stderr)
        return 1

    # Pad to a power of two, minimum 32 KB. A real cartridge is a ROM chip and
    # is therefore always a power of two; Genesis Plus GX segfaults inside
    # retro_load_game on an image that is not, before it reports anything.
    size = 0x8000
    while size < len(rom):
        size <<= 1
    rom.extend(b"\xFF" * (size - len(rom)))

    # The header's ROM end must describe the padded image, not the linker's
    # idea of where code stopped.
    end = size - 1
    rom[0x1A4:0x1A8] = bytes(((end >> 24) & 0xFF, (end >> 16) & 0xFF,
                              (end >> 8) & 0xFF, end & 0xFF))

    total = 0
    for i in range(0x200, len(rom), 2):
        total = (total + (rom[i] << 8) + rom[i + 1]) & 0xFFFF

    # The checksum covers the padding too, so it is computed after it.
    rom[0x18E] = (total >> 8) & 0xFF
    rom[0x18F] = total & 0xFF
    path.write_bytes(bytes(rom))
    print(f"{path.name}: {len(rom)} bytes, checksum {total:#06x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
