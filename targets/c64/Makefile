# Commodore 64 - cc65 (ca65 / ld65)
#
# The character set has to sit where the VIC can see it, so c64.cfg places it
# at a fixed $2000 rather than letting the linker choose.

TARGET   := c64
PROGRAMS := testcard inputtest overscan

ROOT     := ../..
BUILD    := $(ROOT)/build/$(TARGET)
GEN      := $(BUILD)/gen
DIST     := $(ROOT)/dist/$(TARGET)

CA65     := ca65
LD65     := ld65
CA65FLAGS := -I src --bin-include-dir $(GEN)

ROMS     := $(PROGRAMS:%=$(DIST)/%.prg)
GENSTAMP := $(GEN)/.stamp

.PHONY: all clean
all: $(ROMS)

$(GENSTAMP): tools/gen.py $(ROOT)/tools/font.py
	@mkdir -p $(GEN)
	python3 tools/gen.py $(GEN)
	@touch $@

$(BUILD)/%.o: src/%.s src/c64.inc $(GENSTAMP)
	@mkdir -p $(BUILD)
	$(CA65) $(CA65FLAGS) -o $@ $<

$(DIST)/%.prg: $(BUILD)/%.o c64.cfg
	@mkdir -p $(DIST)
	$(LD65) -C c64.cfg -o $@ $<
	@printf '%s: %s bytes\n' $(@F) $$(stat -f%z $@)

clean:
	rm -rf $(BUILD) $(DIST)
