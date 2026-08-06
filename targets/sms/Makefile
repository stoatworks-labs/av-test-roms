# Sega Master System - SDCC's Z80 assembler and linker
#
# sdasz80 assembles, sdldz80 links to Intel HEX, makebin turns that into a
# flat 32 KB cartridge image. No C and no runtime: it is all Z80.

TARGET   := sms
PROGRAMS := testcard inputtest overscan

ROOT     := ../..
BUILD    := $(ROOT)/build/$(TARGET)
GEN      := $(BUILD)/gen
DIST     := $(ROOT)/dist/$(TARGET)

AS       := sdasz80
LD       := sdldz80
MAKEBIN  := makebin

ROMS     := $(PROGRAMS:%=$(DIST)/%.sms)
GENSTAMP := $(GEN)/.stamp

.PHONY: all clean
all: $(ROMS)

$(GENSTAMP): tools/gen.py $(ROOT)/tools/font.py
	@mkdir -p $(GEN)
	python3 tools/gen.py $(GEN)
	@touch $@

# sdasz80 wants -Idir attached, and writes its .rel next to the source however
# it is invoked - the explicit-outfile form in its usage text does not take.
$(BUILD)/%.rel: src/%.s src/sms.inc $(GENSTAMP)
	@mkdir -p $(BUILD)
	$(AS) -o -Isrc -I$(GEN) src/$*.s
	mv src/$*.rel $@

$(DIST)/%.sms: $(BUILD)/%.rel
	@mkdir -p $(DIST)
	$(LD) -n -i $(BUILD)/$*.ihx $<
	$(MAKEBIN) -s 32768 $(BUILD)/$*.ihx $@
	@printf '%s: %s bytes\n' $(@F) $$(stat -f%z $@)

clean:
	rm -rf $(BUILD) $(DIST)
