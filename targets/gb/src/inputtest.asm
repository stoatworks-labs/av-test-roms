; inputtest - controller mapping tester, Game Boy / Game Boy Color.

INCLUDE "runtime.inc"

; A glyph's tile index *is* its ASCII code (see tools/gen.py), so a digit's
; tile number is just its character code - written numerically because rgbasm
; wants a charmap before it will convert a string, and there is not one here.
DEF ASCII_0 EQU $30
DEF ASCII_9 EQU $39
DEF ASCII_A EQU $41

DEF TILE_SOLID EQU 3
DEF TILE_GREY  EQU 2
DEF TILE_BLANK EQU 0

SECTION "InputVars", WRAM0
Latch:   ds 1
Slot:    ds 1
Unseen:  ds 1
TmpMask: ds 1
TmpX:    ds 1
TmpY:    ds 1

SECTION "Inputtest", ROM0

Main:
    call LCDOff
    ld  hl, TileData
    ld  de, _VRAM
    ld  bc, 4096
    call CopyBytes
    ld  hl, MapData
    ld  de, _SCRN0
    call CopyMap
    ld  hl, AttrData
    call LoadAttributes
    ld  hl, PalData
    call LoadPalettes
    call LCDOn

    xor a
    ld  [Latch], a

.frame:
    call ReadPad

    ; SELECT+START together clears the latch, so a mapping can be re-walked
    ; without power-cycling.
    ld  a, [Pad]
    and PAD_SELECT | PAD_START
    cp  PAD_SELECT | PAD_START
    jr  nz, .keep
    xor a
    ld  [Latch], a
.keep:
    ld  a, [Latch]
    ld  b, a
    ld  a, [Pad]
    or  b
    ld  [Latch], a

    xor a
    ld  [Slot], a
    call DrawIndicators
    call DrawRaw
    call DrawUnseen
    call HideRest
    call WaitVBlank
    call OAMDMA
    jr  .frame

; --- indicators -----------------------------------------------------------
; Held wins over latched, so what you are pressing is still visible after
; everything has gone grey.
; The three table fields go through WRAM rather than being juggled in
; registers: SetSprite wants B, C, D and E all set at once, and there are not
; enough left over to also carry the mask and the loop index.
DrawIndicators:
    ld  b, 0                        ; slot, and the loop counter
.loop:
    ld  a, b                        ; hl = BtnTable + b * 3
    ld  h, 0
    ld  l, a
    add hl, hl
    ld  d, 0
    ld  e, a
    add hl, de
    ld  de, BtnTable
    add hl, de

    ld  a, [hl+]
    ld  [TmpMask], a
    ld  a, [hl+]
    ld  [TmpX], a
    ld  a, [hl]
    sub 9                           ; indicator sits above the label
    ld  [TmpY], a

    ld  a, [Pad]
    ld  c, a
    ld  a, [TmpMask]
    and c
    jr  nz, .held
    ld  a, [Latch]
    ld  c, a
    ld  a, [TmpMask]
    and c
    jr  nz, .seen
    ld  c, TILE_BLANK               ; never pressed
    jr  .emit
.seen:
    ld  c, TILE_GREY
    jr  .emit
.held:
    ld  c, TILE_SOLID
.emit:
    ld  a, [TmpX]
    ld  e, a
    ld  a, [TmpY]
    ld  d, a
    call SetSprite                  ; leaves B and C alone
    inc b
    ld  a, b
    cp  8
    jr  nz, .loop
    ld  a, 8
    ld  [Slot], a
    ret

; --- raw port word --------------------------------------------------------
; When a control lands on the wrong bit, this says which bit moved.
DrawRaw:
    ld  a, [Pad]
    swap a
    and $0F
    ld  d, 96
    ld  e, 32
    call HexDigit
    ld  a, [Pad]
    and $0F
    ld  d, 96
    ld  e, 40
    call HexDigit
    ret

; A = nibble, D = y, E = x. Converts to a glyph and draws it at the next slot.
HexDigit:
    add ASCII_0
    cp  ASCII_9 + 1
    jr  c, PutChar
    add ASCII_A - ASCII_9 - 1
    ; falls through

; A = character code, D = y, E = x. A glyph's tile index is its ASCII code.
PutChar:
    ld  c, a
    ld  a, [Slot]
    ld  b, a
    call SetSprite
    ld  a, [Slot]
    inc a
    ld  [Slot], a
    ret

; --- unseen count ---------------------------------------------------------
; Zero means every control has arrived at least once, which is the whole
; question this program exists to answer.
DrawUnseen:
    ld  a, [Latch]
    ld  b, a
    ld  c, 8                        ; controls not yet seen
    ld  d, 8                        ; bits left to examine
.count:
    srl b
    jr  nc, .next
    dec c
.next:
    dec d
    jr  nz, .count

    ld  a, c
    add ASCII_0
    ld  d, 112
    ld  e, 56
    call PutChar
    ret

; Park unused slots off-screen; a slot left over from an earlier frame keeps
; drawing whatever it drew then.
HideRest:
    ld  a, [Slot]
    ld  b, a
.loop:
    ld  a, b
    cp  40
    ret nc
    ld  h, HIGH(ShadowOAM)
    ld  a, b
    add a, a
    add a, a
    ld  l, a
    xor a
    ld  [hl], a                     ; y = 0 is off the top of the screen
    inc b
    jr  .loop

SECTION "InputData", ROM0

; mask, label x, label y - in pixels, matching tools/gen.py's layout.
BtnTable:
    db PAD_A,      144, 48
    db PAD_B,      120, 48
    db PAD_SELECT,  64, 72
    db PAD_START,   96, 72
    db PAD_RIGHT,   40, 48
    db PAD_LEFT,     8, 48
    db PAD_UP,      24, 32
    db PAD_DOWN,    24, 64

TileData:
    INCBIN "tiles.bin"
MapData:
    INCBIN "inputtest_map.bin"
AttrData:
    INCBIN "inputtest_attr.bin"
PalData:
    INCBIN "inputtest_pal.bin"
