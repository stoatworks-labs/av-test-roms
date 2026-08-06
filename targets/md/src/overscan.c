/* overscan - safe-area and edge display, Mega Drive.
 *
 * The only target in the suite whose overscan rectangles are colour-keyed.
 * That is not generosity, it is the plane map: one 16-bit entry per cell
 * carries the palette, so two rectangles meeting in the same 16x16 area is a
 * non-event here where on the NES it is impossible. */

#include "md.h"

extern const u16 md_tiles[];
extern const u16 md_palettes[];
extern const u16 overscan_map[];

#define T_SOLID_WHITE 1
#define PARITY_X 304

int main(void)
{
    vdp_init();
    vdp_load_tiles(md_tiles, 0xC0 * 16);
    vdp_load_palettes(md_palettes);
    vdp_load_map(overscan_map);

    for (;;) {
        sprite_set(0, PARITY_X, 0,
                   (frame_count() & 1) ? T_SOLID_WHITE : 0, 1, 1);
        for (u8 i = 1; i < SPRITE_COUNT; i++)
            sprite_hide(i);

        vsync();
        sprite_flush();
    }
}
