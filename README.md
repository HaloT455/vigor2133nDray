# ALICE / Vigor2133n firmware research

> **RESEARCH ONLY — NOT FLASH VERIFIED.** A proprietary `.all` firmware image is compiled machine code, **not** reconstructible original C source. This repository contains original analysis tools, baseline metadata and a reproducible local workflow — not a verified DrayOS firmware builder.

## Baseline — uploaded image

- Target router: **DrayTek Vigor2133n**; header identifies family `v2133`, **not** the exact hardware variant.
- Firmware version: `3.9.7`; distribution `3.9.7_Anphat`; build-family tag `V385`.
- Research filename: `ALICE_V2133n_P25_CHAT_FIX_P12_BASE_NOT_FLASH_VERIFIED.all`.
- Size: **15,761,588 bytes** (~15.03 MiB).
- SHA256: `009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2`.
- Apparent MIPS big-endian code from offset `0x100` (requires disassembly confirmation).
- ZIP markers are present, but **raw magic matches do not establish a valid archive or filesystem**.
- ROM checksum/signature rules, partitions and safe repacking method remain **unknown**.

## Working with your original ROM locally

Never commit router configs, passwords, keys or proprietary `.all` images to this public repository.

```bash
python3 tools/rom_audit.py /path/to/firmware.all --verify analysis/p25_baseline.json --out experiments/audit.json
python3 tools/rom_diff.py /path/to/firmware.all /path/to/modified.all --out experiments/diff.json
python3 -m unittest discover -s tests -v
```

- `tools/rom_audit.py`: read-only header, file hash, entropy blocks and signature inventory.
- `tools/rom_diff.py`: 4 KiB block-level change inventory.
- `tools/rom_patch_lab.py`: guarded, same-length byte replacement for **offline experiment only**, NOT a flashable firmware generator.
- `analysis/p25_baseline.json`: snapshot of the uploaded ROM.
- `.github/workflows/source-checks.yml`: CI uses synthetic fixtures; no firmware upload or flashing.

## Engineering process

1. Keep this baseline immutable. Work only on a dedicated development branch.
2. Back up the router configuration and secure a known-good recovery path; document hardware revision.
3. Map the ROM image and validate segment boundaries (MIPS disassembler, headers, checksum, filesystem verification).
4. Record a **specific** bug and reproduce it with logs; isolate the smallest change.
5. Do not flash a patched firmware until checksum/signature/loader compatibility, rollback and physical device test are proven.

