; TIA and RIOT registers, and the shape of an NTSC frame.
;
; There is no framebuffer on this machine. The picture is produced by writing
; TIA registers while the beam is moving, so every program here is a "kernel"
; that runs once per scanline and must fit in the 76 CPU cycles a line lasts.
; That constraint is the whole character of the target.

; --- TIA write registers ---
VSYNC   = $00
VBLANK  = $01
WSYNC   = $02       ; writing it stalls the CPU until the next scanline
RSYNC   = $03
NUSIZ0  = $04
NUSIZ1  = $05
COLUP0  = $06
COLUP1  = $07
COLUPF  = $08
COLUBK  = $09
CTRLPF  = $0A
REFP0   = $0B
REFP1   = $0C
PF0     = $0D
PF1     = $0E
PF2     = $0F
RESP0   = $10
RESP1   = $11
RESM0   = $12
RESM1   = $13
RESBL   = $14
GRP0    = $1B
GRP1    = $1C
ENAM0   = $1D
ENAM1   = $1E
ENABL   = $1F
HMP0    = $20
HMP1    = $21
HMM0    = $22
HMM1    = $23
HMBL    = $24
VDELP0  = $25
VDELP1  = $26
HMOVE   = $2A
HMCLR   = $2B
CXCLR   = $2C

; --- TIA read registers ---
INPT4   = $3C       ; player 0 fire, active low
INPT5   = $3D       ; player 1 fire, active low

; --- RIOT ---
SWCHA   = $0280     ; joystick directions, active low
SWCHB   = $0282     ; console switches
INTIM   = $0284
TIM64T  = $0296

; NTSC frame: 3 lines of sync, 37 blank, 192 visible, 30 of overscan.
VISIBLE_LINES = 192
