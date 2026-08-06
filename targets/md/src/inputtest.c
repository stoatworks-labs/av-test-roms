/* inputtest - controller mapping tester, Mega Drive.
 *
 * Twelve controls, because a six-button pad has twelve. The last four are
 * shown as their own group: a three-button pad never reports them, and an
 * unlit group there is information rather than a fault, so they are excluded
 * from the unseen count. */

#include "md.h"

extern const u16 md_tiles[];
extern const u16 md_palettes[];
extern const u16 inputtest_map[];

#define T_SOLID_WHITE 1
#define T_SOLID_GREY  13            /* palette 0 index 13, a mid grey */

typedef struct { u16 bit; u8 tx, ty; } Control;

/* Positions match tools/gen.py's labels; the indicator sits to their left. */
static const Control controls[] = {
    { PAD_UP,    6,  6 }, { PAD_DOWN,  6, 12 },
    { PAD_LEFT,  2,  9 }, { PAD_RIGHT, 10, 9 },
    { PAD_A,    24, 11 }, { PAD_B,    28, 10 }, { PAD_C, 32, 9 },
    { PAD_START, 16, 14 },
    { PAD_MODE, 16, 16 }, { PAD_X, 24, 7 }, { PAD_Y, 28, 6 }, { PAD_Z, 32, 5 },
};
#define NCONTROLS (int)(sizeof(controls) / sizeof(controls[0]))

static u8 slot;

static void put_char(char c, s16 x, s16 y)
{
    if (slot < SPRITE_COUNT)
        sprite_set(slot++, x, y, (u16)(unsigned char)c, 1, 1);
}

static void put_hex(u16 v, int digits, s16 x, s16 y)
{
    static const char hexd[] = "0123456789ABCDEF";
    for (int i = digits - 1; i >= 0; i--, x += 8)
        put_char(hexd[(v >> (i * 4)) & 0xF], x, y);
}

int main(void)
{
    u16 latched = 0;

    vdp_init();
    vdp_load_tiles(md_tiles, 0xC0 * 16);
    vdp_load_palettes(md_palettes);
    vdp_load_map(inputtest_map);

    for (;;) {
        u16 pad = pad_read();

        /* START+MODE clears the latch on a six-button pad; START alone held
           with A does the same for a three-button one. */
        if ((pad & (PAD_START | PAD_MODE)) == (PAD_START | PAD_MODE) ||
            (pad & (PAD_START | PAD_A)) == (PAD_START | PAD_A))
            latched = 0;
        latched |= pad;

        slot = 0;
        for (int i = 0; i < NCONTROLS; i++) {
            const Control *c = &controls[i];
            int held = (pad & c->bit) != 0;
            int seen = (latched & c->bit) != 0;
            /* Held wins over latched, so what you are pressing stays visible
               after everything has gone grey. */
            u16 tile = held ? T_SOLID_WHITE : seen ? T_SOLID_GREY : 0;
            sprite_set(slot++, (s16)(c->tx * 8 - 10), (s16)(c->ty * 8), tile, 1, 1);
        }

        /* The raw port word. When a control lands on the wrong bit, the bit
           that moved says what it was mapped to. */
        put_hex(pad, 3, 40, 160);

        int missing = 0;
        for (int i = 0; i < NCONTROLS; i++)
            if ((controls[i].bit & PAD_BASE_MASK) && !(latched & controls[i].bit))
                missing++;
        put_char((char)('0' + missing), 64, 176);

        for (u8 i = slot; i < SPRITE_COUNT; i++)
            sprite_hide(i);

        vsync();
        sprite_flush();
    }
}
