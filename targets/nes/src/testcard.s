; testcard - pattern generator with motion, NES.
;
; The five panels are whole nametables uploaded with rendering off. Every
; moving element is a sprite, because NROM has no scanline interrupt and the
; NES cannot scroll part of a background without one.

.include "runtime.inc"

PANEL_COUNT  = 5
PANEL_FRAMES = 128

TICK_Y   = 215                  ; row 27, where the track is
SCROLL_Y = 199
PARITY_X = 240

.segment "ZEROPAGE"
panel:  .res 1
since:  .res 1
manual: .res 1
newpad: .res 1

.segment "CODE"

.proc main
    lda #0
    sta panel
    sta since
    sta manual
    jsr load_panel

frame:
    jsr read_pads

    lda pad1                    ; newly pressed this frame
    eor pad1_prev
    and pad1
    sta newpad

    lda newpad
    and #(BTN_A | BTN_RIGHT)
    beq check_prev
    inc panel
    lda panel
    cmp #PANEL_COUNT
    bcc store_next
    lda #0
store_next:
    sta panel
    lda #1
    sta manual
    jsr load_panel

check_prev:
    lda newpad
    and #(BTN_B | BTN_LEFT)
    beq check_start
    dec panel
    bpl store_prev
    lda #PANEL_COUNT-1
    sta panel
store_prev:
    lda #1
    sta manual
    jsr load_panel

check_start:
    lda newpad
    and #BTN_START
    beq auto
    lda #0                      ; START resumes automatic cycling
    sta manual

auto:
    lda manual
    bne motion
    inc since
    lda since
    cmp #PANEL_FRAMES
    bcc motion
    lda #0
    sta since
    inc panel
    lda panel
    cmp #PANEL_COUNT
    bcc store_auto
    lda #0
store_auto:
    sta panel
    jsr load_panel

motion:
    jsr update_sprites
    jsr update_flip
    jsr wait_frame
    jmp frame
.endproc

; --- panel upload ---------------------------------------------------------
.proc load_panel
    ; Each panel is $400 bytes, so the panel index scales into the high byte
    ; alone and the low byte never changes.
    lda panel
    asl a
    asl a
    clc
    adc #>testcard_nt
    sta src_ptr+1
    lda #<testcard_nt
    sta src_ptr

    lda panel                   ; 16 bytes of palette each
    asl a
    asl a
    asl a
    asl a
    clc
    adc #<testcard_pal
    sta pal_ptr
    lda #>testcard_pal
    adc #0
    sta pal_ptr+1

    jsr load_screen

    ; Only the checkerboard animates its palette.
    lda #0
    sta flip_on
    lda panel
    cmp #3
    bne done
    lda #1
    sta flip_on
done:
    rts
.endproc

; --- motion ---------------------------------------------------------------
.proc update_sprites
    lda #1                      ; solid tile, sprite palette entry 1 = white
    sta sprite_tile
    lda #0
    sta sprite_attr

    ; Frame ticker: one cell of 4 pixels per frame, 60 cells to the lap.
    lda tick_cell
    asl a
    asl a
    tax
    ldy #TICK_Y
    lda #0
    jsr set_sprite

    ; 1 px/frame scroll bar, four sprites making 32 pixels.
    lda frame_lo
    sta tmp
    ldx #0
scroll:
    txa
    pha
    lda tmp
    tax
    ldy #SCROLL_Y
    pla
    pha
    clc
    adc #1                      ; slots 1..4
    jsr set_sprite
    lda tmp
    clc
    adc #8
    sta tmp
    pla
    tax
    inx
    cpx #4
    bne scroll

    ; Parity flash: solid on odd frames, transparent on even, over the grey
    ; box the layout puts behind it.
    lda frame_lo
    and #1
    sta sprite_tile             ; tile 1 = solid, tile 0 = blank
    ldx #PARITY_X
    ldy #0
    lda #5
    jsr set_sprite
    rts
.endproc

; Two bytes a frame, against the GBA build's 16 DMA transfers for the same
; inversion. This is what a palette gets you.
.proc update_flip
    lda flip_on
    beq skip
    lda frame_lo
    and #1
    beq even
    lda #$0F                    ; black / white
    sta flip_a
    lda #$20
    sta flip_b
    rts
even:
    lda #$20                    ; white / black
    sta flip_a
    lda #$0F
    sta flip_b
skip:
    rts
.endproc

.segment "RODATA"
testcard_nt:
    .incbin "testcard_nt.bin"
testcard_pal:
    .incbin "testcard_pal.bin"
