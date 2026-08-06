; Shared C64 runtime: BASIC stub, VIC setup, screen upload, joystick, raster
; sync. Included by each program, which supplies `main`.

VIC_SPR0X   = $D000
VIC_SPR0Y   = $D001
VIC_SPRXMSB = $D010
VIC_RASTER  = $D012
VIC_SPREN   = $D015
VIC_SPRCOL0 = $D027
VIC_BORDER  = $D020
VIC_BG      = $D021
VIC_MEMPTR  = $D018
CIA1_PRA    = $DC00                 ; joystick port 2
CIA1_PRB    = $DC01                 ; joystick port 1, shared with the keyboard

SCREEN      = $0400
COLOUR      = $D800
SPRPTR      = SCREEN + $3F8
CHARSET_AT  = $2000
SPRITES_AT  = $2800

VIEW_W      = 40
VIEW_H      = 25
MAP_BYTES   = 1000

; Joystick bits, active high once read_joy has inverted them.
JOY_UP    = $01
JOY_DOWN  = $02
JOY_LEFT  = $04
JOY_RIGHT = $08
JOY_FIRE  = $10

.segment "LOADADDR"
    .word   $0801

.segment "CODE"
; BASIC line 10 SYS 2061, which is the byte after this stub.
    .word   basic_end
    .word   10
    .byte   $9E, "2061", 0
basic_end:
    .word   0

    jmp     start

.segment "ZEROPAGE"
src_ptr:   .res 2
dst_ptr:   .res 2
col_ptr:   .res 2
joy1:      .res 1
joy2:      .res 1
joy1_prev: .res 1
joy_new:   .res 1
frame_lo:  .res 1
frame_hi:  .res 1
tick_cell: .res 1
tmp:       .res 2

.segment "CODE"

start:
    sei
    lda #$00
    sta VIC_BORDER
    sta VIC_BG
    ; Screen at $0400, charset at $2000: bits 7-4 are screen/$0400, bits 3-1
    ; are charset/$0800.
    lda #$18
    sta VIC_MEMPTR
    lda #$00
    sta frame_lo
    sta frame_hi
    sta tick_cell
    sta joy1
    sta joy2
    sta VIC_SPREN
    cli
    jmp main

; --- screen upload --------------------------------------------------------
; src_ptr -> screen characters, col_ptr -> colour RAM. 1000 bytes each, done
; as four page copies because a 1000-byte loop needs 16-bit indexing and this
; does not.
.proc load_screen
    ldx #0
page:
    ldy #0
copy:
    lda (src_ptr),y
    sta (dst_ptr),y
    iny
    bne copy
    inc src_ptr+1
    inc dst_ptr+1
    inx
    cpx #4
    bne page
    rts
.endproc

; Copies both maps. A = panel index is handled by the caller setting the
; pointers; this just moves 1000 bytes twice.
.proc upload
    ; characters -> $0400
    lda #<SCREEN
    sta dst_ptr
    lda #>SCREEN
    sta dst_ptr+1
    jsr load_screen
    ; colours -> $D800
    lda col_ptr
    sta src_ptr
    lda col_ptr+1
    sta src_ptr+1
    lda #<COLOUR
    sta dst_ptr
    lda #>COLOUR
    sta dst_ptr+1
    jsr load_screen
    rts
.endproc

; --- input ----------------------------------------------------------------
; Port 2 is the clean one. Port 1 shares its lines with the keyboard matrix,
; so it reads as pressed whenever certain keys are down - which is a property
; of the machine, not a mapping fault, and inputtest says so on screen.
.proc read_joy
    lda joy1
    sta joy1_prev

    lda CIA1_PRA
    eor #$FF
    and #$1F
    sta joy1

    lda CIA1_PRB
    eor #$FF
    and #$1F
    sta joy2

    lda joy1_prev
    eor #$FF
    and joy1
    sta joy_new
    rts
.endproc

; --- frame ----------------------------------------------------------------
; Wait for the raster to leave the visible area and come back. Polling rather
; than an interrupt keeps every program's timing in one place.
.proc vsync
wait_low:
    lda VIC_RASTER
    cmp #250
    bne wait_low
wait_high:
    lda VIC_RASTER
    cmp #250
    beq wait_high

    inc frame_lo
    bne no_carry
    inc frame_hi
no_carry:
    inc tick_cell
    lda tick_cell
    cmp #60
    bcc done
    lda #0
    sta tick_cell
done:
    rts
.endproc

; --- sprites --------------------------------------------------------------
; X = sprite number, A = x/2, `tmp` = y. Both are already in VIC coordinates:
; the visible screen starts at sprite x=24, y=50, so a screen pixel (px,py) is
; (px+24, py+50). Passing x halved is what lets one byte cover all 320 columns;
; the ninth bit goes to the MSB register.
.proc sprite_at
    sta tmp+1
    txa
    asl a
    tay                             ; y = sprite * 2, the register pair offset
    lda tmp+1
    asl a
    sta VIC_SPR0X,y
    lda tmp
    sta VIC_SPR0X+1,y
    bcc no_msb
    lda VIC_SPRXMSB
    ora msb_bit,x
    sta VIC_SPRXMSB
    rts
no_msb:
    lda VIC_SPRXMSB
    and msb_clear,x
    sta VIC_SPRXMSB
    rts
.endproc

.segment "RODATA"
msb_bit:   .byte $01, $02, $04, $08, $10, $20, $40, $80
msb_clear: .byte $FE, $FD, $FB, $F7, $EF, $DF, $BF, $7F

.segment "CHARS"
    .incbin "charset.bin"

; Sprite 0 is a 4-pixel bar for the frame ticker, sprite 1 a solid block for
; the 1px/frame scroll, sprite 2 the parity flash.
.segment "SPRDATA"
sprite_tick:
    .repeat 21
    .byte $F0, $00, $00
    .endrep
    .byte 0
sprite_block:
    .repeat 21
    .byte $FF, $FF, $FF
    .endrep
    .byte 0
