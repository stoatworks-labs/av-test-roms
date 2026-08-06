; Shared Master System runtime: boot, VDP setup, uploads, pad, vblank.
; Included by each program, which supplies `main`.

VDP_DATA    = 0xBE
VDP_CTRL    = 0xBF
PORT_A      = 0xDC              ; P1 directions + buttons, P2 up/down
PORT_B      = 0xDD              ; the rest of P2

NAME_TABLE  = 0x3800
SPRITE_ATTR = 0x3F00
VIEW_W      = 32
VIEW_H      = 24
MAP_BYTES   = VIEW_W * VIEW_H * 2

; Pad bits, active high once read_pad has inverted them.
PAD_UP    = 0x01
PAD_DOWN  = 0x02
PAD_LEFT  = 0x04
PAD_RIGHT = 0x08
PAD_B1    = 0x10
PAD_B2    = 0x20

    .area _HEADER (ABS)
    .org 0x0000
    di
    im 1
    jp init

    .org 0x0038                 ; interrupt mode 1 vector
    push af
    ld a, (frame_lo)
    inc a
    ld (frame_lo), a
    in a, (VDP_CTRL)            ; reading the status port clears the interrupt
    pop af
    ei
    reti

    .org 0x0066                 ; NMI: the Pause button, ignored
    retn

    .org 0x0100
init:
    ld sp, #0xDFF0
    call vdp_init
    xor a
    ld (frame_lo), a
    ld (tick_cell), a
    ld (pad1), a
    ld (pad2), a
    ei
    jp main

; --- VDP ------------------------------------------------------------------
vdp_init:
    ld hl, #vdp_regs
    ld b, #11
    ld c, #0x80                 ; register 0
vdp_loop:
    ld a, (hl)
    out (VDP_CTRL), a
    ld a, c
    out (VDP_CTRL), a
    inc hl
    inc c
    djnz vdp_loop
    ret

vdp_regs:
    .db 0x04                    ; mode 4
    .db 0xE0                    ; display on, vertical interrupt on
    .db 0xFF                    ; name table at 0x3800
    .db 0xFF
    .db 0xFF
    .db 0xFF                    ; sprite attribute table at 0x3F00
    .db 0xFB                    ; sprite tiles at 0x0000, where ours are
                                ; (bit 2 set would put them at 0x2000)
    .db 0x00                    ; border: palette entry 0
    .db 0x00                    ; horizontal scroll
    .db 0x00                    ; vertical scroll
    .db 0xFF                    ; no line interrupt

; HL = source, DE = VRAM address, BC = byte count.
vdp_write:
    ld a, e
    out (VDP_CTRL), a
    ld a, d
    or #0x40                    ; 0x40 in the high byte selects a VRAM write
    out (VDP_CTRL), a
copy_loop:
    ld a, (hl)
    out (VDP_DATA), a
    inc hl
    dec bc
    ld a, b
    or c
    jr nz, copy_loop
    ret

; HL = 32 palette bytes: 16 background then 16 sprite.
vdp_palette:
    xor a
    out (VDP_CTRL), a
    ld a, #0xC0                 ; 0xC0 selects a CRAM write
    out (VDP_CTRL), a
    ld b, #32
pal_loop:
    ld a, (hl)
    out (VDP_DATA), a
    inc hl
    djnz pal_loop
    ret

; A = palette entry, B = colour. One byte, which is how the checkerboard
; inverts.
vdp_cram_one:
    out (VDP_CTRL), a
    ld a, #0xC0
    out (VDP_CTRL), a
    ld a, b
    out (VDP_DATA), a
    ret

; --- input ----------------------------------------------------------------
read_pad:
    ld a, (pad1)
    ld (pad1_prev), a
    in a, (PORT_A)
    cpl
    and #0x3F
    ld (pad1), a
    ld b, a
    ld a, (pad1_prev)
    cpl
    and b
    ld (pad_new), a

    in a, (PORT_B)              ; P2 left/right/buttons live here
    cpl
    and #0x0F
    ld (pad2), a
    ret

; --- frame ----------------------------------------------------------------
; The interrupt bumps frame_lo; this waits for it to change. Polling a counter
; the ISR owns keeps every program's timing in one place.
vsync:
    ld a, (frame_lo)
    ld b, a
vsync_wait:
    ld a, (frame_lo)
    cp b
    jr z, vsync_wait

    ld a, (tick_cell)           ; one cell per frame, 60 to the lap
    inc a
    cp #60
    jr c, tick_store
    xor a
tick_store:
    ld (tick_cell), a
    ret

; --- sprites --------------------------------------------------------------
; The attribute table is split: 64 Y bytes at 0x3F00, then 64 (X, tile) pairs
; at 0x3F80. A Y of 0xD0 ends the list, which is how unused slots are hidden.
; A = slot, B = screen y, C = screen x, D = tile.
; The tile arrives in D, and the offset arithmetic needs a 16-bit register
; pair - so D gets pushed first. Using it as scratch without saving it made
; every sprite come out as tile 0, which is blank, which looks exactly like
; sprites being disabled.
sprite_set:
    ld (spr_slot), a
    push de

    ld e, a
    ld d, #0
    ld hl, #SPRITE_ATTR
    add hl, de
    ld a, l
    out (VDP_CTRL), a
    ld a, h
    or #0x40
    out (VDP_CTRL), a
    ld a, b
    dec a                       ; the table stores y-1
    out (VDP_DATA), a

    ld a, (spr_slot)
    ld e, a
    ld d, #0
    ld hl, #(SPRITE_ATTR + 0x80)
    add hl, de
    add hl, de                  ; two bytes an entry
    ld a, l
    out (VDP_CTRL), a
    ld a, h
    or #0x40
    out (VDP_CTRL), a
    ld a, c
    out (VDP_DATA), a
    pop de
    ld a, d                     ; VRAM auto-increments, so the tile follows
    out (VDP_DATA), a
    ret

sprite_end:                     ; A = first unused slot
    ld hl, #SPRITE_ATTR
    ld e, a
    ld d, #0
    add hl, de
    ld a, l
    out (VDP_CTRL), a
    ld a, h
    or #0x40
    out (VDP_CTRL), a
    ld a, #0xD0
    out (VDP_DATA), a
    ret

; RAM lives at 0xC000. Declared as equates rather than a reserved area: a
; .ds block inside the ABS image makes makebin emit padding out to 0xC000.
frame_lo   = 0xC000
tick_cell  = 0xC001
pad1       = 0xC002
pad2       = 0xC003
pad1_prev  = 0xC004
pad_new    = 0xC005
panel      = 0xC006
since      = 0xC007
manual     = 0xC008
scrollx    = 0xC009
latch1     = 0xC00A
slot       = 0xC00B
tmpb       = 0xC00C
spr_slot   = 0xC00E
