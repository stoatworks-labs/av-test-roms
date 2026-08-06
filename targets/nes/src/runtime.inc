; Shared NES runtime: iNES header, reset, NMI, screen upload, pad reading.
; Included by each program, which supplies `main`.

PPUCTRL   = $2000
PPUMASK   = $2001
PPUSTATUS = $2002
OAMADDR   = $2003
PPUSCROLL = $2005
PPUADDR   = $2006
PPUDATA   = $2007
OAMDMA    = $4014
JOY1      = $4016
JOY2      = $4017

; Button bits as they arrive from the shift register, MSB first.
BTN_A      = $80
BTN_B      = $40
BTN_SELECT = $20
BTN_START  = $10
BTN_UP     = $08
BTN_DOWN   = $04
BTN_LEFT   = $02
BTN_RIGHT  = $01

.segment "HEADER"
    .byte "NES", $1A
    .byte 2                 ; 2 x 16 KB PRG
    .byte 1                 ; 1 x  8 KB CHR
    .byte $01               ; mapper 0, vertical mirroring
    .byte $00
    .res  8, 0

.segment "ZEROPAGE"
nmi_count:   .res 1
src_ptr:     .res 2
pal_ptr:     .res 2
pad1:        .res 1
pad2:        .res 1
pad1_prev:   .res 1
pad2_prev:   .res 1
frame_lo:    .res 1
frame_hi:    .res 1
tick_cell:   .res 1         ; 0..59, advanced once per frame
flip_on:     .res 1         ; non-zero: rewrite palette entries 1/2 in vblank
flip_a:      .res 1
flip_b:      .res 1
tmp:         .res 2

.segment "OAMBUF"
oam:         .res 256

.segment "CODE"

; --- NMI ------------------------------------------------------------------
; Everything that touches the PPU happens here, in vblank, in one order:
; sprite DMA, then the optional palette write, then the address and scroll
; reset. The reset has to come last - any write to PPUADDR corrupts the scroll
; position, so a palette write after it would shift the whole screen sideways.
.proc nmi
    pha
    txa
    pha
    tya
    pha

    lda #0
    sta OAMADDR
    lda #>oam
    sta OAMDMA

    lda flip_on
    beq no_flip
    lda PPUSTATUS
    lda #$3F
    sta PPUADDR
    lda #$01
    sta PPUADDR
    lda flip_a
    sta PPUDATA
    lda flip_b
    sta PPUDATA
no_flip:

    lda PPUSTATUS
    lda #0
    sta PPUADDR
    sta PPUADDR
    sta PPUSCROLL
    sta PPUSCROLL

    inc nmi_count
    pla
    tay
    pla
    tax
    pla
    rti
.endproc

.proc irq
    rti
.endproc

; --- reset ----------------------------------------------------------------
.proc reset
    sei
    cld
    ldx #$40
    stx JOY2                ; silence the APU frame IRQ
    ldx #$FF
    txs
    inx                     ; x = 0
    stx PPUCTRL
    stx PPUMASK
    stx $4010               ; and the DMC IRQ

    bit PPUSTATUS
wait1:
    bit PPUSTATUS
    bpl wait1

    lda #0
    tax
clear:
    sta $0000,x
    sta $0100,x
    sta $0300,x
    sta $0400,x
    sta $0500,x
    sta $0600,x
    sta $0700,x
    lda #$FF                ; park every sprite off the bottom of the screen
    sta $0200,x
    lda #0
    inx
    bne clear

wait2:
    bit PPUSTATUS
    bpl wait2

    jmp main
.endproc

; --- screen upload --------------------------------------------------------
; 1 KB of nametable will not fit in one vblank, so rendering is switched off
; for the transfer. That costs a black frame on every panel change, which the
; frame ticker duly reports - see ../README.md.
.proc load_screen
    lda #0
    sta PPUMASK
    sta PPUCTRL

    lda PPUSTATUS
    lda #$3F
    sta PPUADDR
    lda #$00
    sta PPUADDR
    ldy #0
pal_bg:
    lda (pal_ptr),y
    sta PPUDATA
    iny
    cpy #16
    bne pal_bg
    ldy #0
pal_spr:
    lda sprite_palette,y
    sta PPUDATA
    iny
    cpy #16
    bne pal_spr

    lda PPUSTATUS
    lda #$20
    sta PPUADDR
    lda #$00
    sta PPUADDR
    ldx #4                  ; four 256-byte pages = 960 tiles + 64 attributes
    ldy #0
nt_page:
    lda (src_ptr),y
    sta PPUDATA
    iny
    bne nt_page
    inc src_ptr+1
    dex
    bne nt_page

    lda PPUSTATUS
    lda #0
    sta PPUADDR
    sta PPUADDR
    sta PPUSCROLL
    sta PPUSCROLL

    lda #%10000000          ; NMI on, background pattern table 0
    sta PPUCTRL
    lda #%00011110          ; background + sprites, no clipping
    sta PPUMASK
    rts
.endproc

; --- input ----------------------------------------------------------------
.proc read_pads
    lda pad1
    sta pad1_prev
    lda pad2
    sta pad2_prev

    lda #1
    sta JOY1
    lda #0
    sta JOY1

    ldx #8
shift:
    lda JOY1
    lsr a
    rol pad1
    lda JOY2
    lsr a
    rol pad2
    dex
    bne shift
    rts
.endproc

; --- frame ----------------------------------------------------------------
.proc wait_frame
    lda nmi_count
spin:
    cmp nmi_count
    beq spin

    inc frame_lo
    bne no_carry
    inc frame_hi
no_carry:
    ; One ticker cell per frame, wrapping at 60: one lap is one second of NTSC.
    inc tick_cell
    lda tick_cell
    cmp #60
    bcc done
    lda #0
    sta tick_cell
done:
    rts
.endproc

; --- sprite helpers -------------------------------------------------------
; set_sprite: A = slot, X = x, Y = y, tile/attr from sprite_tile/sprite_attr.
; Uses its own scratch rather than `tmp`, so callers can keep values across a
; call - which several of them need to.
.proc set_sprite
    asl a
    asl a
    stx spx
    sty spy
    tay
    lda spy
    sta oam,y               ; Y position
    iny
    lda sprite_tile
    sta oam,y
    iny
    lda sprite_attr
    sta oam,y
    iny
    lda spx
    sta oam,y               ; X position
    rts
.endproc

.segment "ZEROPAGE"
sprite_tile: .res 1
sprite_attr: .res 1
spx:         .res 1
spy:         .res 1

.segment "RODATA"
sprite_palette:
    .byte $0F, $20, $16, $10        ; black, white, red, light grey
    .byte $0F, $20, $16, $10
    .byte $0F, $20, $16, $10
    .byte $0F, $20, $16, $10

.segment "CHARS"
    .incbin "chr.bin"

.segment "VECTORS"
    .addr nmi, reset, irq
