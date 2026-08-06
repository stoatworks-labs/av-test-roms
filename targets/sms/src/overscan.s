    .module overscan
    .include "sms.inc"

T_SOLID_WHITE = 1
PARITY_X = 240

; Continues the absolute image sms.inc started. Without an explicit origin
; the linker places _CODE at 0 and it lands on the reset vector.
    .area _HEADER (ABS)
    .org 0x0400
main:
    ld hl, #tiles
    ld de, #0x0000
    ld bc, #6144
    call vdp_write
    ld hl, #palettes
    call vdp_palette
    ld hl, #overscan_map
    ld de, #NAME_TABLE
    ld bc, #MAP_BYTES
    call vdp_write

frame:
    ld a, (frame_lo)
    and #1
    ld d, #0
    jr z, go
    ld d, #T_SOLID_WHITE
go:
    ld c, #PARITY_X
    ld b, #8
    xor a
    call sprite_set
    ld a, #1
    call sprite_end
    call vsync
    jp frame

    .org 0x1000
tiles:
    .incbin "tiles.bin"
palettes:
    .incbin "palettes.bin"
overscan_map:
    .incbin "overscan_map.bin"
