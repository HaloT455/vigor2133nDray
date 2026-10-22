# P30 — MIPS RTOS disassembly import (private analysis only)

The extracted P25 RTOS payload is **19,001,596 bytes**, SHA256:

`6018940fd0b28e905504db13e01d4b979bd0c03eda5241be8cf005912f8de612`

`tools/p30_mips_elf_view.py` wraps the raw bytes in an **ELF32, big-endian, ET_REL, EM_MIPS** file with a single synthetic `.text` section. The produced analysis wrapper is **19,001,992 bytes** (SHA256 `48edcf77cf3e8886a457fad01cd85d74c567cba149fe104a95448d2836e2a756`).

The wrapper was recognized by the Unix `file` utility and disassembled successfully with LLVM 17 `llvm-objdump`. Sample decoded mnemonics include `jr`, `jal`, `lui`, `lw`, `sw`, `addiu`, and `bnez`. The observed `jal` target at virtual offset `0x5dec98` is **not a confirmed runtime address** because no load address or relocation base has been established.

## Reproduce using private exports

```bash
python3 tools/p30_mips_elf_view.py private-extracts/rtos/rtos_mips_candidate.bin \
  --expected-sha256 6018940fd0b28e905504db13e01d4b979bd0c03eda5241be8cf005912f8de612 \
  --out private-extracts/rtos/alice_p30.analysis.elf \
  --report experiments/p30_elf.json

llvm-objdump -d --start-address=0 --stop-address=0x100 \
  private-extracts/rtos/alice_p30.analysis.elf
```

You can also import the private ELF as a research artifact into Ghidra. Confirm the CPU ISA, actual load address, memory segment permissions, code/data boundaries and pointer bases before trusting decompiler output. The entire payload is labelled `.text` heuristically, despite containing mixed code and data.

**This is NOT original DrayOS source, a working firmware image, an executable, a proven bootloader entry, or a functional port.** Do not flash the ELF.

## True blockers for a runnable port

1. Exact source and destination router hardware/PCB revision, chip markings, flash/RAM IDs.
2. Boot ROM/bootloader communication, verified image acceptance rules and a safe recovery procedure.
3. Runtime RTOS load address and precise code/data layout.
4. DLM loader ABI, driver initialization dependencies, NVRAM and Wi-Fi calibration storage.
5. Actual cross-compiled target replacement, device boot logs, WAN/LAN/Wi-Fi and management tests.

Official Vigor2133 information: https://www.draytek.com/products/vigor2133/

Green synthetic CI verifies a *research helper*, not these missing physical device tests.
