    .module inputtest
    .include "sms.inc"

T_SOLID_WHITE = 1
T_SOLID_GREY  = 12

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
    ld hl, #inputtest_map
    ld de, #NAME_TABLE
    ld bc, #MAP_BYTES
    call vdp_write

    xor a
    ld (latch1), a

frame:
    call read_pad

    ; Both buttons together clears the latch.
    ld a, (pad1)
    and #(PAD_B1 | PAD_B2)
    cp #(PAD_B1 | PAD_B2)
    jr nz, keep
    xor a
    ld (latch1), a
keep:
    ld a, (latch1)
    ld b, a
    ld a, (pad1)
    or b
    ld (latch1), a

    xor a
    ld (slot), a
    call draw_controls
    call draw_raw
    call draw_unseen
    ld a, (slot)
    call sprite_end
    call vsync
    jp frame

; Held wins over latched, so what you are holding stays visible once the rest
; has gone grey.
draw_controls:
    ld hl, #ctrl_table
    ld b, #6
ctrl_loop:
    push bc
    ld a, (hl)                  ; mask
    inc hl
    ld c, a
    ld a, (pad1)
    and c
    jr nz, held
    ld a, (latch1)
    and c
    jr nz, seen
    ld d, #0
    jr emit
seen:
    ld d, #T_SOLID_GREY
    jr emit
held:
    ld d, #T_SOLID_WHITE
emit:
    ld a, (hl)                  ; x
    inc hl
    ld c, a
    ld a, (hl)                  ; y
    inc hl
    push hl
    ld b, a
    ld a, (slot)
    call sprite_set
    ld a, (slot)
    inc a
    ld (slot), a
    pop hl
    pop bc
    djnz ctrl_loop
    ret

; The raw port byte in hex. When a control lands on the wrong bit, the bit
; that moved says what it was mapped to.
draw_raw:
    ld a, (pad1)
    rrca
    rrca
    rrca
    rrca
    and #0x0F
    ld c, #40
    call put_hex
    ld a, (pad1)
    and #0x0F
    ld c, #48
    call put_hex
    ret

; A = nibble, C = x. Tile index equals the character code.
put_hex:
    cp #10
    jr c, is_digit
    add a, #55                  ; 'A' - 10
    jr have_char
is_digit:
    add a, #48                  ; '0'
have_char:
    ld d, a
    ld b, #112
    ld a, (slot)
    call sprite_set
    ld a, (slot)
    inc a
    ld (slot), a
    ret

; Zero means every control has arrived at least once.
draw_unseen:
    ld a, #6
    ld (tmpb), a
    ld hl, #ctrl_table
    ld b, #6
tally:
    push bc
    ld a, (hl)
    ld c, a
    ld a, (latch1)
    and c
    jr z, not_seen
    ld a, (tmpb)
    dec a
    ld (tmpb), a
not_seen:
    inc hl
    inc hl
    inc hl
    pop bc
    djnz tally

    ld a, (tmpb)
    add a, #48
    ld d, a
    ld c, #56
    ld b, #128
    ld a, (slot)
    call sprite_set
    ld a, (slot)
    inc a
    ld (slot), a
    ret

    .org 0x1000
; mask, x, y - the indicator sits just left of each label in the name table.
ctrl_table:
    .db PAD_UP,    32, 32
    .db PAD_DOWN,  32, 80
    .db PAD_LEFT,  0,  56
    .db PAD_RIGHT, 64, 56
    .db PAD_B1,    120, 56
    .db PAD_B2,    152, 56

tiles:
    .incbin "tiles.bin"
palettes:
    .incbin "palettes.bin"
inputtest_map:
    .incbin "inputtest_map.bin"
