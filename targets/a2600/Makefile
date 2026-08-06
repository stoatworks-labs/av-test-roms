# Atari 2600 - dasm
#
# 4 KB, 128 bytes of RAM and no framebuffer. Playfield tables come from
# tools/gen.py; the kernels are hand-timed and the cycle budgets are commented
# where they matter, which is everywhere.

TARGET   := a2600
PROGRAMS := testcard inputtest overscan

ROOT     := ../..
BUILD    := $(ROOT)/build/$(TARGET)
GEN      := $(BUILD)/gen
DIST     := $(ROOT)/dist/$(TARGET)

DASM     := dasm

ROMS     := $(PROGRAMS:%=$(DIST)/%.a26)
GENSTAMP := $(GEN)/.stamp

.PHONY: all clean
all: $(ROMS)

$(GENSTAMP): tools/gen.py
	@mkdir -p $(GEN)
	python3 tools/gen.py $(GEN)
	@touch $@

# dasm resolves incbin relative to its own working directory, so it runs in the
# generated-data directory and is given the source by absolute path.
$(DIST)/%.a26: src/%.asm src/vcs.inc $(GENSTAMP)
	@mkdir -p $(DIST)
	cd $(GEN) && $(DASM) $(CURDIR)/src/$*.asm -I$(CURDIR)/src -I. -f3 -o$*.a26
	mv $(GEN)/$*.a26 $@
	@printf '%s: %s bytes\n' $(@F) $$(stat -f%z $@)

clean:
	rm -rf $(BUILD) $(DIST)
