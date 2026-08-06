; inputtest - controller mapping tester, Atari 2600.
;
; There is nowhere to draw a picture of a joystick: no character set, no tile
; map, 128 bytes of RAM. So each control gets a horizontal band of the screen,
; twelve bands of sixteen scanlines, and the band is drawn solid while the
; control is held and as edge blocks once it has been seen. Ten controls, two
; ports, and the reading is by position - which is the same information the
; other targets give with labels.

    processor 6502
    include "vcs.inc"

BANDS      = 12
BAND_LINES = 16

    seg.u ram
    org $80
frame       ds 1
latch0      ds 1                ; port 0: up down left right fire
latch1      ds 1
bandpf0     ds BANDS
bandpf1     ds BANDS
bandpf2     ds BANDS
held        ds 1
seen        ds 1

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

    lda #%00000001              ; reflected playfield
    sta CTRLPF
    lda #$00
    sta COLUBK
    ; The clear loop above zeroes every TIA register, COLUPF included, so the
    ; playfield starts black on black - which looks exactly like a kernel that
    ; never runs.
    lda #$0E
    sta COLUPF

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

    jsr read_inputs
    jsr build_bands

vblank_wait:
    lda INTIM
    bne vblank_wait
    sta WSYNC
    lda #0
    sta VBLANK

    ; --- kernel ---
    ; PF0 is written ten cycles into the line and PF1 seventeen, both inside
    ; the 22.67 cycles of horizontal blank. PF2 lands about four pixels into
    ; the visible area, which is harmless: it controls pixels 48 to 79.
    ldx #0
    ldy #BAND_LINES
kernel:
    sta WSYNC
    lda bandpf0,x
    sta PF0
    lda bandpf1,x
    sta PF1
    lda bandpf2,x
    sta PF2
    dey
    bne kernel
    ldy #BAND_LINES
    inx
    cpx #BANDS
    bne kernel

    lda #0
    sta PF0
    sta PF1
    sta PF2

    lda #2
    sta VBLANK
    lda #35
    sta TIM64T
overscan_wait:
    lda INTIM
    bne overscan_wait
    sta WSYNC
    jmp frame_loop

; --- input ----------------------------------------------------------------
; SWCHA carries both sticks, port 0 in the high nibble, and every bit is
; active low. The fire buttons are elsewhere again, in INPT4 and INPT5, bit 7.
read_inputs:
    lda SWCHA
    lsr
    lsr
    lsr
    lsr                         ; port 0 directions into the low nibble
    eor #$0F
    and #$0F
    sta held
    bit INPT4                   ; bit 7 clear means held
    bmi no_fire0
    lda held
    ora #$10
    sta held
no_fire0:
    lda latch0
    ora held
    sta latch0

    lda SWCHA
    eor #$0F
    and #$0F
    sta seen                    ; borrowed: port 1 directions
    bit INPT5
    bmi no_fire1
    lda seen
    ora #$10
    sta seen
no_fire1:
    lda latch1
    ora seen
    sta latch1

    ; Both fire buttons at once clears the latches.
    lda held
    and #$10
    beq no_clear
    lda seen
    and #$10
    beq no_clear
    lda #0
    sta latch0
    sta latch1
no_clear:
    rts

; --- band construction -----------------------------------------------------
; Bands 0..4 are port 0's five controls, 6..10 are port 1's, and 5 and 11 are
; left blank as separators. Held wins over latched.
build_bands:
    ldx #0
    ldy #0                      ; bit index within the port
build_p0:
    lda bit_masks,y
    and held
    bne p0_held
    lda bit_masks,y
    and latch0
    bne p0_seen
    lda unseen_marks,y          ; never pressed: one block, staggered so
    sta bandpf0,x               ; adjacent bands do not merge into one bar
    lda #0
    sta bandpf1,x
    sta bandpf2,x
    jmp p0_next
p0_seen:
    lda #$F0                    ; edge blocks: seen but not held
    sta bandpf0,x
    lda #0
    sta bandpf1,x
    sta bandpf2,x
    jmp p0_next
p0_held:
    lda #$F0                    ; solid across: held now
    sta bandpf0,x
    lda #$FF
    sta bandpf1,x
    sta bandpf2,x
p0_next:
    inx
    iny
    cpy #5
    bne build_p0

    lda #0                      ; band 5, separator
    sta bandpf0,x
    sta bandpf1,x
    sta bandpf2,x
    inx

    ldy #0
build_p1:
    lda bit_masks,y
    and latch1
    bne p1_seen
    lda unseen_marks,y
    sta bandpf0,x
    lda #0
    sta bandpf1,x
    sta bandpf2,x
    jmp p1_next
p1_seen:
    lda #$F0
    sta bandpf0,x
    lda #$FF
    sta bandpf1,x
    lda #0
    sta bandpf2,x
p1_next:
    inx
    iny
    cpy #5
    bne build_p1

    lda #0                      ; band 11, separator
    sta bandpf0,x
    sta bandpf1,x
    sta bandpf2,x
    rts

bit_masks:
    .byte $01, $02, $04, $08, $10   ; up, down, left, right, fire
; PF0 uses bits 4..7 left to right, so these are four distinct x positions.
unseen_marks:
    .byte $10, $20, $40, $80, $10

    org $FFFC
    .word reset
    .word reset
