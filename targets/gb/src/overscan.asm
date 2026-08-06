; overscan - safe-area and edge display, Game Boy / Game Boy Color.
; Static apart from the parity flash.

INCLUDE "runtime.inc"

DEF TILE_SOLID EQU 3
DEF TILE_BLANK EQU 0
DEF PARITY_X   EQU 152

SECTION "Overscan", ROM0

Main:
    call LCDOff
    ld  hl, TileData
    ld  de, _VRAM
    ld  bc, 4096
    call CopyBytes
    ld  hl, MapData
    ld  de, _SCRN0
    call CopyMap
    ld  hl, AttrData
    call LoadAttributes
    ld  hl, PalData
    call LoadPalettes
    call LCDOn

.frame:
    ld  a, [FrameLo]
    and 1
    ld  c, TILE_BLANK
    jr  z, .even
    ld  c, TILE_SOLID
.even:
    ld  b, 0
    ld  d, 0
    ld  e, PARITY_X
    call SetSprite
    call WaitVBlank
    call OAMDMA
    jr  .frame

SECTION "OverscanData", ROM0

TileData:
    INCBIN "tiles.bin"
MapData:
    INCBIN "overscan_map.bin"
AttrData:
    INCBIN "overscan_attr.bin"
PalData:
    INCBIN "overscan_pal.bin"
