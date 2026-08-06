#include "gba.h"

const u16 smpte[8] = {
    C_WHITE, C_YELLOW, C_CYAN, C_GREEN, C_MAGENTA, C_RED, C_BLUE, C_BLACK
};

/* 4x5 font, one nibble per row, bit 3 leftmost. Order: 0-9, A-Z, then the
   punctuation in punct[] below. */
static const u8 font[][5] = {
    {0x6,0x9,0x9,0x9,0x6}, {0x2,0x6,0x2,0x2,0x7}, {0x6,0x9,0x2,0x4,0xF},
    {0xE,0x1,0x6,0x1,0xE}, {0x9,0x9,0xF,0x1,0x1}, {0xF,0x8,0xE,0x1,0xE},
    {0x6,0x8,0xE,0x9,0x6}, {0xF,0x1,0x2,0x4,0x4}, {0x6,0x9,0x6,0x9,0x6},
    {0x6,0x9,0x7,0x1,0x6},
    {0x6,0x9,0xF,0x9,0x9}, {0xE,0x9,0xE,0x9,0xE}, {0x7,0x8,0x8,0x8,0x7},
    {0xE,0x9,0x9,0x9,0xE}, {0xF,0x8,0xE,0x8,0xF}, {0xF,0x8,0xE,0x8,0x8},
    {0x7,0x8,0xB,0x9,0x7}, {0x9,0x9,0xF,0x9,0x9}, {0x7,0x2,0x2,0x2,0x7},
    {0x3,0x1,0x1,0x9,0x6}, {0x9,0xA,0xC,0xA,0x9}, {0x8,0x8,0x8,0x8,0xF},
    {0x9,0xF,0xF,0x9,0x9}, {0x9,0xD,0xB,0x9,0x9}, {0x6,0x9,0x9,0x9,0x6},
    {0xE,0x9,0xE,0x8,0x8}, {0x6,0x9,0x9,0xB,0x7}, {0xE,0x9,0xE,0xA,0x9},
    {0x7,0x8,0x6,0x1,0xE}, {0xF,0x6,0x6,0x6,0x6}, {0x9,0x9,0x9,0x9,0x6},
    {0x9,0x9,0x9,0x6,0x6}, {0x9,0x9,0xF,0xF,0x9}, {0x9,0x9,0x6,0x9,0x9},
    {0x9,0x9,0x6,0x6,0x6}, {0xF,0x1,0x6,0x8,0xF},
    {0x0,0x0,0x0,0x0,0x0},                                  /* space */
    {0x0,0x0,0x0,0x0,0x4},                                  /* .     */
    {0x9,0x1,0x2,0x4,0x9},                                  /* %     */
    {0x0,0x0,0xF,0x0,0x0},                                  /* -     */
    {0x0,0x4,0x0,0x4,0x0},                                  /* :     */
    {0x0,0x4,0xE,0x4,0x0},                                  /* +     */
    {0x1,0x2,0x2,0x4,0x8},                                  /* /     */
};
static const char punct[] = " .%-:+/";

static int glyph_of(char ch)
{
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'A' && ch <= 'Z') return 10 + (ch - 'A');
    if (ch >= 'a' && ch <= 'z') return 10 + (ch - 'a');
    for (int i = 0; punct[i]; i++)
        if (punct[i] == ch) return 36 + i;
    return 36;                                              /* space */
}

void vsync(void)
{
    while (REG_VCOUNT >= SCREEN_H) { }                      /* finish this vblank */
    while (REG_VCOUNT <  SCREEN_H) { }                      /* wait for the next  */
}

u16 key_read(void)
{
    return (u16)(~REG_KEYINPUT & KEY_MASK);
}

void px(int x, int y, u16 c)
{
    if ((unsigned)x < SCREEN_W && (unsigned)y < SCREEN_H)
        VRAM[y * SCREEN_W + x] = c;
}

