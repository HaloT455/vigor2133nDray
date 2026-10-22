# ALICE Vigor2133n P26 — static ROM map (2026-10-22)

**Status: research only; NOT FLASH VERIFIED.**

Input: `ALICE_V2133n_P25_CHAT_FIX_P12_BASE_NOT_FLASH_VERIFIED.all`
Size: **15,761,588 bytes**
SHA256: `009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2`
Header: `v2133`, `3.9.7`, `3.9.7_Anphat`, `V385`. Exact SKU/revision unverified.

## Machine code

At `0x100`, a 32-word sample **decodes 32/32** with a limited MIPS big-endian decoder. Examples:

| Offset | Word | MIPS32 BE interpretation |
|---|---|---|
| `0x100` | `40809000` | `mtc0 zero, cp0_18` |
| `0x10c` | `40086000` | `mfc0 t0, cp0_12` |
| `0x110` | `3c011000` | `lui at, 0x1000` |
| `0x138` | `8d090000` | `lw t1, 0(t0)` |

This is not reconstruction of C source, proof of physical SoC, or reliable image memory mapping.

## Archive/resources

**57** `PK 03 04` byte-pattern matches. **8** local entries passed deflate/decompression, CRC32 and data-descriptor size checks. **3** extra candidates decompressed with matching CRC but failed their size descriptor; they were **rejected** and cannot be exported by the strict tool.

Examples of validated resources: `META-INF/DRAYTEK_.SF`, `META-INF/DRAYTEK_.RSA`, `com/elusiva/rdp/RasterOp.class`, `gnu/getopt/GetoptDemo.class`, `VncViewer.class`. These appear to be signed Java applet-related resource **binaries**, not complete DrayOS source. Whole ZIP/JAR central directory is **not** validated.

3 inconsistent candidates: `com/elusiva/rdp/CELLHEADER.class` (`0x951f9a`), `com/elusiva/rdp/RdesktopCanvas.class` (`0x96b343`), `com/elusiva/rdp/rdp5/cliprdr/TextHandler.class` (`0x97753c`).

## UI text and LZO caution

Raw text markers (all unvalidated): `<html`=58, `</html`=26, `<script`=48, `<form`=66, `login`=81, `vlan`=127, `mesh`=55. These are occurrences, **not** a proven inventory of discrete functioning pages.

Legacy `draytools` LZO marker `a5a5a55aa55a` at `0x5266` intersects a MIPS instruction stream at a non-word-aligned offset. Do **not** interpret it as an actual compressed region boundary without further evidence.

## Implementation

- `tools/rom_resource_index.py`: read-only embedded deflate validation, guarded optional private export, web marker index.
- `tools/rom_mips_probe.py`: read-only opcode sample inspection.
- `tests/test_resources_and_mips.py`: synthetic automated regression tests.
- Proprietary firmware and any extracted original resources stay **off public GitHub**.

## Remaining blockers to rebuilding firmware

Image/segment mapping, hardware revision, integrity/signature algorithm, safe packaging, device recovery/rollback, functional target bug logs. No verified flash images, UART procedure or binary patch application has been delivered.

## Vendor version context

DrayTek Australia lists Vigor2133 Series **3.9.9.6**, released **2026-09-18** (see https://www.draytek.com.au/support/downloads/vigor2133-series/); the examined 3.9.7 baseline is older. Verify regional model compatibility and vendor release notes before upgrading. Firmware source remains proprietary.
