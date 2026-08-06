; overscan - safe-area and edge display, Commodore 64.
; Static apart from the parity flash.

.include "c64.inc"

PARITY_SPR = 0
PARITY_Y   = 50

.segment "CODE"

.proc main
    lda #<overscan_scr
    sta src_ptr
    lda #>overscan_scr
    sta src_ptr+1
    lda #<overscan_col
    sta col_ptr
    lda #>overscan_col
    sta col_ptr+1
    jsr upload

    lda #%00000001
    sta VIC_SPREN
    lda #1
    sta VIC_SPRCOL0
    lda #(SPRITES_AT / 64) + 1      ; solid block
    sta SPRPTR + PARITY_SPR

frame:
    lda frame_lo
    and #1
    beq off
    lda #164
    ldy #PARITY_Y
    bne go
off:
    lda #0
    ldy #0
go:
    sty tmp
    ldx #PARITY_SPR
    jsr sprite_at
    jsr vsync
    jmp frame
.endproc

.segment "MAPDATA"
overscan_scr:
    .incbin "overscan_scr.bin"
overscan_col:
    .incbin "overscan_col.bin"
