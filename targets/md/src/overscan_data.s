| Generated data for the overscan program. tools/gen.py writes these; see the
| Makefile's gen stamp.

    .section .rodata
    .align  2

    .globl  md_tiles
md_tiles:
    .incbin "tiles.bin"

    .globl  md_palettes
md_palettes:
    .incbin "palettes.bin"

    .globl  overscan_map
overscan_map:
    .incbin "overscan_map.bin"
