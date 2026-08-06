; testcard - pattern generator with motion, Atari 2600.
;
; Two kinds of kernel. The colour-bar panel writes COLUPF eight times *during*
; each visible scanline, which is this machine's signature trick and the only
; way to get vertical colour on it. The other panels drive the playfield from a
; table, one triple of registers per line, set during horizontal blank.

    processor 6502
    include "vcs.inc"

PANEL_COUNT  = 4
PANEL_FRAMES = 128
BAR_LINES    = 120              ; colour bars above, grey ramp below

    seg.u ram
    org $80
frame       ds 1
panel       ds 1
since       ds 1
line        ds 1
tickpos     ds 1
ptr0        ds 2
ptr1        ds 2
ptr2        ds 2
c0          ds 8                ; the eight bar colours, read by the kernel

    seg code
    org $F000

reset:
    sei
    cld
    ldx #0
    txa
clear:
    sta $00,x
    inx
    bne clear

    lda #$0E
    sta COLUPF
    lda #%00000001              ; reflected playfield
    sta CTRLPF
    lda #$0E
    sta COLUP0

frame_loop:
    lda #2
    sta VSYNC
    sta WSYNC
    sta WSYNC
    sta WSYNC
    lda #0
    sta VSYNC

    lda #43
    sta TIM64T
    inc frame

    ; --- panel selection, in vertical blank where there is time ---
    lda SWCHA                   ; joystick right steps the panel
    and #$80
    bne no_step
    lda since
    cmp #250
    beq no_step
    lda #250
    sta since
    jmp bump
no_step:
    inc since
    lda since
    cmp #PANEL_FRAMES
    bne no_bump
bump:
    lda #0
    sta since
    inc panel
    lda panel
    cmp #PANEL_COUNT
    bcc no_bump
    lda #0
    sta panel
no_bump:

    jsr set_pointers
    jsr position_tick

vblank_wait:
    lda INTIM
    bne vblank_wait
    sta WSYNC
    lda #0
    sta VBLANK

    ; --- parity flash: two lines of inverted background, every frame ---
    lda frame
    and #1
    beq parity_dark
    lda #$0E
    bne parity_set
parity_dark:
    lda #$00
parity_set:
    sta COLUBK
    sta WSYNC
    sta WSYNC
    lda #$00
    sta COLUBK

    lda panel
    beq bars_kernel
    jmp table_kernel

; --- colour bars -----------------------------------------------------------
; Eight writes to COLUPF per line at six cycles apiece: lda zero-page is 3 and
; sta is 3, so each bar is 18 colour clocks. Eight of them cover 144 of the 160
; visible, which is what six whole CPU cycles buys - a bar cannot be narrower
; than one store, and one store is nine pixels.
; Cycle budget, and why the bars are the width they are.
;
; A scanline is 76 CPU cycles, of which the first 22.67 are horizontal blank -
; writes there land before the beam reaches pixel 0 and are simply not seen.
; The first attempt started writing immediately after WSYNC and lost the first
; three bars into blank, which looked like the colour table being wrong.
;
; So: WSYNC (3) + iny (2) + nine NOPs (18) = 23 cycles, putting the first store
; at the left edge. Then eight bars of lda-immediate + sta = 5 cycles each.
;
; Five cycles is fifteen colour clocks, and that is the floor: a bar cannot be
; narrower than one store. Eight of them cover 120 of the 160 visible pixels,
; and the remaining 40 are black. Widening them to 20 pixels would need 6.67
; cycles apiece, and there is no way to spend two thirds of a cycle.
bars_kernel:
    lda #$FF                    ; playfield solid, so COLUPF paints everything
    sta PF0
    sta PF1
    sta PF2
    ldy #0
bars_line:
    sta WSYNC
    iny
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    lda #$0E                    ; white
    sta COLUPF
    lda #$1C                    ; yellow
    sta COLUPF
    lda #$9C                    ; cyan
    sta COLUPF
    lda #$CC                    ; green
    sta COLUPF
    lda #$6C                    ; magenta
    sta COLUPF
    lda #$46                    ; red
    sta COLUPF
    lda #$86                    ; blue
    sta COLUPF
    lda #$00                    ; black
    sta COLUPF
    cpy #BAR_LINES
    bne bars_line

    ; Grey ramp underneath: eight luminances of one hue, which is the ramp
    ; this machine has.
