/* testcard - pattern generator with motion. See ../../../docs/DESIGN.md.
 *
 * The static part of a panel is drawn once when the panel changes; only the
 * three motion elements are redrawn per frame. That keeps a frame's work to a
 * scroll band, a ticker cell and a flash square, which comfortably fits inside
 * one GBA frame even executing from a 16-bit ROM bus. */

#include "gba.h"

#define PANEL_TOP    8
#define PANEL_BOT    136
#define PANEL_H      (PANEL_BOT - PANEL_TOP)
#define BAND_Y       138
#define BAND_H       12
#define PANEL_FRAMES 128

enum { P_BARS, P_HATCH, P_BURST, P_CHECK, P_EDGE, P_COUNT };

static const char *const panel_name[P_COUNT] = {
    "1 BARS", "2 HATCH", "3 BURST", "4 CHECK", "5 EDGE"
};

/* --- panels ------------------------------------------------------------- */

static void panel_bars(void)
{
    int bar_h = 90, ramp_y = PANEL_TOP + bar_h;

    for (int i = 0; i < 8; i++)
        fillrect(i * 30, PANEL_TOP, 30, bar_h, smpte[i]);

    /* 16-step luma staircase underneath, so colour and luma linearity are
       read from the same photograph. */
    for (int i = 0; i < 16; i++) {
        u16 v = (u16)(i * 2 + (i == 15));
        fillrect(i * 15, ramp_y, 15, PANEL_BOT - ramp_y, RGB(v, v, v));
    }
}

static void panel_hatch(void)
{
    fillrect(0, PANEL_TOP, SCREEN_W, PANEL_H, C_BLACK);
    for (int x = 0; x < SCREEN_W; x += 16) vline(x, PANEL_TOP, PANEL_H, C_WHITE);
    vline(SCREEN_W - 1, PANEL_TOP, PANEL_H, C_WHITE);
    for (int y = PANEL_TOP; y < PANEL_BOT; y += 16) hline(0, y, SCREEN_W, C_WHITE);
    hline(0, PANEL_BOT - 1, SCREEN_W, C_WHITE);

    /* Circle-ish centre marker: convergence errors show as colour fringes on
       the diagonal, which straight lines alone will not reveal. */
    for (int i = 0; i < 24; i++) {
        px(SCREEN_W / 2 - 24 + i, PANEL_TOP + PANEL_H / 2 - 24 + i, C_RED);
        px(SCREEN_W / 2 + 24 - i, PANEL_TOP + PANEL_H / 2 - 24 + i, C_RED);
    }
}

static void panel_burst(void)
{
    static const int pitch[4] = { 2, 4, 8, 16 };
    int h = PANEL_H / 4;

    for (int b = 0; b < 4; b++) {
        int y = PANEL_TOP + b * h;
        fillrect(0, y, SCREEN_W, h, C_BLACK);
        for (int x = 0; x < SCREEN_W; x += pitch[b])
            fillrect(x, y, pitch[b] / 2, h - 1, C_WHITE);
        putdec(2, y + 2, pitch[b] / 2, C_YELLOW, 1);
    }
}

/* The only pattern that must be rewritten in full every frame, and the reason
   this is done with DMA rather than a store loop.
 *
 * Mode 3 has no palette, so "invert the checkerboard" means touching all 128
 * rows: 15360 32-bit stores. Measured against the frame ticker on mGBA, the
 * CPU loop that did that sustained about a third of frame rate - the ticker
 * repeated cells (22,22,23,23,23) instead of advancing one per frame. A test
 * card whose own frame counter is wrong is a broken instrument, so the work
 * had to fit inside a frame rather than merely look right in a screenshot.
 *
 * Two 8-row buffers hold the two phases, built once. Each frame is then 16 DMA
 * transfers, and the ticker advances exactly one cell per frame again. On the
 * tile-based targets in this suite the same inversion is a single palette
 * write, which is why only this one needed the treatment. */
static u16 chk_phase[2][8 * SCREEN_W];
static int chk_ready;

