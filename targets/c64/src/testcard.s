; testcard - pattern generator with motion, Commodore 64.

.include "c64.inc"

PANEL_COUNT  = 5
PANEL_FRAMES = 128

CHECK_CHAR   = 5
CHECK_ADDR   = CHARSET_AT + CHECK_CHAR * 8

TICK_SPR     = 0
SCROLL_SPR   = 1
PARITY_SPR   = 2

TICK_Y       = 184 + 50
SCROLL_Y     = 168 + 50
PARITY_Y     = 50

.segment "ZEROPAGE"
panel:   .res 1
since:   .res 1
manual:  .res 1
scrollx: .res 1

.segment "CODE"

.proc main
    lda #0
    sta panel
    sta since
    sta manual
    sta scrollx
    jsr load_panel

    lda #%00000111                  ; sprites 0..2 on
    sta VIC_SPREN
    lda #1                          ; white
    sta VIC_SPRCOL0
    sta VIC_SPRCOL0+1
    sta VIC_SPRCOL0+2
    lda #(SPRITES_AT / 64)
    sta SPRPTR + TICK_SPR
    lda #(SPRITES_AT / 64) + 1
    sta SPRPTR + SCROLL_SPR
    sta SPRPTR + PARITY_SPR

frame:
    jsr read_joy

    lda joy_new
    and #(JOY_FIRE | JOY_RIGHT)
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
    lda joy_new
    and #JOY_LEFT
    beq check_up
    dec panel
    bpl store_prev
    lda #PANEL_COUNT-1
    sta panel
store_prev:
    lda #1
    sta manual
    jsr load_panel

check_up:
    lda joy_new
    and #JOY_UP
    beq auto
    lda #0                          ; up resumes automatic cycling
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
    jsr update_check
    jsr vsync
    jmp frame
.endproc

; --- panel upload ---------------------------------------------------------
; Each map is 1000 bytes, which is not a shift, so the offset is reached by
; adding 1000 the required number of times.
.proc load_panel
    lda #<testcard_scr
    sta src_ptr
    lda #>testcard_scr
    sta src_ptr+1
    ldx panel
    beq scr_done
scr_add:
    lda src_ptr
    clc
    adc #<MAP_BYTES
    sta src_ptr
    lda src_ptr+1
    adc #>MAP_BYTES
    sta src_ptr+1
    dex
    bne scr_add
scr_done:

    lda #<testcard_col
    sta col_ptr
    lda #>testcard_col
    sta col_ptr+1
    ldx panel
    beq col_done
col_add:
    lda col_ptr
    clc
    adc #<MAP_BYTES
    sta col_ptr
    lda col_ptr+1
    adc #>MAP_BYTES
    sta col_ptr+1
    dex
    bne col_add
col_done:

    jsr upload
    rts
.endproc

; --- motion ---------------------------------------------------------------
.proc update_sprites
    ; Frame ticker: one 4-pixel cell per frame, 60 to the lap. Halved for
    ; sprite_at, plus the 12 that is half of the 24-pixel left border.
    lda tick_cell
    asl a
    clc
    adc #12
    ldx #TICK_SPR
    ldy #TICK_Y
    sty tmp
    jsr sprite_at

    ; 1 px/frame bar. The sprite is 24 pixels wide, so one is enough.
    inc scrollx
    lda scrollx
    cmp #148                        ; (320-24)/2, so it wraps off the right
    bcc keep
    lda #0
    sta scrollx
keep:
    lda scrollx
    clc
    adc #12
    ldx #SCROLL_SPR
    ldy #SCROLL_Y
    sty tmp
    jsr sprite_at

    ; Parity flash: moved off screen on even frames rather than blanked,
    ; because a sprite has no transparent tile to switch to.
    lda frame_lo
    and #1
    beq parity_off
    lda #164                        ; x = 328, over the grey backing cell
    ldy #PARITY_Y
    bne parity_go
parity_off:
    lda #0
    ldy #0
parity_go:
    sty tmp
    ldx #PARITY_SPR
    jsr sprite_at
    rts
.endproc

; The cheapest inversion in the suite: the character set is in RAM, so
; rewriting the eight bytes of the checkerboard character flips every cell
; using it at once. No screen writes at all.
.proc update_check
    lda panel
    cmp #3
    bne skip
    ldx #7
loop:
    lda CHECK_ADDR,x
    eor #$FF
    sta CHECK_ADDR,x
    dex
    bpl loop
skip:
    rts
.endproc

.segment "MAPDATA"
testcard_scr:
    .incbin "testcard_scr.bin"
testcard_col:
    .incbin "testcard_col.bin"
