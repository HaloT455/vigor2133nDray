# P32 — MIPS diagnostic build and physical boot blockers

**Status: NOT A FLASHABLE ROM; NOT A COMPLETED DRAYOS PORT.**

On 2026-10-22, the new C HAL and diagnostic entry were compiled and linked to ELF32 MIPS32r2 big-endian **ET_EXEC**, confirmed by LLVM disassembly. The analysis ELF is **67,160 bytes**, SHA256 `f1a2242f48cd86630d22b2b5b4a71deb57fda70777d3b78e519bdb243ff7b20e`. Entry address `0x100d0`; synthetic link address `0x10000` is **not** a verified Vigor2133n physical load address.

The original P25 proprietary image SHA256 is `009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2`. Its BIN/WEB checksums and footer MD5 all validate offline. Local P32 source and HAL tests passed **47/47**, but there is NO kernel, ethernet/switch/Wi-Fi driver, firmware bootloader or independent ported DrayOS.

## Build safely

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
make -C port_scaffold host-check mips-object diagnostic-elf
file port_scaffold/alice_diagnostic.analysis.elf
python3 -m tools.p32_port_check --elf port_scaffold/alice_diagnostic.analysis.elf \
  --baseline /path/to/ALICE_V2133n_P25_CHAT_FIX_P12_BASE_NOT_FLASH_VERIFIED.all \
  --expect-baseline-sha256 009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2 \
  --out experiments/p32_readiness.json
```

The P32 ELF exists **only** to test compiler/linker architecture. No access to physical router was available. Real boot, LAN, WAN, Wi-Fi, management and recovery remain **UNVERIFIED**.

## Device UART capture: optional and READ-ONLY

Only if the exact 3.3V TX/RX/GND pinout has been confirmed by technical documentation or qualified inspection, and you have an appropriate TTL adapter. **NEVER connect 5V or VCC.** Never run flash or bootloader write commands.

```bash
python3 tools/p32_uart_capture.py --port /dev/ttyUSB0 --baud 115200 \
  --seconds 45 --out private-router-boot.log
python3 tools/p31_uart_triage.py private-router-boot.log --out private-uart-triage.json
```

Private UART logs may contain secrets, MACs and serial numbers. Redact them and keep off the public repo.

## Completion requirements

A genuinely complete firmware port requires: source or newly written runtime and real device drivers; validated SoC/PCB identity, memory/flash mapping and Wi-Fi calibration backup; correct bootloader image format; verified recovery; and **physical** repeated boot plus LAN/WAN/Wi-Fi/login validation. The vendor's Vigor2133n uses 2.4 GHz 802.11n; model variants differ: https://www.draytek.com.au/products/broadband-routers/vigor2133-series/.

Green CI proves toolchain tests only. No experimental image is released for flashing.
