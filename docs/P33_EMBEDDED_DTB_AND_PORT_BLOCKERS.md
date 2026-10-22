# P33: Embedded device tree recovered from the actual P25 firmware

**Research only — NOT FLASH VERIFIED, and NOT a complete port.**

Image: `ALICE_V2133n_P25_CHAT_FIX_P12_BASE_NOT_FLASH_VERIFIED.all`, SHA256 `009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2`.

Decoded RTOS: 19,001,596 bytes, SHA256 `6018940fd0b28e905504db13e01d4b979bd0c03eda5241be8cf005912f8de612`.

## Major finding

An actual valid **FDT (Flattened Device Tree)**, version 17, occurs at decoded RTOS offset **`0x11F4288`**. Its embedded size is **10,153 bytes**, with SHA256 `d71a5269e34e7d57ff4fa508df189afd44504396c783cae1f543ecf27a20b30a`. A complete node/property-token walk found **92 nodes and 318 properties**.

Root compatible: `lantiq,xway`, `lantiq,grx390`. CPU `mips,mips34Kc`. Candidate hardware nodes include Ethernet/MDIO/PHY, switch, UART, USB, NAND, SPI NOR, PCIe and WLAN.

The embedded FDT describes **7 NAND partitions** covering 64 MiB and **5 SPI NOR partitions** ending at `0x3F0000`. These are **device-tree-declared candidate addresses, not verified on-device flash geometry**.

### NAND partition descriptions from embedded FDT

| Partition | Offset | Size |
|---|---|---|
| uboot | `0x0` | `0x100000` |
| ubootconfigA | `0x100000` | `0x40000` |
| ubootconfigB | `0x140000` | `0x40000` |
| gphyfirmware | `0x180000` | `0x40000` |
| system_sw | `0x1C0000` | `0x3200000` |
| calibration | `0x33C0000` | `0x100000` |
| res | `0x34C0000` | `0xB40000` |

### SPI NOR partition descriptions from embedded FDT

| Partition | Offset | Size |
|---|---|---|
| SPI (RO) U-Boot Image | `0x0` | `0x20000` |
| ENV_MAC | `0x20000` | `0x10000` |
| DPF | `0x30000` | `0x10000` |
| NVRAM | `0x40000` | `0x10000` |
| kernel | `0x50000` | `0x3A0000` |

**Important caveat:** The FDT contains **three placeholder MAC addresses** in the 00:11:22:33:44:5x pattern. It may be a generic vendor platform tree or otherwise not represent the final board configuration. Do **not** use this map to write or erase flash until confirmed against exact PCB/flash identification and on-device dumps. Keep calibration, NVRAM, MAC and bootloader data protected.

## Reproduce on private extracted RTOS

```bash
python3 tools/p33_dtb_audit.py private-extracts/rtos/rtos_mips_candidate.bin \
  --sha256 6018940fd0b28e905504db13e01d4b979bd0c03eda5241be8cf005912f8de612 \
  --out experiments/p33_dtb_public_audit.json \
  --dtb-private private-extracts/rtos/board_candidate.dtb
python3 -m unittest discover -s tests -v
```

`--dtb-private` is optional, writes only to a new local path, and **must never** be used to commit proprietary board images, MACs or calibration information to the public repo.

## Explicit port acceptance status

- Embedded DTB extraction and structural parse: **DONE**.
- Exact router board/flash/RAM and radio hardware identity: **NOT VERIFIED**.
- BSP/driver source integrated with target kernel/runtime: **NOT DONE**.
- Complete DrayOS-equivalent compiled firmware: **NOT DONE**.
- Physical boot, WAN/LAN/Wi-Fi and recovery: **NOT VERIFIED**.

The official DrayTek site identifies Vigor2133n as the 2.4 GHz-only wireless variant: https://www.draytek.com/products/vigor2133/.

The vendor has published GPL-covered code for selected products at https://gplsource.draytek.com/; a Vigor2133 source directory was not visible in the root listing checked on 2026-10-22. The proprietary part of DrayOS is not automatically available from those GPL bundles.

**This analysis provides the first strong candidate device-tree/BSP starting point. It does not prove any flashable firmware.**
