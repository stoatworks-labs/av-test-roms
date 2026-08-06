/* overscan - safe-area and edge display. See ../../../docs/DESIGN.md.
 *
 * The output is a number: "the path is eating 6 pixels off the left", not "it
 * looks a bit off". Ticks every 8 pixels, doubled every 32, from all four
 * edges; count the missing ones. */

#include "gba.h"

static const int inset_pct[4] = { 25, 50, 75, 100 };  /* tenths of a percent x10 */
static const u16 inset_col[4] = { C_YELLOW, C_CYAN, C_GREEN, C_RED };
static const char *const inset_name[4] = { "2.5%", "5%", "7.5%", "10%" };

static void ruler(void)
{
    for (int x = 0; x < SCREEN_W; x += 8) {
        int len = (x % 32) ? 3 : 6;
        vline(x, 1, len, C_WHITE);
        vline(x, SCREEN_H - 1 - len, len, C_WHITE);
    }
    for (int y = 0; y < SCREEN_H; y += 8) {
        int len = (y % 32) ? 3 : 6;
        hline(1, y, len, C_WHITE);
        hline(SCREEN_W - 1 - len, y, len, C_WHITE);
    }
}

/* Deliberately different in each corner: a flipped or rotated output is then
   obvious rather than merely plausible. */
static void corners(void)
{
    fillrect(2, 2, 10, 2, C_RED);                       /* TL: bar */
    fillrect(2, 2, 2, 10, C_RED);

    fillrect(SCREEN_W - 12, 2, 10, 10, C_GREEN);        /* TR: solid block */

    for (int i = 0; i < 10; i++)                        /* BL: diagonal */
        px(2 + i, SCREEN_H - 3 - i, C_CYAN);

    for (int i = 0; i < 10; i += 2)                     /* BR: dashes */
        fillrect(SCREEN_W - 12 + i, SCREEN_H - 6, 1, 4, C_MAGENTA);
}

int main(void)
{
    u32 frame = 0;

    REG_DISPCNT = MODE_3 | BG2_ENABLE;
    clear(C_BLACK);

    /* The true edge of the active raster, drawn first and white. If all four
       are not visible, every other measurement on this screen is suspect. */
    rect(0, 0, SCREEN_W, SCREEN_H, C_WHITE);

    ruler();
    corners();

    for (int i = 0; i < 4; i++) {
        int ix = (SCREEN_W * inset_pct[i]) / 1000;
        int iy = (SCREEN_H * inset_pct[i]) / 1000;
        rect(ix, iy, SCREEN_W - 2 * ix, SCREEN_H - 2 * iy, inset_col[i]);
    }

    /* Centre crosshair. */
    hline(SCREEN_W / 2 - 12, SCREEN_H / 2, 25, C_WHITE);
    vline(SCREEN_W / 2, SCREEN_H / 2 - 12, 25, C_WHITE);
    rect(SCREEN_W / 2 - 4, SCREEN_H / 2 - 4, 9, 9, C_WHITE);

    puts_(SCREEN_W / 2 - 17, SCREEN_H / 2 - 26, "240X160", C_WHITE, 1);

    /* The insets are only 4 pixels apart on this platform, which is narrower
       than a line of text: labelling each rectangle in place produced four
       overlapping labels in one corner. A colour-keyed legend in the middle,
       where there is nothing else, stays readable at any scale. */
    for (int i = 0; i < 4; i++) {
        int ix = (SCREEN_W * inset_pct[i]) / 1000;
        int iy = (SCREEN_H * inset_pct[i]) / 1000;
        int ly = SCREEN_H / 2 + 12 + i * 8;

        fillrect(SCREEN_W / 2 - 34, ly, 6, 5, inset_col[i]);
        puts_(SCREEN_W / 2 - 25, ly, inset_name[i], inset_col[i], 1);
        /* The inset in pixels, which is the number you actually report. */
        putdec(SCREEN_W / 2 + 2,  ly, ix, inset_col[i], 1);
        putch (SCREEN_W / 2 + 13, ly, '/', inset_col[i], 1);
        putdec(SCREEN_W / 2 + 19, ly, iy, inset_col[i], 1);
    }
    puts_(SCREEN_W / 2 - 34, SCREEN_H / 2 + 46, "INSET PX X/Y", C_DIM, 1);

    for (;;) {
        parity_flash(frame);
        vsync();
        frame++;
    }
}