void hline(int x, int y, int w, u16 c)
{
    if ((unsigned)y >= SCREEN_H) return;
    if (x < 0) { w += x; x = 0; }
    if (x + w > SCREEN_W) w = SCREEN_W - x;
    if (w <= 0) return;

    volatile u16 *p = VRAM + y * SCREEN_W + x;

    /* Pair the halfwords into 32-bit stores: on a 16-bit VRAM bus this is the
       difference between one write per pixel and one per two. */
    if ((x & 1) && w > 0) { *p++ = c; w--; }
    volatile u32 *q = (volatile u32 *)p;
    u32 cc = ((u32)c << 16) | c;
    for (int i = w >> 1; i > 0; i--) *q++ = cc;
    if (w & 1) *(volatile u16 *)q = c;
}

void vline(int x, int y, int h, u16 c)
{
    for (int i = 0; i < h; i++) px(x, y + i, c);
}

void fillrect(int x, int y, int w, int h, u16 c)
{
    for (int i = 0; i < h; i++) hline(x, y + i, w, c);
}

void rect(int x, int y, int w, int h, u16 c)
{
    hline(x, y, w, c);
    hline(x, y + h - 1, w, c);
    vline(x, y, h, c);
    vline(x + w - 1, y, h, c);
}

void clear(u16 c)
{
    volatile u32 *q = (volatile u32 *)VRAM;
    u32 cc = ((u32)c << 16) | c;
    for (int i = (SCREEN_W * SCREEN_H) / 2; i > 0; i--) *q++ = cc;
}

void putch(int x, int y, char ch, u16 c, int scale)
{
    const u8 *g = font[glyph_of(ch)];
    for (int row = 0; row < 5; row++) {
        u8 bits = g[row];
        for (int col = 0; col < 4; col++) {
            if (bits & (8 >> col)) {
                if (scale == 1) px(x + col, y + row, c);
                else fillrect(x + col * scale, y + row * scale, scale, scale, c);
            }
        }
    }
}

void puts_(int x, int y, const char *s, u16 c, int scale)
{
    for (; *s; s++, x += 5 * scale) putch(x, y, *s, c, scale);
}

void puthex(int x, int y, u32 v, int digits, u16 c, int scale)
{
    static const char hexd[] = "0123456789ABCDEF";
    for (int i = digits - 1; i >= 0; i--, x += 5 * scale)
        putch(x, y, hexd[(v >> (i * 4)) & 0xF], c, scale);
}

void putdec(int x, int y, s32 v, u16 c, int scale)
{
    char buf[12];
    int n = 0;
    if (v < 0) { putch(x, y, '-', c, scale); x += 5 * scale; v = -v; }
    do { buf[n++] = (char)('0' + (v % 10)); v /= 10; } while (v);
    while (n--) { putch(x, y, buf[n], c, scale); x += 5 * scale; }
}

/* One cell per emulated frame around a 60-cell track: one lap is one second of
   NTSC. Only the two cells that changed are drawn, so the cost is constant. */

void frame_ticker_track(void)
{
    for (int i = 0; i < TICK_CELLS; i++) {
        fillrect(i * TICK_W, TICK_Y, TICK_W, 5, C_DIM);
        if (i % 10 == 0)
            fillrect(i * TICK_W, TICK_Y + 3, TICK_W, 2, C_RED);
    }
    hline(0, TICK_Y - 2, SCREEN_W, C_DIM);
}

void frame_ticker(u32 frame)
{
    u32 cur  = frame % TICK_CELLS;
    u32 prev = (cur + TICK_CELLS - 1) % TICK_CELLS;

    fillrect((int)prev * TICK_W, TICK_Y, TICK_W, 5, C_DIM);
    if (prev % 10 == 0)
        fillrect((int)prev * TICK_W, TICK_Y + 3, TICK_W, 2, C_RED);
    fillrect((int)cur * TICK_W, TICK_Y, TICK_W, 5, C_WHITE);
}

/* Inverts every single frame. Blending or frame-averaging anywhere in the path
   turns this from a flicker into a flat grey.
   The grey surround is fixed and always drawn: without it the black half of
   the cycle is a black square on a black field, and "inverting every frame" is
   indistinguishable from "not being drawn at all". */
void parity_flash(u32 frame)
{
    rect(SCREEN_W - 12, PARITY_Y, 10, 6, C_GREY);
    fillrect(SCREEN_W - 11, PARITY_Y + 1, 8, 4, (frame & 1) ? C_WHITE : C_BLACK);
}
