    .module testcard
    .include "sms.inc"

PANEL_COUNT  = 5
PANEL_FRAMES = 128
T_SOLID_WHITE = 1
T_TICKCELL   = 24
TICK_Y       = 176
SCROLL_Y     = 160
PARITY_X     = 240

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

    xor a
    ld (panel), a
    ld (since), a
    ld (manual), a
    ld (scrollx), a
    call load_panel

frame:
    call read_pad

    ld a, (pad_new)
    and #(PAD_B1 | PAD_RIGHT)
    jr z, check_prev
    ld a, (panel)
    inc a
    cp #PANEL_COUNT
    jr c, store_next
    xor a
store_next:
    ld (panel), a
    ld a, #1
    ld (manual), a
    call load_panel

check_prev:
    ld a, (pad_new)
    and #(PAD_B2 | PAD_LEFT)
    jr z, check_up
    ld a, (panel)
    or a
    jr nz, dec_panel
    ld a, #PANEL_COUNT
dec_panel:
    dec a
    ld (panel), a
    ld a, #1
    ld (manual), a
    call load_panel

check_up:
    ld a, (pad_new)
    and #PAD_UP
    jr z, auto
    xor a                       ; up resumes automatic cycling
    ld (manual), a

auto:
    ld a, (manual)
    or a
    jr nz, motion
    ld a, (since)
    inc a
    ld (since), a
    cp #PANEL_FRAMES
    jr c, motion
    xor a
    ld (since), a
    ld a, (panel)
    inc a
    cp #PANEL_COUNT
    jr c, store_auto
    xor a
store_auto:
    ld (panel), a
    call load_panel

motion:
    call update_sprites
    call update_check
    call vsync
    jp frame

; --- panel upload ---------------------------------------------------------
; Each map is 1536 bytes, which is not a shift, so the offset is reached by
; adding 1536 the required number of times.
load_panel:
    ld hl, #testcard_map
    ld a, (panel)
    or a
    jr z, upload_now
    ld b, a
add_loop:
    ld de, #MAP_BYTES
    add hl, de
    djnz add_loop
upload_now:
    ld de, #NAME_TABLE
    ld bc, #MAP_BYTES
    call vdp_write
    ret

; --- motion ---------------------------------------------------------------
update_sprites:
    ; Frame ticker: one 4-pixel cell per frame, 60 to the lap.
    ld a, (tick_cell)
    add a, a
    add a, a
    ld c, a
    ld b, #TICK_Y
    ld d, #T_TICKCELL
    xor a
    call sprite_set

    ; 1 px/frame bar, one 8-pixel sprite.
    ld a, (scrollx)
    inc a
    ld (scrollx), a
    ld c, a
    ld b, #SCROLL_Y
    ld d, #T_SOLID_WHITE
    ld a, #1
    call sprite_set

    ; Parity flash: solid on odd frames, blank on even, over the dim backing.
    ld a, (frame_lo)
    and #1
    ld d, #0
    jr z, parity_go
    ld d, #T_SOLID_WHITE
parity_go:
    ld c, #PARITY_X
    ld b, #8
    ld a, #2
    call sprite_set

    ld a, #3
    call sprite_end
    ret

; One CRAM byte a frame. The checkerboard tile is drawn in entries 1 and 14,
; so swapping what entry 14 holds inverts every cell using it.
update_check:
    ld a, (panel)
    cp #3
    ret nz
    ld a, (frame_lo)
    and #1
    ld b, #0x00                 ; black
    jr z, flip_write
    ld b, #0x3F                 ; white
flip_write:
    ld a, #14
    call vdp_cram_one
    ret

    .org 0x1000
tiles:
    .incbin "tiles.bin"
palettes:
    .incbin "palettes.bin"
testcard_map:
    .incbin "testcard_map.bin"
