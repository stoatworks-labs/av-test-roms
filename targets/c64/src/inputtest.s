; inputtest - controller mapping tester, Commodore 64.
;
; Indicators are screen characters rather than sprites: there are ten controls
; across two ports and only eight sprites, and unlike the Game Boy there is no
; restriction on when screen RAM may be written.

.include "c64.inc"

.segment "ZEROPAGE"
latch1: .res 1
latch2: .res 1
idx:    .res 1

.segment "CODE"

.proc main
    lda #<inputtest_scr
    sta src_ptr
    lda #>inputtest_scr
    sta src_ptr+1
    lda #<inputtest_col
    sta col_ptr
    lda #>inputtest_col
    sta col_ptr+1
    jsr upload

    lda #0
    sta latch1
    sta latch2

frame:
    jsr read_joy

    ; Both fire buttons together clears the latch.
    lda joy1
    and #JOY_FIRE
    beq keep
    lda joy2
    and #JOY_FIRE
    beq keep
    lda #0
    sta latch1
    sta latch2
keep:
    lda latch1
    ora joy1
    sta latch1
    lda latch2
    ora joy2
    sta latch2

    jsr draw_port1
    jsr draw_port2
    jsr draw_raw
    jsr draw_unseen
    jsr vsync
    jmp frame
.endproc

; A screen offset runs to 999, so it will not fit in an index register: every
; cell write goes through a 16-bit pointer. dst_ptr = offset, A = colour, the
; character in tmp+1.
.proc write_cell
    sta tmp
    lda dst_ptr
    sta col_ptr
    lda dst_ptr+1
    clc
    adc #>COLOUR
    sta col_ptr+1
    lda dst_ptr+1
    clc
    adc #>SCREEN
    sta dst_ptr+1
    ldy #0
    lda tmp+1
    sta (dst_ptr),y
    lda tmp
    sta (col_ptr),y
    rts
.endproc

; X = control index, A = colour, table base in `idx` (0 = port 2, 1 = port 1).
.proc place
    pha
    txa
    asl a
    tay
    lda idx
    beq port2
    lda p1_off,y
    sta dst_ptr
    lda p1_off+1,y
    sta dst_ptr+1
    jmp ready
port2:
    lda p2_off,y
    sta dst_ptr
    lda p2_off+1,y
    sta dst_ptr+1
ready:
    lda #1                          ; solid block
    sta tmp+1
    pla
    jsr write_cell
    rts
.endproc

; Held wins over latched, so what you are holding stays visible once the rest
; has gone grey.
.proc draw_port1
    lda #0
    sta idx
    ldx #0
loop:
    lda bit_table,x
    and joy1
    bne held
    lda bit_table,x
    and latch1
    bne seen
    lda #0                          ; never pressed: black on black
    beq emit
seen:
    lda #11                         ; dark grey
    bne emit
held:
    lda #1                          ; white
emit:
    jsr place
    inx
    cpx #5
    bne loop
    rts
.endproc

.proc draw_port2
    lda #1
    sta idx
    ldx #0
loop:
    lda bit_table,x
    and joy2
    bne held
    lda bit_table,x
    and latch2
    bne seen
    lda #0
    beq emit
seen:
    lda #11
    bne emit
held:
    lda #1
emit:
    jsr place
    inx
    cpx #5
    bne loop
    rts
.endproc

; The raw port byte. When a control lands on the wrong bit, the bit that moved
; says what it was mapped to.
.proc draw_raw
    lda joy1
    sta tmp
    lsr a
    lsr a
    lsr a
    lsr a
    jsr hex_char
    sta tmp+1
    lda #<(15 * VIEW_W + 6)
    sta dst_ptr
    lda #>(15 * VIEW_W + 6)
    sta dst_ptr+1
    lda #1
    jsr write_cell

    lda tmp
    and #$0F
    jsr hex_char
    sta tmp+1
    lda #<(15 * VIEW_W + 7)
    sta dst_ptr
    lda #>(15 * VIEW_W + 7)
    sta dst_ptr+1
    lda #1
    jsr write_cell
    rts
.endproc

.proc hex_char
    cmp #10
    bcc digit
    clc
    adc #'A' - 10
    rts
digit:
    clc
    adc #'0'
    rts
.endproc

; Zero means every control on port 2 has arrived at least once.
.proc draw_unseen
    lda #5
    sta idx
    ldx #0
tally:
    lda bit_table,x
    and latch1
    beq next
    dec idx
next:
    inx
    cpx #5
    bne tally

    lda idx
    clc
    adc #'0'
    sta tmp+1
    lda #<(17 * VIEW_W + 8)
    sta dst_ptr
    lda #>(17 * VIEW_W + 8)
    sta dst_ptr+1
    lda #1
    jsr write_cell
    rts
.endproc

.segment "RODATA"
bit_table: .byte JOY_UP, JOY_DOWN, JOY_LEFT, JOY_RIGHT, JOY_FIRE
; Screen offsets of the indicator cell, one left of each label.
p1_off: .word  5 * VIEW_W + 5, 11 * VIEW_W + 5,  8 * VIEW_W + 1
        .word  8 * VIEW_W + 9,  8 * VIEW_W + 15
p2_off: .word  5 * VIEW_W + 27, 11 * VIEW_W + 27, 8 * VIEW_W + 23
        .word  8 * VIEW_W + 31, 8 * VIEW_W + 35

.segment "MAPDATA"
inputtest_scr:
    .incbin "inputtest_scr.bin"
inputtest_col:
    .incbin "inputtest_col.bin"
