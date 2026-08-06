# Atari 2600

160x192 visible, 4 KB of ROM, **128 bytes of RAM**, and no framebuffer at all.
Built with `dasm`.

| ROM | Bytes |
|---|---|
| `testcard.a26` | 4096 |
| `inputtest.a26` | 4096 |
| `overscan.a26` | 4096 |

Verified against **Stella**.

## There is no picture, only timing

Every other target in this suite has somewhere to put a picture — a
framebuffer, a tilemap, a character set. This one has three playfield
registers and 76 CPU cycles per scanline, and the image exists only because
the program writes registers while the beam is moving. Every design decision
below falls out of that.

**Horizontal blank is 22.67 cycles.** Writes made there land before the beam
reaches pixel 0 and are simply not seen. The colour-bar kernel first wrote
straight after `WSYNC` and lost its first three bars into blank, which looked
exactly like a wrong colour table. It now pads with nine `NOP`s so the first
store lands on the left edge.

**A colour bar cannot be narrower than one store.** `lda #imm` plus
`sta COLUPF` is five cycles, which is fifteen colour clocks. Eight bars cover
120 of the 160 visible pixels and the remaining 40 are black. Twenty-pixel
bars would need 6.67 cycles each, and there is no way to spend two thirds of a
cycle.

**The playfield grid is four pixels.** Twenty bits across the left half,
mirrored into the right by `CTRLPF` bit 0 — which is why every pattern here is
perfectly symmetric without trying. The finest frequency burst is therefore an
8-pixel pair, not the 1-pixel one every other target manages. That is the
honest statement of this machine's horizontal resolution.

## What overscan can and cannot show

Vertically there is no limit: a playfield register can change on any scanline,
so the four horizontal rules land exactly at 5, 10, 14 and 19 of 192.

Horizontally the four insets are 4, 8, 12 and 16 pixels — which is playfield
bits 1, 2, 3 and 4, **adjacent**. Drawing all four vertical arms produces one
solid 16-pixel band rather than four rectangles. So only the two separable ones
are drawn, 2.5% and 10%, with two clear bits between them. Four rectangles at
4-pixel spacing is not a thing this machine can show, and pretending otherwise
would make the measurement worse, not better.

## inputtest has no labels because there is nowhere to put them

No character set, no tile map, 128 bytes of RAM. Each control gets a
horizontal band of sixteen scanlines instead — five for each port, with a
separator between. Held draws the band solid; seen-but-released draws edge
blocks; never-pressed draws a single block whose position is **staggered per
control**, so adjacent bands do not merge into one continuous bar. The reading
is by position, which is the same information the other targets give with
words.

## Two ways to get a black screen

**Forgetting `COLUPF`.** The reset loop zeroes every TIA register, the
playfield colour included, so the playfield starts black on black. Identical in
appearance to a kernel that never runs.

**Drawing nothing for the default state.** `inputtest` originally drew nothing
at all for a control that had never been pressed, so with no input the screen
was entirely black and the layout invisible. Correct, and useless.
