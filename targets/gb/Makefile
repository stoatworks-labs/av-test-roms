# Game Boy / Game Boy Color - RGBDS
#
# One ROM per program, CGB-enhanced and DMG-compatible: it runs on both and
# uses colour only where a Game Boy Color is present. See src/runtime.inc.

TARGET   := gb
PROGRAMS := testcard inputtest overscan

ROOT     := ../..
BUILD    := $(ROOT)/build/$(TARGET)
GEN      := $(BUILD)/gen
DIST     := $(ROOT)/dist/$(TARGET)

RGBASM   := rgbasm
RGBLINK  := rgblink
RGBFIX   := rgbfix

# -c sets the CGB flag to $80 (enhanced, still runs on DMG).
# -f hg fixes the header and global checksums but NOT the logo: that bitmap is
# Nintendo's artwork and is deliberately left zero. See README.md.
FIXFLAGS := -c -t "AVTESTROM" -m 0x00 -p 0xFF -f hg

ROMS     := $(PROGRAMS:%=$(DIST)/%.gb)
GENSTAMP := $(GEN)/.stamp

.PHONY: all clean
all: $(ROMS)

$(GENSTAMP): tools/gen.py $(ROOT)/tools/font.py
	@mkdir -p $(GEN)
	python3 tools/gen.py $(GEN)
	@touch $@

$(BUILD)/%.o: src/%.asm src/runtime.inc $(GENSTAMP)
	@mkdir -p $(BUILD)
	$(RGBASM) -I src -I $(GEN) -o $@ $<

$(DIST)/%.gb: $(BUILD)/%.o
	@mkdir -p $(DIST)
	$(RGBLINK) -o $@ -m $(BUILD)/$*.map -n $(BUILD)/$*.sym $<
	$(RGBFIX) $(FIXFLAGS) $@
	@printf '%s: %s bytes\n' $(@F) $$(stat -f%z $@)

clean:
	rm -rf $(BUILD) $(DIST)
