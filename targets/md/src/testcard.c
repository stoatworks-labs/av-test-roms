/* testcard - pattern generator with motion, Mega Drive.
 *
 * Panels are whole plane maps written during vblank; every moving element is a
 * sprite. The checkerboard inverts by swapping two CRAM words, the same trick
 * the NES and Game Boy Color builds use and for the same reason: it is two
 * writes rather than a screenful. */

#include "md.h"

#define PANEL_COUNT  5
#define PANEL_FRAMES 128
#define MAP_WORDS    (VIEW_W * VIEW_H)

#define T_SOLID_WHITE 1
#define T_TICKCELL    24
#define PAL_TRACK     2

#define TICK_Y   208
#define SCROLL_Y 192
#define PARITY_X 304

extern const u16 md_tiles[];
extern const u16 md_palettes[];
extern const u16 testcard_map[];

/* CRAM colours, 9-bit BGR. Palette 1 entries 1 and 2 are the checkerboard's. */
#define CRAM_WHITE 0x0EEE
#define CRAM_BLACK 0x0000

int main(void)
{
    int panel = 0, since = 0, manual = 0, redraw = 1;
    u16 scroll = 0;

    vdp_init();
    vdp_load_tiles(md_tiles, 0xC0 * 16);        /* 0xC0 tiles, 16 words each */
    vdp_load_palettes(md_palettes);

    for (;;) {
        u16 hit = (pad_read(), pad_new());

        if (hit & (PAD_A | PAD_C | PAD_RIGHT)) {
            panel = (panel + 1) % PANEL_COUNT;
            redraw = 1;
            manual = 1;
        }
        if (hit & (PAD_B | PAD_LEFT)) {
            panel = (panel + PANEL_COUNT - 1) % PANEL_COUNT;
            redraw = 1;
            manual = 1;
        }
        if (hit & PAD_START)
            manual = 0;

        if (!manual && ++since >= PANEL_FRAMES) {
            since = 0;
            panel = (panel + 1) % PANEL_COUNT;
            redraw = 1;
        }

        if (redraw) {
            redraw = 0;
            vdp_load_map(&testcard_map[panel * MAP_WORDS]);
        }

        /* Frame ticker: one 4-pixel cell per frame, 60 to the lap. Four
           pixels divides the 8-pixel tile exactly here, so the decade marks
           in the background land on tile boundaries. */
        sprite_set(0, (s16)(tick_cell() * 4), TICK_Y,
                   (u16)((PAL_TRACK << 13) | T_TICKCELL), 1, 1);

        /* 1 px/frame bar: four one-cell sprites rather than one four-cell
           sprite, because a multi-cell sprite takes consecutive tiles and the
           tiles after solid white are the other solid colours. */
        scroll = (u16)((scroll + 1) % SCREEN_W);
        for (u8 i = 0; i < 4; i++)
            sprite_set((u8)(1 + i), (s16)((scroll + i * 8) % SCREEN_W), SCROLL_Y,
                       T_SOLID_WHITE, 1, 1);

        sprite_set(5, PARITY_X, 0,
                   (frame_count() & 1) ? T_SOLID_WHITE : 0, 1, 1);

        for (u8 i = 6; i < SPRITE_COUNT; i++)
            sprite_hide(i);

        vsync();
        sprite_flush();

        if (panel == 3) {
            /* Two CRAM words a frame. */
            u16 a = (frame_count() & 1) ? CRAM_BLACK : CRAM_WHITE;
            vdp_cram_word(1, 1, a);
            vdp_cram_word(1, 2, (u16)(a == CRAM_WHITE ? CRAM_BLACK : CRAM_WHITE));
        }
    }
}
