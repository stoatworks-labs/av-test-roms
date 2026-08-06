/* Minimal GBA hardware definitions and the drawing primitives the three
   programs share. Mode 3: a 240x160 16bpp framebuffer, no palette, no page
   flip. Slower than mode 4 but every pattern here is row-coherent, so the
   cost lands on whole rows written 32 bits at a time rather than per pixel. */

#ifndef AVTS_GBA_H
#define AVTS_GBA_H

typedef unsigned char  u8;
typedef unsigned short u16;
typedef unsigned int   u32;
typedef signed short   s16;
typedef signed int     s32;

#define SCREEN_W 240
#define SCREEN_H 160

#define REG_DISPCNT  (*(volatile u16 *)0x04000000)
#define REG_DISPSTAT (*(volatile u16 *)0x04000004)
#define REG_VCOUNT   (*(volatile u16 *)0x04000006)
#define REG_KEYINPUT (*(volatile u16 *)0x04000130)

#define MODE_3       0x0003
#define BG2_ENABLE   0x0400

#define VRAM ((volatile u16 *)0x06000000)

/* DMA3 is the general-purpose channel. Used for the one pattern that has to be
   rewritten in full every frame; see panel_check() in testcard.c. */
#define REG_DMA3SAD (*(volatile u32 *)0x040000D4)
#define REG_DMA3DAD (*(volatile u32 *)0x040000D8)
#define REG_DMA3CNT (*(volatile u32 *)0x040000DC)
#define DMA_ENABLE  0x80000000
#define DMA_32BIT   0x04000000

static inline void dma3_copy(volatile void *dst, const void *src, u32 words)
{
    REG_DMA3SAD = (u32)src;
    REG_DMA3DAD = (u32)dst;
    REG_DMA3CNT = DMA_ENABLE | DMA_32BIT | words;
}

/* KEYINPUT is active low; key_read() inverts so a set bit means held. */
#define KEY_A      0x0001
#define KEY_B      0x0002
#define KEY_SELECT 0x0004
#define KEY_START  0x0008
#define KEY_RIGHT  0x0010
#define KEY_LEFT   0x0020
#define KEY_UP     0x0040
#define KEY_DOWN   0x0080
#define KEY_R      0x0100
#define KEY_L      0x0200
#define KEY_MASK   0x03ff

#define RGB(r, g, b) ((u16)((r) | ((g) << 5) | ((b) << 10)))

/* SMPTE order, full amplitude. See docs/DESIGN.md. */
#define C_WHITE   RGB(31, 31, 31)
#define C_YELLOW  RGB(31, 31,  0)
#define C_CYAN    RGB( 0, 31, 31)
#define C_GREEN   RGB( 0, 31,  0)
#define C_MAGENTA RGB(31,  0, 31)
#define C_RED     RGB(31,  0,  0)
#define C_BLUE    RGB( 0,  0, 31)
#define C_BLACK   RGB( 0,  0,  0)
#define C_GREY    RGB(16, 16, 16)
#define C_DIM     RGB( 8,  8,  8)

extern const u16 smpte[8];

/* Frame timing. vsync() spins on VCOUNT rather than waiting on an interrupt so
   that nothing here depends on the IRQ vector, which lives in BIOS. */
void vsync(void);
u16  key_read(void);

/* Drawing. All coordinates are clipped. */
void clear(u16 c);
void px(int x, int y, u16 c);
void hline(int x, int y, int w, u16 c);
void vline(int x, int y, int h, u16 c);
void fillrect(int x, int y, int w, int h, u16 c);
void rect(int x, int y, int w, int h, u16 c);

/* 4x5 glyphs on a 5x6 cell, scale 1 or 2. Uppercase, digits, " .%-:+/". */
void putch(int x, int y, char ch, u16 c, int scale);
void puts_(int x, int y, const char *s, u16 c, int scale);
void puthex(int x, int y, u32 v, int digits, u16 c, int scale);
void putdec(int x, int y, s32 v, u16 c, int scale);

/* The motion elements every testcard panel carries (docs/DESIGN.md).
   TICK_CELLS cells of TICK_W pixels: one lap is one second of NTSC. */
#define TICK_CELLS 60
#define TICK_W     4
#define TICK_Y     (SCREEN_H - 6)

/* Top status strip: row 0 is the border, rows 1..6 carry the panel name and
   the parity flash, so neither ever lands on top of pattern content. */
#define STATUS_Y   1
#define PARITY_Y   1

void frame_ticker(u32 frame);
void frame_ticker_track(void);   /* redraw the empty track after a clear */
void parity_flash(u32 frame);

#endif
