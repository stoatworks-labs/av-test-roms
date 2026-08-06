; testcard - pattern generator with motion, Game Boy / Game Boy Color.

INCLUDE "runtime.inc"

DEF PANEL_COUNT  EQU 5
DEF PANEL_FRAMES EQU 128
DEF MAP_BYTES    EQU VIEW_W * VIEW_H          ; 360
DEF PAL_BYTES    EQU 64

DEF TILE_TICK    EQU 11                        ; 2px mark
DEF TILE_SOLID   EQU 3                         ; solid, ink index 3
DEF TILE_BLANK   EQU 0                         ; index 0: transparent as a sprite

DEF TICK_Y       EQU 136
DEF SCROLL_Y     EQU 124
DEF PARITY_X     EQU 152

SECTION "TestcardVars", WRAM0
Panel:   ds 1
Since:   ds 1
Manual:  ds 1
ScrollX: ds 1

SECTION "Testcard", ROM0

Main:
    call LCDOff
    ld  hl, TileData                ; tiles are the same on every panel
    ld  de, _VRAM
    ld  bc, 4096
    call CopyBytes

    xor a
    ld  [Panel], a
    ld  [Since], a
    ld  [Manual], a
    ld  [ScrollX], a
    call LoadPanel

.frame:
    call ReadPad

    ld  a, [PadNew]
    and PAD_A | PAD_RIGHT
    jr  z, .checkprev
    ld  a, [Panel]
    inc a
    cp  PANEL_COUNT
    jr  c, .storenext
    xor a
.storenext:
    ld  [Panel], a
    ld  a, 1
    ld  [Manual], a
    call LoadPanel

.checkprev:
    ld  a, [PadNew]
    and PAD_B | PAD_LEFT
    jr  z, .checkstart
    ld  a, [Panel]
    dec a
    cp  $FF
    jr  nz, .storeprev
    ld  a, PANEL_COUNT - 1
.storeprev:
    ld  [Panel], a
    ld  a, 1
    ld  [Manual], a
    call LoadPanel

.checkstart:
    ld  a, [PadNew]
    and PAD_START
    jr  z, .auto
    xor a                           ; START resumes automatic cycling
    ld  [Manual], a

.auto:
    ld  a, [Manual]
    or  a
    jr  nz, .motion
    ld  a, [Since]
    inc a
    ld  [Since], a
    cp  PANEL_FRAMES
    jr  c, .motion
    xor a
    ld  [Since], a
    ld  a, [Panel]
    inc a
    cp  PANEL_COUNT
    jr  c, .storeauto
    xor a
.storeauto:
    ld  [Panel], a
    call LoadPanel

.motion:
    call UpdateSprites              ; into the shadow, any time
    call WaitVBlank
    call OAMDMA                     ; and to OAM in one go, in vblank
    call UpdateFlip                 ; palette write, also vblank-only
    jr  .frame

; --- panel upload ---------------------------------------------------------
; Panel stride is 360 bytes, which is not a shift, so the offset is reached by
; adding 360 the required number of times. With five panels that is cheaper
; than a multiply and a great deal clearer.
; Returns HL = base + Panel * DE.
OffsetByPanel:
    ld  a, [Panel]
    or  a
    ret z
    ld  b, a
.loop:
    add hl, de
    dec b
    jr  nz, .loop
    ret

LoadPanel:
    call LCDOff

    ld  hl, MapData
    ld  de, MAP_BYTES
    call OffsetByPanel
    ld  de, _SCRN0
    call CopyMap

    ld  hl, AttrData
    ld  de, MAP_BYTES
    call OffsetByPanel
    call LoadAttributes

    ld  hl, PalData
    ld  de, PAL_BYTES
    call OffsetByPanel
    call LoadPalettes

    call LCDOn
    ret

; --- motion ---------------------------------------------------------------
UpdateSprites:
    ; Frame ticker: one 2-pixel cell per frame, 60 to the lap.
    ld  a, [TickCell]
    add a, a
    ld  e, a
    ld  d, TICK_Y
    ld  c, TILE_TICK
    ld  b, 0
    call SetSprite

    ; 1 px/frame bar, four sprites making 32 pixels.
    ld  a, [ScrollX]
    inc a
    cp  160
    jr  c, .keep
    xor a
.keep:
    ld  [ScrollX], a

    ld  b, 1
.bar:
    ld  a, [ScrollX]
    ld  e, a
    ld  a, b
    dec a
    add a, a
    add a, a
    add a, a                        ; (slot-1) * 8
    add e
    ld  e, a
    ld  d, SCROLL_Y
    ld  c, TILE_SOLID
    push bc
    call SetSprite
    pop bc
    inc b
    ld  a, b
    cp  5
    jr  nz, .bar

    ; Parity flash: solid on odd frames, transparent on even, over the grey
    ; box the layout puts behind it.
    ld  a, [FrameLo]
    and 1
    ld  c, TILE_BLANK
    jr  z, .even
    ld  c, TILE_SOLID
.even:
    ld  b, 5
    ld  d, 0
    ld  e, PARITY_X
    call SetSprite
    ret

; --- checkerboard inversion ----------------------------------------------
; Palette 5 entries 0 and 3 are swapped every frame, which is eight bytes
; through one port. A DMG has no per-tile palettes, so there it would mean
; inverting BGP - which inverts the title and the ticker track along with the
; pattern. It is left static there instead; the parity flash still gives a
; per-frame inversion to look at. See ../README.md.
UpdateFlip:
    ld  a, [IsCGB]
    or  a
    ret z
    ld  a, [Panel]
    cp  3
    ret nz

    ld  a, $80 | (5 * 8)            ; palette 5, auto-increment
    ldh [rBCPS], a
    ld  a, [FrameLo]
    and 1
    ld  hl, CheckPalA
    jr  z, .write
    ld  hl, CheckPalB
.write:
    ld  c, 8
.loop:
    ld  a, [hl+]
    ldh [rBCPD], a
    dec c
    jr  nz, .loop
    ret

SECTION "TestcardData", ROM0

CheckPalA:
    dw  $0000, $294A, $56B5, $7FFF  ; index 0 black, index 3 white
CheckPalB:
    dw  $7FFF, $294A, $56B5, $0000  ; and swapped

TileData:
    INCBIN "tiles.bin"
MapData:
    INCBIN "testcard_map.bin"
AttrData:
    INCBIN "testcard_attr.bin"
PalData:
    INCBIN "testcard_pal.bin"
