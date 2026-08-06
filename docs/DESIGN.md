# The three programs

Every target builds the same three programs. They are specified here once, in
terms of what they must *show*, because the code cannot be shared — a 2600 races
the beam with 128 bytes of RAM and a Mega Drive has a display list. What is
shared is the design, so that a person who has read one screen can read all
seven.

The suite exists to answer questions about a **video path**, not about emulation
accuracy. There are excellent accuracy suites already (blargg, Mesen, mooneye,
AckAttack); this is not one, and it does not try to be. It answers: *is the
picture I am looking at the picture the core produced?*

---

## Conventions all seven obey

**The outermost pixel row and column are drawn.** Every screen puts a 1-pixel
white border on the true edge of the active raster. If you cannot see all four
edges, something in the path is cropping and every other measurement is suspect.
This is why it is drawn first and why it is white.

**Colours are in SMPTE order**, left to right, at full amplitude for the
platform: white, yellow, cyan, green, magenta, red, blue, black. Where a palette
cannot express one of them (the 2600's chroma/luma pairs, the DMG's four greys)
the target's README says what was substituted and why, rather than silently
picking the nearest thing.

**Nothing needs a BIOS, and nothing needs a save.** Every ROM boots from cold to
its first frame.

**No input is required to see something useful.** Programs cycle on a timer.
Input steps them early, and stops the timer once you have touched it, so you can
hold a frame for a photograph.

---

## 1. `testcard` — pattern generator, with motion

Static test cards are solved. The thing that is not solved, and the reason this
program exists, is that **a dropped or repeated frame is invisible in a static
pattern**. Cartridge runs an emulator's clock against a composition's clock;
those two disagree, and the disagreement shows up as pacing, not as a wrong
picture.

So every panel carries a motion element with *countable* semantics:

| Element | Semantics |
|---|---|
| **Frame ticker** | A marker advancing exactly one cell per emulated frame around a 60-cell track. One lap = one second of NTSC. Photograph two frames; if the marker did not advance exactly one cell, a frame was dropped or repeated. |
| **1px/frame scroll** | A bar moving one pixel per frame. Judder, tearing and interpolation are all visible on it and on nothing else. |
| **Parity flash** | A corner square inverting every frame. If it looks grey rather than flickering, frames are being blended or averaged somewhere. |

The panels themselves, cycling every 128 frames:

1. **Colour bars** over a grey staircase — colour, and luma linearity under it
2. **Crosshatch** — geometry and convergence
3. **Frequency burst** — vertical lines at 1, 2, 4 and 8 pixel pitch. Where the
   1px burst turns grey, the path is scaling or filtering.
4. **Checkerboard**, inverting — the highest frequency the raster has
5. **Luma/chroma edge** — a hard vertical edge over a ramp, the pair a composite
   path smears differently

## 2. `inputtest` — input mapping tester

A diagram of the platform's own controller. Each control lights while held.

Two things make it a mapping tester rather than a button display:

- **Latching.** Anything ever pressed stays marked. You can walk every control
  once and see at a glance which one never arrived — which is the actual failure
  when a frontend's mapping is wrong.
- **The raw word.** The controller's port value is shown in hex. When a mapping
  is wrong, the bit that moved tells you what it was mapped *to*.

Both controller ports are shown where the platform has two.

## 3. `overscan` — safe-area and edge display

Nested rectangles inset 2.5%, 5%, 7.5% and 10% from each edge, each labelled
with its inset in pixels for that platform. Ruler ticks every 8 pixels along all
four edges, with every 32nd tick doubled. A centre crosshair, and corner
markers that are asymmetric — so a flipped or rotated output is obvious rather
than merely plausible.

The point is to be able to say "the path is eating 6 pixels off the left" with a
number, instead of "it looks a bit off".
