| Generated data for the inputtest program. tools/gen.py writes these; see the
| Makefile's gen stamp.

    .section .rodata
    .align  2

    .globl  md_tiles
md_tiles:
    .incbin "tiles.bin"

    .globl  md_palettes
md_palettes:
    .incbin "palettes.bin"

    .globl  inputtest_map
inputtest_map:
    .incbin "inputtest_map.bin"
