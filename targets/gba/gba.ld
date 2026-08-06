/* GBA cartridge image. ROM is memory-mapped at 0x08000000 and executed in
   place; only .data and .bss are copied down into IWRAM at boot. */

OUTPUT_FORMAT("elf32-littlearm")
OUTPUT_ARCH(arm)
ENTRY(_start)

MEMORY
{
    rom   (rx)  : ORIGIN = 0x08000000, LENGTH = 32M
    iwram (rwx) : ORIGIN = 0x03000000, LENGTH = 32K
    ewram (rwx) : ORIGIN = 0x02000000, LENGTH = 256K
}

SECTIONS
{
    .crt0 : { KEEP(*(.crt0)) } > rom

    .text : ALIGN(4) {
        *(.text .text.*)
        *(.glue_7 .glue_7t)
    } > rom

    .rodata : ALIGN(4) {
        *(.rodata .rodata.*)
    } > rom

    /* Runs from IWRAM, ships in ROM. It is kept non-empty by __data_guard in
       crt0.s - see the note there before removing it. */
    .data : ALIGN(4) {
        __data_start = .;
        KEEP(*(.data.guard))
        *(.data .data.*)
        . = ALIGN(4);
        __data_end = .;
    } > iwram AT> rom

    __data_lma = LOADADDR(.data);

    .bss (NOLOAD) : ALIGN(4) {
        __bss_start = .;
        *(.bss .bss.*)
        *(COMMON)
        . = ALIGN(4);
        __bss_end = .;
    } > iwram

    /* IRQs are never enabled by these programs, but the mode has a stack
       pointer whether we use it or not and leaving it at 0 makes any stray
       exception land somewhere undiagnosable. */
    __sp_irq = ORIGIN(iwram) + LENGTH(iwram) - 0x60;
    __sp_usr = ORIGIN(iwram) + LENGTH(iwram) - 0x200;

    /DISCARD/ : { *(.ARM.exidx*) *(.ARM.attributes) *(.comment) }
}
