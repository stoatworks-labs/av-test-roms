# av-test-roms - build every target, or one at a time.
#
#   make            all targets whose toolchain is installed
#   make gba        one target
#   make toolchains what to install, and how
#   make clean

TARGETS_READY := gba nes gb

.PHONY: all clean toolchains $(TARGETS_READY)

all: $(TARGETS_READY)

$(TARGETS_READY):
	$(MAKE) -C targets/$@

clean:
	@for t in $(TARGETS_READY); do $(MAKE) -C targets/$$t clean; done
	rm -rf build dist

toolchains:
	@echo "brew install cc65 rgbds dasm sdcc arm-none-eabi-gcc m68k-elf-gcc"
	@echo
	@printf '%-22s %-28s %s\n' TARGET TOOLCHAIN STATUS
	@printf '%-22s %-28s %s\n' ------ --------- ------
	@printf '%-22s %-28s %s\n' "Game Boy Advance" "arm-none-eabi-gcc" "$$(command -v arm-none-eabi-gcc >/dev/null && echo installed || echo MISSING)"
	@printf '%-22s %-28s %s\n' "NES"              "cc65"              "$$(command -v ca65 >/dev/null && echo installed || echo MISSING)"
	@printf '%-22s %-28s %s\n' "Game Boy / GBC"   "rgbds"             "$$(command -v rgbasm >/dev/null && echo installed || echo MISSING)"
	@printf '%-22s %-28s %s\n' "Mega Drive"       "m68k-elf-gcc"      "$$(command -v m68k-elf-gcc >/dev/null && echo installed || echo MISSING)"
	@printf '%-22s %-28s %s\n' "Master System/GG" "sdcc"              "$$(command -v sdcc >/dev/null && echo installed || echo MISSING)"
	@printf '%-22s %-28s %s\n' "Atari 2600"       "dasm"              "$$(command -v dasm >/dev/null && echo installed || echo MISSING)"
	@printf '%-22s %-28s %s\n' "Commodore 64"     "cc65"              "$$(command -v ca65 >/dev/null && echo installed || echo MISSING)"
