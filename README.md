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
