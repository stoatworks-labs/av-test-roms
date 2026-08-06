#include "md.h"

static u16 sprite_table[SPRITE_COUNT * 4];
static u16 pad_state, pad_prev, pad_edge;
static u32 last_vblank;
static u16 tick;

void vdp_init(void)
{
    volatile u16 *ctrl = (volatile u16 *)0xC00004;
    (void)*ctrl;                    /* clears any half-written control word */

    vdp_reg(0x00, 0x04);            /* mode 5, no H interrupt              */
    vdp_reg(0x01, 0x74);            /* display on, V interrupt, DMA, 224   */
    vdp_reg(0x02, VRAM_PLANE_A >> 10);
    vdp_reg(0x03, 0x00);            /* window, unused                      */
    vdp_reg(0x04, VRAM_PLANE_B >> 13);
    vdp_reg(0x05, VRAM_SPRITES >> 9);
    vdp_reg(0x07, 0x00);            /* backdrop: palette 0, colour 0       */
    vdp_reg(0x0A, 0xFF);            /* H interrupt counter, unused         */
    vdp_reg(0x0B, 0x00);            /* full-screen scroll                  */
    vdp_reg(0x0C, 0x81);            /* H40: 320 pixels across              */
    vdp_reg(0x0D, VRAM_HSCROLL >> 10);
    vdp_reg(0x0F, 0x02);            /* auto-increment one word             */
    vdp_reg(0x10, 0x01);            /* plane size 64x32                    */
    vdp_reg(0x11, 0x00);
    vdp_reg(0x12, 0x00);

    /* Scroll is fixed at zero; nothing here scrolls the plane, the moving
       elements are all sprites. */
    vdp_vram(VRAM_HSCROLL);
    VDP_DATA = 0;
    VDP_DATA = 0;

    for (u8 i = 0; i < SPRITE_COUNT; i++)
        sprite_hide(i);
    sprite_flush();
}

void vdp_load_tiles(const u16 *src, u16 words)
{
    vdp_vram(0);
    for (u16 i = 0; i < words; i++)
        VDP_DATA = src[i];
}

void vdp_load_palettes(const u16 *src)
{
    vdp_cram(0);
    for (u16 i = 0; i < 64; i++)    /* 4 palettes of 16 */
        VDP_DATA = src[i];
}

void vdp_cram_word(u8 pal, u8 index, u16 colour)
{
    vdp_cram((u16)((pal * 16 + index) * 2));
    VDP_DATA = colour;
}

/* The plane is 64 cells wide and the screen is 40, so each row is written
   then skipped forward. Writing the whole 64x32 plane instead would be
   simpler and four times the VRAM traffic. */
void vdp_load_map(const u16 *src)
{
    for (u16 y = 0; y < VIEW_H; y++) {
        vdp_vram((u16)(VRAM_PLANE_A + (y * PLANE_W) * 2));
        for (u16 x = 0; x < VIEW_W; x++)
            VDP_DATA = src[y * VIEW_W + x];
    }
}

/* --- input --------------------------------------------------------------
 * The six-button pad multiplexes onto the same six lines by counting TH
 * transitions: the third TH=0 read returns zero in its low nibble as a
 * signature, and the TH=1 read after it carries Mode, X, Y and Z. A
 * three-button pad simply never produces the signature, and those four bits
 * stay clear - which is why inputtest labels them as a separate group rather
 * than counting them as missing.
 */
u16 pad_read(void)
{
    volatile u8 *port = (volatile u8 *)0xA10003;
    volatile u8 *ctrl = (volatile u8 *)0xA10009;
    u8 r[8];

    *ctrl = 0x40;

    for (u8 i = 0; i < 4; i++) {
        *port = 0x40;
        (void)*port; (void)*port;   /* the pad needs a moment to settle */
        r[i * 2] = *port;
        *port = 0x00;
        (void)*port; (void)*port;
        r[i * 2 + 1] = *port;
    }
    *port = 0x40;

    u16 v = 0;
    u8 th1 = (u8)~r[0];             /* ? ? C B R L D U */
    u8 th0 = (u8)~r[1];             /* ? ? S A ? ? D U */

    if (th1 & 0x01) v |= PAD_UP;
    if (th1 & 0x02) v |= PAD_DOWN;
    if (th1 & 0x04) v |= PAD_LEFT;
    if (th1 & 0x08) v |= PAD_RIGHT;
    if (th1 & 0x10) v |= PAD_B;
    if (th1 & 0x20) v |= PAD_C;
    if (th0 & 0x10) v |= PAD_A;
    if (th0 & 0x20) v |= PAD_START;

    if ((r[5] & 0x0F) == 0) {       /* six-button signature */
        u8 ex = (u8)~r[6];
        if (ex & 0x01) v |= PAD_MODE;
        if (ex & 0x02) v |= PAD_X;
        if (ex & 0x04) v |= PAD_Y;
        if (ex & 0x08) v |= PAD_Z;
    }

    pad_prev = pad_state;
    pad_state = v;
    pad_edge = (u16)(v & ~pad_prev);
    return v;
}

u16 pad_new(void) { return pad_edge; }

/* --- frame -------------------------------------------------------------- */
void vsync(void)
{
    while (vblank_count == last_vblank) { }
    last_vblank = vblank_count;
    tick = (u16)((tick + 1) % 60);  /* one cell per frame, 60 to the lap */
}

u32 frame_count(void) { return last_vblank; }
u16 tick_cell(void)   { return tick; }

/* --- sprites ------------------------------------------------------------
 * Sprite coordinates carry a +128 offset, and the link field chains the list:
 * a sprite whose link is 0 ends it, so every slot links to the next and the
 * last links to zero. Getting that wrong truncates the list silently.
 */
void sprite_set(u8 slot, s16 x, s16 y, u16 tile, u8 wcells, u8 hcells)
{
    u16 *s = &sprite_table[slot * 4];
    s[0] = (u16)(y + 128);
    s[1] = (u16)((((wcells - 1) & 3) << 10) | (((hcells - 1) & 3) << 8) |
                 ((slot + 1 < SPRITE_COUNT) ? (slot + 1) : 0));
    s[2] = tile;
    s[3] = (u16)(x + 128);
}

void sprite_hide(u8 slot)
{
    sprite_set(slot, 0, -128, 0, 1, 1);   /* y = 0 is off the top */
}

void sprite_flush(void)
{
    vdp_vram(VRAM_SPRITES);
    for (u16 i = 0; i < SPRITE_COUNT * 4; i++)
        VDP_DATA = sprite_table[i];
}
