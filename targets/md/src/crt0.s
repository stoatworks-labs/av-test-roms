| Mega Drive vector table, cartridge header and entry.
|
| The 68000 fetches its initial stack pointer from $000 and its reset vector
| from $004, so those two longs are the first thing in the ROM and the header
| follows at $100.

    .section .crt0, "ax"
    .globl  _start

| --- vector table, $000..$0FF -------------------------------------------
| 64 vectors of four bytes. .org markers rather than counted .long lists,
| because miscounting here moves the whole header and the only symptom is an
| assembler warning about odd alignment several screens away.
    .long   0x00FFFE00              | 0: initial stack pointer, top of RAM
    .long   _start                  | 1: reset
    .rept   22                      | 2..23: bus error through to reserved
    .long   _except
    .endr
    .long   _except                 | 24: spurious
    .long   _except                 | 25: level 1
    .long   _except                 | 26: level 2, external
    .long   _except                 | 27: level 3
    .long   _hblank                 | 28: level 4, horizontal blank
    .long   _except                 | 29: level 5
    .long   _vblank                 | 30: level 6, vertical blank
    .long   _except                 | 31: level 7
    .rept   32                      | 32..63: traps and the rest
    .long   _except
    .endr

| --- cartridge header, $100..$1FF ---------------------------------------
| Nothing here is anybody else's artwork, unlike the Nintendo platforms in
| this suite: the Mega Drive header is plain text, so it is simply correct.
    .org    0x100
    .ascii  "SEGA MEGA DRIVE "      | console name, 16
    .org    0x110
    .ascii  "STOATWORKS  2026"      | copyright, 16
    .org    0x120
    .ascii  "AV TEST ROM"           | domestic name, 48
    .org    0x150
    .ascii  "AV TEST ROM"           | overseas name, 48
    .org    0x180
    .ascii  "GM AVTS0001-00"        | serial, 14
    .org    0x18E
    .word   0x0000                  | checksum, patched by tools/mdfix.py
    .org    0x190
    .ascii  "J"                     | I/O support: 3-button pad
    .org    0x1A0
    .long   0x00000000              | ROM start
    .long   __rom_end - 1           | ROM end
    .long   0x00FF0000              | RAM start
    .long   0x00FFFFFF              | RAM end
    .org    0x1B0
    .ascii  "            "          | SRAM info: none
    .org    0x1F0
    .ascii  "JUE"                   | region: all three
    .org    0x200

| --- entry ---------------------------------------------------------------
_start:
    move    #0x2700, %sr            | interrupts off while we set up
    lea     0x00FFFE00, %sp

    lea     __bss_start, %a0        | zero .bss
    lea     __bss_end, %a1
1:  cmpa.l  %a1, %a0
    bge     2f
    clr.l   (%a0)+
    bra     1b
2:

    lea     __data_lma, %a0         | copy .data into RAM
    lea     __data_start, %a1
    lea     __data_end, %a2
3:  cmpa.l  %a2, %a1
    bge     4f
    move.l  (%a0)+, (%a1)+
    bra     3b
4:

    | Interrupt mask down to 0 so the level 6 vertical blank can arrive. Left
    | at 7 from the setup above, vblank_count never increments and vsync()
    | spins forever - the screen shows the first frame's background perfectly
    | and not one sprite, which looks like a sprite bug and is not.
    move    #0x2000, %sr

    jsr     main
5:  bra     5b                      | main never returns

| Vertical blank just bumps a counter the programs poll. Doing the work here
| instead would mean every VDP write raced whatever main() was in the middle
| of, and this suite has no need of the extra frame.
_vblank:
    addq.l  #1, vblank_count
    rte

_hblank:
    rte

| Any unexpected exception parks the machine rather than running off into
| whatever the bus happens to return. A frozen picture is a diagnosis; a
| wandering one is not.
_except:
    stop    #0x2700
    bra     _except

    .section .bss
    .align  2
    .globl  vblank_count
vblank_count:
    .space  4

| Keeps .data non-empty. Same reason as the GBA build: an empty output section
| gets no sensible load address, and the failure is silent.
    .section .data.guard, "aw"
    .align  2
    .globl  __data_guard
__data_guard:
    .long   0xA55A0FF0
