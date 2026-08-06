@ GBA cartridge header and entry stub.
@
@ Bytes 0x04..0x9F are the Nintendo logo bitmap, which a real GBA BIOS compares
@ against its own copy before it will run a cartridge. That bitmap is Nintendo's
@ artwork, so it is NOT reproduced here and the field is left zeroed: these ROMs
@ boot in emulators that skip the BIOS check and will NOT boot on real hardware.
@ See ../README.md.

    .section .crt0, "ax"
    .arm
    .global _start
    .align  2

_start:
    b       rom_entry

    .fill   156, 1, 0               @ 0x004 Nintendo logo - deliberately absent
    .byte   'A','V',' ','T','E','S','T',' ','R','O','M',0   @ 0x0A0 title, 12
    .ascii  "AVTS"                  @ 0x0AC game code
    .ascii  "SW"                    @ 0x0B0 maker code
    .byte   0x96                    @ 0x0B2 fixed
    .byte   0x00                    @ 0x0B3 main unit
    .byte   0x00                    @ 0x0B4 device type
    .fill   7, 1, 0                 @ 0x0B5 reserved
    .byte   0x00                    @ 0x0BC software version
    .byte   0x00                    @ 0x0BD complement - patched by gbafix.py
    .byte   0x00, 0x00              @ 0x0BE reserved

rom_entry:
    mov     r0, #0x12               @ IRQ mode, IRQ+FIQ masked
    msr     cpsr_c, r0
    ldr     sp, =__sp_irq
    mov     r0, #0x1f               @ system mode
    msr     cpsr_c, r0
    ldr     sp, =__sp_usr

    ldr     r1, =__data_lma         @ copy .data from ROM into IWRAM
    ldr     r2, =__data_start
    ldr     r3, =__data_end
1:  cmp     r2, r3
    ldrlo   r0, [r1], #4
    strlo   r0, [r2], #4
    blo     1b

    mov     r0, #0                  @ zero .bss
    ldr     r2, =__bss_start
    ldr     r3, =__bss_end
2:  cmp     r2, r3
    strlo   r0, [r2], #4
    blo     2b

    ldr     r0, =main
    bx      r0

3:  b       3b                      @ main never returns

    .pool

@ Keeps .data non-empty, and it must stay.
@
@ These programs hold every table in .rodata and every variable in .bss, so
@ .data comes out empty - and an empty output section gets no LOAD segment,
@ which leaves its load address at the IWRAM virtual address instead of the ROM
@ one. objcopy -O binary then spans 0x03000000 to the end of ROM and writes an
@ 83 MB "cartridge" whose header is four megabytes into the file. Four bytes
@ here cost nothing, keep the load address in ROM, and mean that adding a real
@ initialised variable later just works.
@ Its own section, KEEP'd by gba.ld: nothing references it, so --gc-sections
@ would otherwise collect it and put .data straight back to empty.
    .section .data.guard, "aw", %progbits
    .align  2
    .global __data_guard
__data_guard:
    .word   0xA55A0FF0

    .end
