# Sega Mega Drive / Genesis - m68k-elf-gcc
#
# Tiles, plane maps and CRAM palettes come from tools/gen.py; the C is plain
# 68000 with no library beyond libgcc.

TARGET   := md
PROGRAMS := testcard inputtest overscan

ROOT     := ../..
BUILD    := $(ROOT)/build/$(TARGET)
GEN      := $(BUILD)/gen
DIST     := $(ROOT)/dist/$(TARGET)

CROSS    := m68k-elf-
CC       := $(CROSS)gcc
OBJCOPY  := $(CROSS)objcopy

CFLAGS   := -m68000 -O2 -Wall -Wextra -Werror -std=gnu11 \
            -ffreestanding -fno-builtin -fomit-frame-pointer \
            -ffunction-sections -fdata-sections -I src -I $(GEN)
ASFLAGS  := -m68000 -x assembler-with-cpp -I $(GEN)
LDFLAGS  := -T md.ld -nostdlib -Wl,--gc-sections
# The 68000 has no divide-by-register for 32 bits, so gcc emits libgcc calls.
LIBS     := -lgcc

COMMON   := $(BUILD)/crt0.o $(BUILD)/md.o
ROMS     := $(PROGRAMS:%=$(DIST)/%.bin)
GENSTAMP := $(GEN)/.stamp

.PHONY: all clean
all: $(ROMS)

$(GENSTAMP): tools/gen.py $(ROOT)/tools/font.py
	@mkdir -p $(GEN)
	python3 tools/gen.py $(GEN)
	@touch $@

$(BUILD)/crt0.o: src/crt0.s $(GENSTAMP)
	@mkdir -p $(BUILD)
	$(CC) $(ASFLAGS) -c $< -o $@

$(BUILD)/%.o: src/%.c src/md.h $(GENSTAMP)
	@mkdir -p $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%_data.o: src/%_data.s $(GENSTAMP)
	@mkdir -p $(BUILD)
	$(CC) $(ASFLAGS) -c $< -o $@

.PRECIOUS: $(BUILD)/%_data.o $(BUILD)/%.o

$(BUILD)/%.elf: $(BUILD)/%.o $(BUILD)/%_data.o $(COMMON) md.ld
	$(CC) $(CFLAGS) $(LDFLAGS) $(COMMON) $< $(BUILD)/$*_data.o -o $@ $(LIBS)

$(DIST)/%.bin: $(BUILD)/%.elf
	@mkdir -p $(DIST)
	$(OBJCOPY) -O binary --gap-fill 0 $< $@
	@python3 tools/mdfix.py $@

clean:
	rm -rf $(BUILD) $(DIST)
