CC ?= cc
CLANG ?= clang
CFLAGS = -std=c11 -Wall -Wextra -Werror -O2
MIPSFLAGS = --target=mips-unknown-elf -march=mips32r2 -mabi=32 -EB -std=c11 -ffreestanding -fno-builtin -nostdlib -Wall -Wextra -Werror -O2
.PHONY: host-check mips-object clean
host-check:
	$(CC) $(CFLAGS) alice_hal.c test_hal.c -o alice_hal_test
	./alice_hal_test
mips-object:
	$(CLANG) $(MIPSFLAGS) -c alice_hal.c -o alice_hal_mips32be.o
clean:
	rm -f alice_hal_test alice_hal_mips32be.o

.PHONY: diagnostic-elf
diagnostic-elf:
	sh build_diagnostic.sh
