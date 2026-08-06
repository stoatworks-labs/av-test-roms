; inputtest - controller mapping tester, NES.
;
; The background never changes: button boxes and labels are in the nametable,
; and everything that moves is a sprite. That sidesteps the vblank budget
; entirely - there is no frame on which this program writes to the PPU outside
; the sprite DMA the runtime already does.

.include "runtime.inc"

.segment "ZEROPAGE"
latch1: .res 1
latch2: .res 1
slot:   .res 1
count:  .res 1

.segment "CODE"

.proc main
    lda #<inputtest_nt
    sta src_ptr
    lda #>inputtest_nt
    sta src_ptr+1
    lda #<inputtest_pal
    sta pal_ptr
    lda #>inputtest_pal
    sta pal_ptr+1
    jsr load_screen

    lda #0
    sta latch1
    sta latch2

frame:
    jsr read_pads

    ; SELECT+START together clears the latch, so a mapping can be re-walked
    ; without resetting the console.
    lda pad1
    and #(BTN_SELECT | BTN_START)
    cmp #(BTN_SELECT | BTN_START)
    bne keep
    lda #0
    sta latch1
    sta latch2
keep:
    lda latch1
    ora pad1
    sta latch1
    lda latch2
    ora pad2
    sta latch2

    lda #0
    sta slot
    jsr draw_pad1
    jsr draw_pad2
    jsr draw_raw
    jsr draw_unseen
    jsr hide_rest

    jsr wait_frame
    jmp frame
.endproc

; --- indicators -----------------------------------------------------------
; Held wins over latched, so you can still see what you are pressing after
; everything has gone grey.
.proc draw_pad1
    ldx #0
loop:
    lda btn_mask,x
    and pad1
    bne held
    lda btn_mask,x
    and latch1
    bne seen
    lda #0                      ; never pressed: blank tile
    beq emit
seen:
    lda #3                      ; solid tile painting palette entry 3, grey
    bne emit
held:
    lda #1                      ; solid tile painting palette entry 1, white
emit:
    sta sprite_tile
    lda #0
    sta sprite_attr
    txa
    pha
    lda btn_y,x                 ; read both tables before X is reloaded
    sec
    sbc #9                      ; P1 indicator sits above the label
    tay
    lda btn_x,x
    tax
    lda slot
    jsr set_sprite
    inc slot
    pla
    tax
    inx
    cpx #8
    bne loop
    rts
.endproc

.proc draw_pad2
    ldx #0
loop:
    lda btn_mask,x
    and pad2
    bne held
    lda btn_mask,x
    and latch2
    bne seen
    lda #0
    beq emit
seen:
    lda #3
    bne emit
held:
    lda #1
emit:
    sta sprite_tile
    lda #0
    sta sprite_attr
    txa
    pha
    lda btn_y,x
    clc
    adc #8                      ; P2 indicator sits below the label
    tay
    lda btn_x,x
    tax
    lda slot
    jsr set_sprite
    inc slot
    pla
    tax
    inx
    cpx #8
    bne loop
    rts
.endproc

; --- raw port words -------------------------------------------------------
; When a control lands on the wrong bit, this is what says which bit moved.
.proc draw_raw
    lda pad1
    ldx #56                     ; x pixel
    ldy #160                    ; y pixel
    jsr hex_byte
    lda pad2
    ldx #56
    ldy #176
    jsr hex_byte
    rts
.endproc

; A = value, X = x, Y = y. Two sprites, high nibble then low.
.proc hex_byte
    sta tmp
    stx tmp+1
    sty count                   ; borrow: y position
    lda tmp
    lsr a
    lsr a
    lsr a
    lsr a
    jsr hex_digit
    ldx tmp+1
    ldy count
    lda slot
    jsr set_sprite
    inc slot

    lda tmp
    and #$0F
    jsr hex_digit
    lda tmp+1
    clc
    adc #8
    tax
    ldy count
    lda slot
    jsr set_sprite
    inc slot
    rts
.endproc

; A = nibble -> sprite_tile set to that character's tile (tile index = ASCII).
.proc hex_digit
    cmp #10
    bcc digit
    clc
    adc #'A' - 10
    bne store
digit:
    clc
    adc #'0'
store:
    sta sprite_tile
    lda #0
    sta sprite_attr
    rts
.endproc

; --- unseen count ---------------------------------------------------------
; Zero means every control on both pads has arrived at least once, which is
; the whole question this program exists to answer.
.proc draw_unseen
    lda #16
    sta count
    ldx #0
tally:
    lda btn_mask,x
    and latch1
    beq no1
    dec count
no1:
    lda btn_mask,x
    and latch2
    beq no2
    dec count
no2:
    inx
    cpx #8
    bne tally

    lda count
    ldx #0
tens:
    cmp #10
    bcc units
    sec
    sbc #10
    inx
    bne tens
units:
    sta tmp
    txa
    clc
    adc #'0'
    sta sprite_tile
    lda #0
    sta sprite_attr
    ldx #64
    ldy #200
    lda slot
    jsr set_sprite
    inc slot

    lda tmp
    clc
    adc #'0'
    sta sprite_tile
    ldx #72
    ldy #200
    lda slot
    jsr set_sprite
    inc slot
    rts
.endproc

; Park every unused sprite off the bottom of the screen; otherwise a slot left
; over from an earlier frame keeps drawing whatever it drew then.
.proc hide_rest
    lda slot
    asl a
    asl a
    tax
clearloop:
    lda #$FF
    sta oam,x
    inx
    inx
    inx
    inx
    bne clearloop
    rts
.endproc

.segment "RODATA"
; Bit, then the pixel position of the label the indicator belongs to.
btn_mask: .byte BTN_A, BTN_B, BTN_SELECT, BTN_START, BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT
btn_x:    .byte 200,   168,   96,          128,       40,     40,       16,       64
btn_y:    .byte 80,    80,    96,          96,        64,     96,       80,       80

inputtest_nt:
    .incbin "inputtest_nt.bin"
inputtest_pal:
    .incbin "inputtest_pal.bin"
