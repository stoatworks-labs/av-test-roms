; overscan - safe-area and edge display, NES.
;
; Entirely static apart from the parity flash, so the whole screen is one
; nametable upload and the frame loop does nothing but the sprite.

.include "runtime.inc"

PARITY_X = 240

.segment "CODE"

.proc main
    lda #<overscan_nt
    sta src_ptr
    lda #>overscan_nt
    sta src_ptr+1
    lda #<overscan_pal
    sta pal_ptr
    lda #>overscan_pal
    sta pal_ptr+1
    jsr load_screen

frame:
    lda frame_lo
    and #1
    sta sprite_tile             ; tile 1 = solid white, tile 0 = transparent
    lda #0
    sta sprite_attr
    ldx #PARITY_X
    ldy #0
    lda #0
    jsr set_sprite

    jsr wait_frame
    jmp frame
.endproc

.segment "RODATA"
overscan_nt:
    .incbin "overscan_nt.bin"
overscan_pal:
    .incbin "overscan_pal.bin"
