; overscan - safe-area and edge display, Atari 2600.
;
; The playfield is 20 bits wide, each bit four pixels, mirrored into the right
; half - so the horizontal grid here is 4 pixels, not 1, and the insets are
; quantised to it. Vertically there is no such limit: a playfield register can
; change on any scanline, so the horizontal rules land exactly.

    processor 6502
    include "vcs.inc"

    seg.u ram
    org $80
frame       ds 1
line        ds 1
tmp         ds 1

    seg code
    org $F000

reset:
    sei
    cld
    ldx #0
    txa
clear:                          ; zero RAM and every TIA register
    sta $00,x
    inx
    bne clear

    lda #$0E                    ; playfield white
    sta COLUPF
    lda #$00
    sta COLUBK
    lda #%00000001              ; reflected playfield: a proper mirror
    sta CTRLPF

frame_loop:
    lda #2                      ; three lines of vertical sync
    sta VSYNC
    sta WSYNC
    sta WSYNC
    sta WSYNC
    lda #0
    sta VSYNC

    lda #43                     ; 37 lines of vertical blank, timed
    sta TIM64T
    inc frame

    ; The parity flash: one scanline of the top border inverts every frame,
    ; which is this machine's equivalent of the flashing square elsewhere.
    lda frame
    and #1
    beq no_flash
    lda #$0E
    bne set_flash
no_flash:
    lda #$00
set_flash:
    sta tmp

vblank_wait:
    lda INTIM
    bne vblank_wait
    sta WSYNC
    lda #0
    sta VBLANK                  ; beam on

    ; --- visible kernel ---
    ldy #0
; WSYNC comes FIRST. The three playfield writes take 21 cycles and horizontal
; blank is 22.67, so they only land before the beam reaches the left edge if
; nothing else runs first - with the loop counter ahead of them, PF0 is written
; after the beam has already passed the pixels it controls.
kernel:
    sta WSYNC
    lda pf0_table,y
    sta PF0
    lda pf1_table,y
    sta PF1
    lda pf2_table,y
    sta PF2
    iny
    cpy #VISIBLE_LINES
    bne kernel

    lda #0
    sta PF0
    sta PF1
    sta PF2

    lda #2                      ; 30 lines of overscan
    sta VBLANK
    lda #35
    sta TIM64T
overscan_wait:
    lda INTIM
    bne overscan_wait
    sta WSYNC
    jmp frame_loop

; The three playfield registers for each of the 192 visible lines, generated
; by tools/gen.py. 576 bytes, which is most of what a 4K cartridge has spare.
pf0_table:
    incbin "overscan_pf0.bin"
pf1_table:
    incbin "overscan_pf1.bin"
pf2_table:
    incbin "overscan_pf2.bin"

    org $FFFC
    .word reset
    .word reset
