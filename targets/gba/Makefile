# Game Boy Advance - arm-none-eabi-gcc
#
# C is built Thumb: cartridge ROM is a 16-bit bus, so a 32-bit ARM instruction
# costs two fetches. crt0 stays ARM because the reset vector arrives in ARM
# state, hence -mthumb-interwork.

TARGET   := gba
PROGRAMS := testcard inputtest overscan

ROOT     := ../..
BUILD    := $(ROOT)/build/$(TARGET)
DIST     := $(ROOT)/dist/$(TARGET)

CROSS    := arm-none-eabi-
CC       := $(CROSS)gcc
OBJCOPY  := $(CROSS)objcopy

CFLAGS   := -mthumb -mthumb-interwork -mcpu=arm7tdmi \
            -O2 -Wall -Wextra -Werror \
            -ffreestanding -fno-builtin -fomit-frame-pointer \
            -ffunction-sections -fdata-sections
ASFLAGS  := -mthumb-interwork -mcpu=arm7tdmi -x assembler-with-cpp
LDFLAGS  := -T gba.ld -nostdlib -Wl,--gc-sections -Wl,--no-warn-rwx-segments

# The ARM7TDMI has no divide instruction, so gcc emits __aeabi_idiv/idivmod
# calls that live in libgcc. -nostdlib drops libgcc along with everything else,
# so it has to come back explicitly - it is the only library linked.
LIBS     := -lgcc

COMMON   := $(BUILD)/crt0.o $(BUILD)/draw.o
ROMS     := $(PROGRAMS:%=$(DIST)/%.gba)

.PHONY: all clean
all: $(ROMS)

$(BUILD) $(DIST):
	@mkdir -p $@

$(BUILD)/crt0.o: src/crt0.s | $(BUILD)
	$(CC) $(ASFLAGS) -c $< -o $@

$(BUILD)/%.o: src/%.c src/gba.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.elf: $(BUILD)/%.o $(COMMON) gba.ld
	$(CC) $(CFLAGS) $(LDFLAGS) $(COMMON) $< -o $@ $(LIBS)

$(DIST)/%.gba: $(BUILD)/%.elf | $(DIST)
	$(OBJCOPY) -O binary --gap-fill 0 $< $@
	@python3 $(ROOT)/tools/gbafix.py $@

clean:
	rm -rf $(BUILD) $(DIST)
