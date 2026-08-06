/* Mega Drive hardware and the helpers the three programs share. */

#ifndef AVTS_MD_H
#define AVTS_MD_H

typedef unsigned char  u8;
typedef unsigned short u16;
typedef unsigned int   u32;
typedef signed short   s16;

#define SCREEN_W 320
#define SCREEN_H 224
#define VIEW_W   40
#define VIEW_H   28
#define PLANE_W  64                 /* the plane is wider than the screen */

#define VDP_DATA   (*(volatile u16 *)0xC00000)
#define VDP_CTRL   (*(volatile u16 *)0xC00004)
#define VDP_CTRL_L (*(volatile u32 *)0xC00004)

#define VRAM_PLANE_A 0xC000
#define VRAM_PLANE_B 0xE000
#define VRAM_SPRITES 0xF000
#define VRAM_HSCROLL 0xFC00

/* Enough for inputtest, which lights twelve controls and prints five digits.
   The VDP allows 80 in H40 mode. */
#define SPRITE_COUNT 40

extern volatile u32 vblank_count;

static inline void vdp_reg(u8 reg, u8 value)
{
    VDP_CTRL = (u16)(0x8000 | (reg << 8) | value);
}

/* The address is split across the 32-bit control word in two pieces, which is
   the one piece of Mega Drive plumbing worth getting from a macro rather than
   remembering. */
static inline void vdp_vram(u16 addr)
{
    VDP_CTRL_L = 0x40000000u | ((u32)(addr & 0x3FFF) << 16) | ((addr >> 14) & 3);
}

static inline void vdp_cram(u16 addr)
{
    VDP_CTRL_L = 0xC0000000u | ((u32)(addr & 0x3FFF) << 16) | ((addr >> 14) & 3);
}

/* Controller bits, active high once pad_read has inverted them. */
#define PAD_UP    0x0001
#define PAD_DOWN  0x0002
#define PAD_LEFT  0x0004
#define PAD_RIGHT 0x0008
#define PAD_A     0x0010
#define PAD_B     0x0020
#define PAD_C     0x0040
#define PAD_START 0x0080
#define PAD_X     0x0100
#define PAD_Y     0x0200
#define PAD_Z     0x0400
#define PAD_MODE  0x0800
#define PAD_BASE_MASK 0x00FF        /* the eight a 3-button pad can report */

void vdp_init(void);
void vdp_load_tiles(const u16 *src, u16 words);
void vdp_load_palettes(const u16 *src);
void vdp_load_map(const u16 *src);   /* 40x28 into plane A, stride 64 */
void vdp_cram_word(u8 pal, u8 index, u16 colour);

u16  pad_read(void);
u16  pad_new(void);
void vsync(void);
u32  frame_count(void);
u16  tick_cell(void);

/* slot 0..SPRITE_COUNT-1. Screen coordinates; the +128 offsets are applied
   here. tile carries palette and priority bits like a plane entry. */
void sprite_set(u8 slot, s16 x, s16 y, u16 tile, u8 wcells, u8 hcells);
void sprite_hide(u8 slot);
void sprite_flush(void);

#endif
