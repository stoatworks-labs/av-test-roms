; Shared Game Boy runtime: header, boot, screen upload, joypad, vblank.
; Included by each program, which supplies Main.
;
; The ROM is CGB-enhanced and DMG-compatible: it runs on both, and uses colour
; only where a Game Boy Color is actually present. `IsCGB` holds the answer.

DEF rP1     EQU $FF00
DEF rDIV    EQU $FF04
DEF rIF     EQU $FF0F
DEF rLCDC   EQU $FF40
DEF rSTAT   EQU $FF41
DEF rSCY    EQU $FF42
DEF rSCX    EQU $FF43
DEF rLY     EQU $FF44
DEF rDMA    EQU $FF46
DEF rBGP    EQU $FF47
DEF rOBP0   EQU $FF48
DEF rVBK    EQU $FF4F
DEF rBCPS   EQU $FF68
DEF rBCPD   EQU $FF69
DEF rOCPS   EQU $FF6A
DEF rOCPD   EQU $FF6B
DEF rIE     EQU $FFFF

DEF _VRAM   EQU $8000
DEF _SCRN0  EQU $9800
DEF _OAM    EQU $FE00

DEF VIEW_W  EQU 20
DEF VIEW_H  EQU 18

; Joypad bits as assembled by ReadPad, active high.
DEF PAD_A      EQU %00000001
DEF PAD_B      EQU %00000010
DEF PAD_SELECT EQU %00000100
DEF PAD_START  EQU %00001000
DEF PAD_RIGHT  EQU %00010000
DEF PAD_LEFT   EQU %00100000
DEF PAD_UP     EQU %01000000
DEF PAD_DOWN   EQU %10000000

; Index 0 black, index 3 white - matching the CGB palettes the generator
; emits, so one tile reads the same way on both machines.
DEF BGP_STD EQU %00011011
; Sprites: index 3 white, so a marker is visible against a black field. The
; DMG default ($E4) makes index 3 black, i.e. invisible, which is exactly the
; failure that looks like "the sprite code is broken".
DEF OBP_STD EQU %00011000

SECTION "Entry", ROM0[$100]
    nop
    jp  Boot
    ; $104..$14F: the Nintendo logo and the header. The logo is Nintendo's
    ; artwork and is NOT reproduced here - it stays zero, so this will not boot
    ; on hardware, only in emulators that skip the boot ROM check. Everything
    ; else in the header is written by rgbfix. See ../README.md.
    ds  $150 - @, 0

SECTION "VBlankInt", ROM0[$40]
    reti

; Sprites are staged here and pushed to OAM by DMA once a frame.
;
; Writing OAM directly only works during vblank or hblank; at any other time
; the write is *silently dropped*. A frame's worth of sprite updates overruns
; vblank, so the later ones landed or did not depending on which PPU mode the
; CPU happened to be in - which looked exactly like one broken sprite slot.
; ALIGN[8] because the DMA source is a page number, not an address.
SECTION "ShadowOAM", WRAM0, ALIGN[8]
ShadowOAM:: ds 160

SECTION "Vars", WRAM0
IsCGB::     ds 1
FrameLo::   ds 1
FrameHi::   ds 1
TickCell::  ds 1
Pad::       ds 1
PadPrev::   ds 1
PadNew::    ds 1

; The CPU can reach nothing but HRAM while OAM DMA runs, so the routine that
; starts it and waits for it has to live there.
DEF OAMDMA_SIZE EQU 8           ; asserted against the real routine below

SECTION "HRAMCode", HRAM
hOAMDMA:: ds OAMDMA_SIZE

SECTION "Boot", ROM0

OAMDMAStart:
    ldh [rDMA], a
    ld  a, 40                   ; 40 x 4 cycles covers the 160-cycle transfer
.wait:
    dec a
    jr  nz, .wait
    ret
OAMDMAEnd:
ASSERT OAMDMAEnd - OAMDMAStart == OAMDMA_SIZE, \
    "OAMDMA_SIZE no longer matches the routine it reserves space for" 

; Push the shadow to OAM. Call it in vblank, once, after the sprites are set.
OAMDMA:
    ld  a, HIGH(ShadowOAM)
    jp  hOAMDMA

Boot:
    ; A holds $11 on a Game Boy Color and $01 on a DMG. This is the only
    ; chance to read it, so it is the first thing that happens.
    ld  b, a
    di
    ld  sp, $DFFF
    ld  a, b
    cp  $11
    ld  a, 0
    jr  nz, .notcgb
    inc a
.notcgb:
    ld  [IsCGB], a

    call LCDOff

    xor a
    ld  [FrameLo], a
    ld  [FrameHi], a
    ld  [TickCell], a
    ld  [Pad], a
    ld  [PadPrev], a

    ld  a, BGP_STD
    ldh [rBGP], a
    ld  a, OBP_STD
    ldh [rOBP0], a
    xor a
    ldh [rSCX], a
    ldh [rSCY], a

    ld  hl, OAMDMAStart         ; install the DMA routine in HRAM
    ld  de, hOAMDMA
    ld  bc, OAMDMA_SIZE
    call CopyBytes

    call ClearOAM

    ld  a, %00000001            ; vblank interrupt only
    ldh [rIE], a
    xor a
    ldh [rIF], a
    ei

    jp  Main