ramp_line:
    sta WSYNC
    iny
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    lda #$00
    sta COLUPF
    lda #$02
    sta COLUPF
    lda #$04
    sta COLUPF
    lda #$06
    sta COLUPF
    lda #$08
    sta COLUPF
    lda #$0A
    sta COLUPF
    lda #$0C
    sta COLUPF
    lda #$0E
    sta COLUPF
    cpy #VISIBLE_LINES
    bne ramp_line
    jmp kernel_done

; --- table-driven playfield ------------------------------------------------
table_kernel:
    lda #$0E
    sta COLUPF
    ldy #0
table_line:
    sta WSYNC
    lda (ptr0),y
    sta PF0
    lda (ptr1),y
    sta PF1
    lda (ptr2),y
    sta PF2
    iny
    cpy #VISIBLE_LINES
    bne table_line

kernel_done:
    lda #0
    sta PF0
    sta PF1
    sta PF2
    sta GRP0

    lda #2
    sta VBLANK
    lda #35
    sta TIM64T

    ; The frame ticker advances one cell of two pixels per frame, sixty to the
    ; lap - drawn as player 0 on the last visible lines, positioned during
    ; vertical blank by the standard divide-by-fifteen trick.
    lda tickpos
    clc
    adc #2
    cmp #120
    bcc tick_store
    lda #0
tick_store:
    sta tickpos

overscan_wait:
    lda INTIM
    bne overscan_wait
    sta WSYNC
    jmp frame_loop

; --- helpers ---------------------------------------------------------------
; Point ptr0/1/2 at this panel's playfield tables. Panel 0 is the bar kernel
; and needs none, so the table is indexed from panel 1.
set_pointers:
    lda panel
    beq load_bars
    sec
    sbc #1
    asl
    tax
    lda table_lo,x
    sta ptr0
    lda table_hi,x
    sta ptr0+1
    lda table_lo+1,x
    sta ptr1
    lda table_hi+1,x
    sta ptr1+1
    lda table_lo+2,x
    sta ptr2
    lda table_hi+2,x
    sta ptr2+1
    rts

load_bars:
    rts

; Player 0 to the pixel in tickpos. Dividing by fifteen counts whole
; 15-colour-clock chunks of the scanline; the remainder goes to HMP0 as a fine
; adjustment applied by HMOVE. There is no other way to place an object on
; this machine.
position_tick:
    sta WSYNC
    lda tickpos
    clc
    adc #16
    sec
divide:
    sbc #15
    bcs divide
    eor #7
    asl
    asl
    asl
    asl
    sta HMP0
    sta RESP0
    sta WSYNC
    sta HMOVE
    lda #$FF                    ; an 8-pixel block of player graphics
    sta GRP0
    rts

table_lo:
    .byte <hatch_pf0, <hatch_pf1, <hatch_pf2
    .byte <burst_pf0, <burst_pf1, <burst_pf2
    .byte <check_pf0, <check_pf1, <check_pf2
table_hi:
    .byte >hatch_pf0, >hatch_pf1, >hatch_pf2
    .byte >burst_pf0, >burst_pf1, >burst_pf2
    .byte >check_pf0, >check_pf1, >check_pf2

    org $F400
hatch_pf0:  incbin "hatch_pf0.bin"
hatch_pf1:  incbin "hatch_pf1.bin"
hatch_pf2:  incbin "hatch_pf2.bin"
burst_pf0:  incbin "burst_pf0.bin"
burst_pf1:  incbin "burst_pf1.bin"
burst_pf2:  incbin "burst_pf2.bin"
check_pf0:  incbin "check_pf0.bin"
check_pf1:  incbin "check_pf1.bin"
check_pf2:  incbin "check_pf2.bin"

    org $FFFC
    .word reset
    .word reset
