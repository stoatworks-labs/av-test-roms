/* Mega Drive cartridge. ROM is mapped at 0 and executed in place; RAM is the
   64 KB at $FF0000. */

OUTPUT_FORMAT("elf32-m68k")
OUTPUT_ARCH(m68k)
ENTRY(_start)

MEMORY
{
    rom (rx)  : ORIGIN = 0x00000000, LENGTH = 4M
    ram (rwx) : ORIGIN = 0x00FF0000, LENGTH = 64K
}

SECTIONS
{
    .crt0 : { KEEP(*(.crt0)) } > rom

    .text : ALIGN(2) {
        *(.text .text.*)
    } > rom

    .rodata : ALIGN(2) {
        *(.rodata .rodata.*)
    } > rom

    /* Kept non-empty by __data_guard in crt0.s for the same reason the GBA
       build needs one: an empty output section gets no load address anyone
       would want. */
    .data : ALIGN(2) {
        __data_start = .;
        KEEP(*(.data.guard))
        *(.data .data.*)
        . = ALIGN(2);
        __data_end = .;
    } > ram AT> rom

    __data_lma = LOADADDR(.data);
    __rom_end = __data_lma + SIZEOF(.data);

    .bss (NOLOAD) : ALIGN(2) {
        __bss_start = .;
        *(.bss .bss.*)
        *(COMMON)
        . = ALIGN(2);
        __bss_end = .;
    } > ram

    /DISCARD/ : { *(.comment) *(.note*) }
}