static void chk_build(void)
{
    for (int y = 0; y < 8; y++)
        for (int x = 0; x < SCREEN_W; x++) {
            int on = (x >> 3) & 1;
            chk_phase[0][y * SCREEN_W + x] = on ? C_WHITE : C_BLACK;
            chk_phase[1][y * SCREEN_W + x] = on ? C_BLACK : C_WHITE;
        }
    chk_ready = 1;
}

static void panel_check(u32 frame)
{
    if (!chk_ready) chk_build();

    for (int blk = 0; blk < PANEL_H / 8; blk++)
        dma3_copy(VRAM + (PANEL_TOP + blk * 8) * SCREEN_W,
                  chk_phase[(blk + (int)(frame & 1)) & 1],
                  (8 * SCREEN_W) / 2);
}

static void panel_edge(void)
{
    /* A hard vertical edge over a horizontal ramp: the pair a composite path
       smears differently, and the one that exposes ringing from a sharpener. */
    for (int x = 0; x < SCREEN_W; x++) {
        u16 v = (u16)((x * 31) / (SCREEN_W - 1));
        vline(x, PANEL_TOP, PANEL_H / 2, RGB(v, v, v));
    }
    fillrect(0, PANEL_TOP + PANEL_H / 2, SCREEN_W / 2, PANEL_H / 2, C_BLACK);
    fillrect(SCREEN_W / 2, PANEL_TOP + PANEL_H / 2, SCREEN_W / 2, PANEL_H / 2, C_WHITE);

    /* Colour-difference edges either side of the luma one. */
    fillrect(SCREEN_W / 2 - 40, PANEL_BOT - 20, 40, 18, C_RED);
    fillrect(SCREEN_W / 2,      PANEL_BOT - 20, 40, 18, C_BLUE);
}

/* --- per-frame motion --------------------------------------------------- */

/* One pixel per frame. Judder, tearing and interpolation are all visible here
   and on nothing else in the suite. */
static void scroll_band(u32 frame)
{
    int off = (int)(frame % 32);

    for (int x = 0; x < SCREEN_W; x++) {
        int t = (x + off) % 32;
        u16 c = (t == 0) ? C_WHITE : smpte[((x + off) / 32) & 7];
        vline(x, BAND_Y, BAND_H, c);
    }
    hline(0, BAND_Y - 1, SCREEN_W, C_DIM);
}

int main(void)
{
    u32 frame = 0, since = 0;
    int panel = P_BARS, redraw = 1, manual = 0;
    u16 prev_keys = 0;

    REG_DISPCNT = MODE_3 | BG2_ENABLE;
    clear(C_BLACK);

    for (;;) {
        u16 keys = key_read();
        u16 hit  = (u16)(keys & ~prev_keys);
        prev_keys = keys;

        /* Stepping by hand stops the timer, so a panel can be held still for a
           photograph. START resumes cycling. */
        if (hit & (KEY_A | KEY_RIGHT | KEY_R)) { panel = (panel + 1) % P_COUNT; redraw = 1; manual = 1; }
        if (hit & (KEY_B | KEY_LEFT  | KEY_L)) { panel = (panel + P_COUNT - 1) % P_COUNT; redraw = 1; manual = 1; }
        if (hit & KEY_START) manual = 0;

        if (!manual && ++since >= PANEL_FRAMES) {
            since = 0;
            panel = (panel + 1) % P_COUNT;
            redraw = 1;
        }

        if (redraw) {
            redraw = 0;
            clear(C_BLACK);
            switch (panel) {
            case P_BARS:  panel_bars();  break;
            case P_HATCH: panel_hatch(); break;
            case P_BURST: panel_burst(); break;
            case P_EDGE:  panel_edge();  break;
            default: break;
            }
            rect(0, 0, SCREEN_W, SCREEN_H, C_WHITE);
            puts_(3, STATUS_Y, panel_name[panel], C_WHITE, 1);
            frame_ticker_track();
        }

        if (panel == P_CHECK) panel_check(frame);

        scroll_band(frame);
        frame_ticker(frame);
        parity_flash(frame);

        vsync();
        frame++;
    }
}