Upstream reference: [gckrol/draytools](https://github.com/gckrol/draytools) is an archived research project that lists older Vigor models; **Vigor2133n is not on its tested list**. It is not a validated repacker for this image.

DrayTek documentation: [difference between ALL and RST](https://www.draytek.com/support/knowledge-base/difference-between-firmware-files). Firmware `.all` typically preserves configuration, while `.rst` restores factory defaults. Neither implies a manually patched image is safe to install.

## P26 enhanced static inspection

```bash
python3 tools/rom_resource_index.py /path/to/firmware.all \
  --verify-sha256 009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2 \
  --out experiments/resources.json
python3 tools/rom_mips_probe.py /path/to/firmware.all --offset 0x100 --count 32 \
  --out experiments/mips.json
# Optional PRIVATE export of CRC+size validated resources:
python3 tools/rom_resource_index.py /path/to/firmware.all --export private-extracts/
python3 -m unittest discover -s tests -v
```

Research findings on the uploaded P25 image: **8** strictly validated deflate entries, **3** rejected for descriptor size mismatch, and **32/32** MIPS big-endian candidate words recognized by a limited decoder at 0x100. Raw occurrences of HTML/VLAN/mesh strings do not prove independent features. See [P26 map](analysis/p26_rom_map.md) and [roadmap](docs/PHASES.md).

The official Australian [Vigor2133 Series download page](https://www.draytek.com.au/support/downloads/vigor2133-series/) lists firmware **3.9.9.6**, dated 2026-09-18. Do not flash unknown images: check exact model and region, vendor release notes and a reliable recovery method first.

Potential AA1D7F50 record layout: 212 raw markers, 146 sizes point inside the file, 14 inferred ends touch the next marker. Use `python3 tools/rom_record_probe.py firmware.all --out experiments/records.json` for reproducible *unvalidated* analysis. The format is not solved and existing HTML fragments contain embedded control bytes; naive HTML carving is not reliable.

## P27 structural reverse engineering — recovered container layout

The checked P25 image contains a 290-block length-prefixed LZ4 RTOS region (19,001,596 bytes decoded), a four-entry `DLM/1.0` directory, and a 111-block LZ4 `PFS/1.0` resource area (7,273,845 bytes decoded). PFS has 1,312 indexed resources: 771 LZ4-encoded (5 span more than one chunk) and 541 raw. See [analysis/P27 report](analysis/p27_unpack_report.md).

The DrayTek section format is also validated: two independent big-endian 32-bit additive one's-complement checksums (BIN and WEB sections both sum to `0xFFFFFFFF`) plus a matching `DrayTekImageMD5` footer. Run `tools/p27_integrity.py` to validate these offline. These integrity checks **do not guarantee flashability or reconstruct any original vendor source code**.

```bash
python3 -m pip install -r requirements.txt
python3 tools/p27_container_unpack.py firmware.all \
  --verify-sha256 009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2 \
  --out experiments/p27.json --manifest-private experiments/manifest.json \
  --export-private private-extracts/
python3 tools/p27_integrity.py firmware.all \
  --expect-sha256 009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2
```

**No extracted proprietary firmware, driver, DLM or UI assets have been committed to the public GitHub repository.** Complete port readiness still requires hardware/SoC, boot address, DLM ABI, firmware loader and rollback validation.

## P28 static port mapping (not a completed source port)

The next research tool, [`tools/p28_port_inventory.py`](tools/p28_port_inventory.py), inspects private P27 RTOS/DLM/PFS exports for **hardware driver fingerprints**, **partial DLM header consistency**, a **heuristic MIPS call target map**, and **static ALICE login-page asset references**. Its outputs exclude the original firmware content, scripts with embedded credentials, and proprietary binaries. See [P28 readiness gates](docs/P28_PORT_READINESS.md).

```bash
python3 tools/p28_port_inventory.py \
  --rtos private-extracts/rtos/rtos_mips_candidate.bin \
  --dlm-dir private-extracts/dlm \
  --pfs-dir private-extracts/pfs/V2000 \
  --expected-sha256 6018940fd0b28e905504db13e01d4b979bd0c03eda5241be8cf005912f8de612 \
  --out experiments/p28_inventory.json
```

**Do not confuse green CI with recovered DrayOS source, a bootable port, or proven safe firmware.** Hardware-specific porting still requires exact destination hardware, serial console evidence and board driver validation.

## P29: Verified offline WEB/PFS re-packing laboratory

The latest tool is [`tools/p29_lab_repacker.py`](tools/p29_lab_repacker.py) and regression tests are in [`tests/test_p29_lab_repacker.py`](tests/test_p29_lab_repacker.py). On the original P25 image: bit-exact no-op reassembly matched the complete original SHA256; full WEB re-compression decoded back to the same **1,312 resources**; and a private test modification to `V2000\\alice.htm` was recovered without altering any other decoded resource. BIN checksum, WEB checksum and footer MD5 matched in all three offline tests. See [P29 validation](docs/P29_OFFLINE_REPACK_VALIDATION.md).

```bash
python3 tools/p29_lab_repacker.py firmware.all \
  --expected-sha256 009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2 \
  --no-recompress --report experiments/p29_noop.json
python3 tools/p29_lab_repacker.py firmware.all \
  --expected-sha256 009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2 \
  --report experiments/p29_repacked.json
```

This is **research output, NOT FLASH VERIFIED and NOT the full DrayOS source**. A valid MD5 and package checksum are insufficient proof that a patched image can boot. The destination hardware has not been identified or physically tested.

## P30 MIPS ELF research import

The original **19,001,596-byte** extracted RTOS payload can now be wrapped for private use into an **ELF32 big-endian MIPS** analysis file with [`tools/p30_mips_elf_view.py`](tools/p30_mips_elf_view.py). The user ROM output was successfully decoded by `llvm-objdump` in the local analysis environment, exposing MIPS instructions and potential call sites. See [P30 validation](docs/P30_DISASSEMBLY_IMPORT.md). No real runtime load address, verified entry point, source code, linker sections, or flash-boot compatibility has been established.

**Green tests refer to the research toolchain, not completion of a DrayOS/OpenWrt port.** Never flash experimental `.lab.bin` or `.analysis.elf` output.

## P31 — verified offline progress toward porting

Added source for static MIPS cross-reference candidates, DLM structural analysis, an evidence-driven port gate, and privacy-conscious UART triage. The completely extracted **19,001,596-byte** RTOS was scanned; 19,711 prologue **candidates** and 117 matching low-28-bit JAL-target candidates were found, **not recovered source functions**. All four DLM headers passed structural validation, but the loader ABI is unknown.

A new independent [C HAL scaffold](port_scaffold/) compiles on the host and as a MIPS32r2 big-endian **relocatable object**. This verifies the cross-compiler and interface syntax; it is **not** a bootable router firmware or actual device driver. GitHub CI now tests both the Python research toolkit and the host/MIPS HAL build.

Run static analysis privately:
```bash
python3 tools/p31_rtos_xrefs.py private-extracts/rtos/rtos_mips_candidate.bin \
  --expected-sha256 6018940fd0b28e905504db13e01d4b979bd0c03eda5241be8cf005912f8de612 \
  --limit-mib 20 --out experiments/p31_xrefs_private.json
python3 tools/p31_dlm_abi_probe.py private-extracts/dlm --out experiments/p31_dlm_private.json
make -C port_scaffold host-check mips-object
python3 tools/p31_port_gate.py --out experiments/p31_gates.json
```

**The four full-port goals remain NOT COMPLETE** until real source or functional reimplementation, chip-specific drivers, a bootable router image and physical UART/network/rollback tests exist. A green CI badge proves tests, not boot. See [evidence gates](docs/P31_PORT_COMPLETION_GATES.md).
