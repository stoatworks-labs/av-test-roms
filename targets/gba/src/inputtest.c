/* inputtest - controller mapping tester. See ../../../docs/DESIGN.md.
 *
 * A frontend with a wrong mapping does not produce a wrong picture, it produces
 * a control that never arrives. So this latches: walk every button once and the
 * one that stayed dark is the one that is not mapped. */

#include "gba.h"

typedef struct { int x, y, w, h; u16 bit; const char *label; } Control;

/* Laid out as the pad itself, so a mapping error reads as a wrong position
   rather than a wrong name in a list. */
static const Control controls[] = {
    { 100,  16, 18,  8, KEY_L,      "L"     },
    { 122,  16, 18,  8, KEY_R,      "R"     },

    {  36,  56, 16, 16, KEY_UP,     "UP"    },
    {  36,  88, 16, 16, KEY_DOWN,   "DN"    },
    {  20,  72, 16, 16, KEY_LEFT,   "LT"    },
    {  52,  72, 16, 16, KEY_RIGHT,  "RT"    },

    { 196,  76, 20, 20, KEY_A,      "A"     },
    { 168,  92, 20, 20, KEY_B,      "B"     },

    {  96, 118, 30, 10, KEY_SELECT, "SEL"   },
    { 132, 118, 30, 10, KEY_START,  "START" },
};
#define NCONTROLS (int)(sizeof(controls) / sizeof(controls[0]))

int main(void)
{
    u16 latched = 0;
    u32 frame = 0;

    REG_DISPCNT = MODE_3 | BG2_ENABLE;
    clear(C_BLACK);
    rect(0, 0, SCREEN_W, SCREEN_H, C_WHITE);
    puts_(3, STATUS_Y, "INPUT TEST", C_WHITE, 1);
    puts_(3, 10, "HOLD A CONTROL - GREEN LATCHES", C_DIM, 1);
    puts_(3, 140, "RAW", C_DIM, 1);
    puts_(120, 140, "UNSEEN", C_DIM, 1);
    puts_(3, 150, "SELECT+START CLEARS LATCH", C_DIM, 1);

    for (;;) {
        u16 keys = key_read();

        if ((keys & (KEY_SELECT | KEY_START)) == (KEY_SELECT | KEY_START))
            latched = 0;
        latched |= keys;

        for (int i = 0; i < NCONTROLS; i++) {
            const Control *c = &controls[i];
            int held = (keys    & c->bit) != 0;
            int seen = (latched & c->bit) != 0;

            /* Held wins over latched, so you can still see what you are
               pressing after everything has gone green. */
            fillrect(c->x, c->y, c->w, c->h,
                     held ? C_WHITE : seen ? C_GREEN : C_BLACK);
            rect(c->x, c->y, c->w, c->h, held ? C_YELLOW : C_DIM);
            puts_(c->x + 2, c->y + (c->h - 5) / 2, c->label,
                  held ? C_BLACK : C_WHITE, 1);
        }

        /* The raw port word. When a control lands on the wrong bit, this says
           which bit it actually moved. */
        puthex(25, 140, keys, 4, C_YELLOW, 1);

        /* Count of controls never yet seen: zero means the mapping is complete. */
        int missing = 0;
        for (int i = 0; i < NCONTROLS; i++)
            if (!(latched & controls[i].bit)) missing++;
        fillrect(155, 140, 20, 6, C_BLACK);
        putdec(155, 140, missing, missing ? C_RED : C_GREEN, 1);

        parity_flash(frame);
        vsync();
        frame++;
    }
}