; --- LCD ------------------------------------------------------------------
; Everything is uploaded with the LCD off rather than dripped through vblank.
; It costs a black frame on a panel change, which the frame ticker reports.
LCDOff:
    ldh a, [rLCDC]
    and %10000000
    ret z                       ; already off
.wait:
    ldh a, [rLY]                ; turning the LCD off outside vblank can damage
    cp  145                     ; real hardware, so wait for it properly
    jr  nz, .wait
    xor a
    ldh [rLCDC], a
    ret

LCDOn:
    ld  a, %10010011            ; LCD on, BG map 0, tiles $8000, BG + OBJ on
    ldh [rLCDC], a
    ret

; --- uploads --------------------------------------------------------------
; HL = source, BC = length, DE = destination.
CopyBytes:
    ld  a, [hl+]
    ld  [de], a
    inc de
    dec bc
    ld  a, b
    or  c
    jr  nz, CopyBytes
    ret

; HL = 20x18 map source, DE = destination in VRAM. The tilemap is 32 wide and
; the screen is 20, so each row skips 12.
CopyMap:
    ld  b, VIEW_H
.row:
    ld  c, VIEW_W
.col:
    ld  a, [hl+]
    ld  [de], a
    inc de
    dec c
    jr  nz, .col
    ld  a, e
    add 32 - VIEW_W
    ld  e, a
    ld  a, d
    adc 0
    ld  d, a
    dec b
    jr  nz, .row
    ret

; HL = 64 bytes of CGB background palette. Ignored on a DMG.
LoadPalettes:
    ld  a, [IsCGB]
    or  a
    ret z
    ld  a, $80                  ; auto-increment
    ldh [rBCPS], a
    ld  c, 64
.loop:
    ld  a, [hl+]
    ldh [rBCPD], a
    dec c
    jr  nz, .loop

    ld  a, $80                  ; sprites: one palette, white ink
    ldh [rOCPS], a
    ld  hl, ObjPalCGB
    ld  c, 8
.obj:
    ld  a, [hl+]
    ldh [rOCPD], a
    dec c
    jr  nz, .obj
    ret

ObjPalCGB:
    dw  $0000, $294A, $56B5, $7FFF

; HL = 20x18 attribute source. VRAM bank 1 holds the CGB attribute map at the
; same addresses as the tilemap. On a DMG there is no bank 1 and no attributes.
LoadAttributes:
    ld  a, [IsCGB]
    or  a
    ret z
    ld  a, 1
    ldh [rVBK], a
    ld  de, _SCRN0
    call CopyMap
    xor a
    ldh [rVBK], a
    ret

ClearOAM:
    ld  hl, ShadowOAM
    ld  c, 160
    xor a
.loop:
    ld  [hl+], a
    dec c
    jr  nz, .loop
    call OAMDMA
    ret

; --- input ----------------------------------------------------------------
; Both halves of the matrix, assembled into one active-high byte.
ReadPad:
    ld  a, [Pad]
    ld  [PadPrev], a

    ld  a, $20                  ; select the d-pad half
    ldh [rP1], a
    ldh a, [rP1]
    ldh a, [rP1]
    cpl
    and $0F
    swap a
    ld  b, a

    ld  a, $10                  ; select the buttons half
    ldh [rP1], a
    ldh a, [rP1]
    ldh a, [rP1]
    ldh a, [rP1]
    ldh a, [rP1]
    cpl
    and $0F
    or  b
    ld  [Pad], a

    ld  b, a
    ld  a, [PadPrev]
    cpl
    and b
    ld  [PadNew], a

    ld  a, $30                  ; deselect
    ldh [rP1], a
    ret

; --- frame ----------------------------------------------------------------
; halt with IME set returns at the start of vblank. Sprites are staged in
; ShadowOAM beforehand and pushed across with OAMDMA immediately after; see the
; note on the ShadowOAM section for why writing OAM directly does not work.
WaitVBlank:
    halt
    nop
    ld  a, [FrameLo]
    inc a
    ld  [FrameLo], a
    jr  nz, .nocarry
    ld  a, [FrameHi]
    inc a
    ld  [FrameHi], a
.nocarry:
    ld  a, [TickCell]           ; one cell per frame, 60 to the lap
    inc a
    cp  60
    jr  c, .store
    xor a
.store:
    ld  [TickCell], a
    ret

; --- sprites --------------------------------------------------------------
; SetSprite: B = slot, C = tile, D = screen y, E = screen x.
; OAM stores y+16 and x+8, which is the offset every "my sprite is invisible"
; bug on this platform comes down to.
SetSprite:
    ld  h, HIGH(ShadowOAM)
    ld  a, b
    add a, a
    add a, a
    ld  l, a
    ld  a, d
    add 16
    ld  [hl+], a
    ld  a, e
    add 8
    ld  [hl+], a
    ld  a, c
    ld  [hl+], a
    xor a                       ; attributes: OBJ palette 0, no flip
    ld  [hl], a
    ret
