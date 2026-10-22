#!/bin/sh
# P32: builds an unbootable, unflashable MIPS linker diagnostic.
set -eu
cd "$(dirname "$0")"
: "${CLANG:=clang}"
: "${LD_LLD:=ld.lld}"
FLAGS='--target=mips-unknown-elf -march=mips32r2 -mabi=32 -EB -mno-abicalls -fno-pic -ffreestanding -fno-builtin -nostdlib -O2 -Wall -Wextra -Werror'
$CLANG $FLAGS -c alice_hal.c -o alice_hal_diag.o
$CLANG $FLAGS -c diagnostic_entry.c -o diagnostic_entry.o
# Synthetic link address! Not the router load address.
$LD_LLD -m elf32btsmip -e alice_diagnostic_entry -Ttext=0x10000 \
  alice_hal_diag.o diagnostic_entry.o -o alice_diagnostic.analysis.elf
python3 ../tools/p32_port_check.py --elf alice_diagnostic.analysis.elf \
  --out ../analysis/p32_diagnostic_link_report.json
