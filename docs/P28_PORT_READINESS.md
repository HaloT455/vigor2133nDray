# P28 port readiness — 2026-10-22

**Research baseline**: `ALICE_V2133n_P25_CHAT_FIX_P12_BASE_NOT_FLASH_VERIFIED.all`, SHA256 `009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2`. All outputs below are **static reverse-engineering artifacts** and NOT ready-to-flash firmware.

## New P28 checks against actual private P27 exports

1. **DLM header structure:** `usr32alice.dlm`, `usr32appe.dlm`, `usr32geoip_data.dlm` and `usr32ssh.dlm` all store a big-endian total-length equal to actual file length, a version word of `1` at offset `4`, and sentinel `0x12345678` at offset `0x30`. Remaining opaque payload/loader ABI is **unsolved**. DLM files are not ELF and do not provide original C source.
2. **MIPS:** First 1 MiB of decompressed RTOS contains **7,033 potential direct-call (JAL) opcode words** whose low-28-bit targets are within the image. These are candidates, not a validated cross-reference graph; a real virtual load address and code/data classification are missing.
3. **Hardware clues:** Lantiq GRX-family and I/O code, MT7603 and Atheros Wi-Fi strings, MIPS relocation handlers, and NAND/SPI routines all occur in the RTOS bytes. This **does not** prove the exact hardware actually populated on a specific Vigor2133n variant, because related-model drivers may be compiled in.
4. **UI dependencies:** Four selected entry pages (`alice.htm`, `WEBLOGIN.HTM`, `LOGIN.HTM`, `index.htm`) have **4, 2, 2, 2** static file references; all 10 resolve to the private decoded PFS tree. Dynamic CGI endpoints remain part of the unavailable RTOS HTTP runtime; the user interface cannot be independently assumed functional.

## Reproduce locally

Install requirements from the repository, then run:

```bash
python3 tools/p28_port_inventory.py \
  --rtos private-extracts/rtos/rtos_mips_candidate.bin \
  --dlm-dir private-extracts/dlm \
  --pfs-dir private-extracts/pfs/V2000 \
  --expected-sha256 6018940fd0b28e905504db13e01d4b979bd0c03eda5241be8cf005912f8de612 \
  --out experiments/p28_inventory.json
python3 -m unittest discover -s tests -v
```

**Do not commit extracted firmware binaries, signed DLMs, router configuration, credentials, Wi-Fi calibration data, or other proprietary assets.**

## Completion gates — never label unverified items green

| Gate | Required objective evidence | State |
|---|---|---|
| P25–P27 baseline + extraction | SHA256, valid RTOS/DLM/PFS bounds, correct extracted bytes | DONE |
| BIN/WEB/MD5 basic integrity | all three checked on baseline | DONE |
| P28 partial DLM headers | version/size/sentinel consistency across all four modules | DONE |
| P28 login UI resource references | 4 inspected pages, referenced static files present | DONE |
| Complete RTOS/DLM source recovery | proven functional equivalence or original licensed source | NOT DONE |
| Drivers/board port | verified SoC, flash, PHY/switch, Wi-Fi, RAM, DT/bootloader | NOT DONE |
| Reproducible firmware builder | matches loader specification, passes checks and rollback | NOT DONE |
| Real device functional test | UART boot log, LAN/WAN/mesh/login and recovery verified | NOT DONE |

## Port work depends on target hardware

Confirm the actual destination model/SoC (porting from **Vigor2133n to what device?**) and provide redacted boot UART transcript and board/chip revision before attempting platform-dependent drivers, bootloader or image generation. The official family includes wireless and non-wireless models with different peripherals; avoid choosing drivers solely from generic firmware text.

Useful references: [Vigor2133 product specs](https://www.draytek.com/products/vigor2133/), [OpenWrt supported devices](https://openwrt.org/supported_devices), and [Draytek Arsenal format research](https://github.com/infobyte/draytek-arsenal).

The **GitHub Actions green check reflects tests of research tools, not 100% ROM port completion.**
