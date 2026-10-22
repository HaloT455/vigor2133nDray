# P27 — firmware extraction verified on user-provided P25 image

**STATIC RESEARCH ONLY. NEVER FLASH EXPERIMENTAL OUTPUT.**

Input: `ALICE_V2133n_P25_CHAT_FIX_P12_BASE_NOT_FLASH_VERIFIED.all` (**15,761,588 bytes**), SHA256 `009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2`.

## Verified image layout

| ROM range | Finding | Verified static output |
|---|---|---|
| `0x100`–`0x5270` | Candidate MIPS big-endian loader/stub | CPU load address unknown |
| `0x5270`–`0x90961f` | RTOS raw LZ4 length-prefixed stream | 290 blocks; 19,001,596 bytes |
| `0x909620` | `DLM/1.0` module directory | Four entries with contiguous, in-bounds byte ranges |
| `0x93fdf4`–`0xf0807d` | PFS LZ4 stream | 111 blocks; 7,273,845 bytes |
| `0xf08084` | `DrayTekImageMD5\0` tag | MD5 calculated on bytes before tag matches stored value |

SHA256 decoded RTOS: `6018940fd0b28e905504db13e01d4b979bd0c03eda5241be8cf005912f8de612`.

SHA256 decoded PFS: `e88ea747c01937c1356929a2b4d4cdc660877b4456b787efddd33e919232d89b`.

Footer MD5 exact match: `34fe48b33db4ea52afc162c5405371f9` over first **15,761,540 bytes**. **This is NOT proof of a valid vendor signature, ROM header integrity or flashability.**

## DLM files

- `usr32ssh.dlm`: 64,108 bytes.
- `usr32geoip_data.dlm`: 500 bytes.
- `usr32appe.dlm`: 154,180 bytes.
- `usr32alice.dlm`: 4,196 bytes.

The DLM code and relocation/signing/loading ABI remain unverified.

## PFS filesystem

Decoded `PFS/1.0` contains exactly **1,312** directory entries, each **44 bytes** (32-byte padded pathname, 4-byte metadata, 4-byte little-endian offset, 4-byte length). The data section begins at offset `0xe190` (57,744) in the decoded PFS container. All offsets are contiguous and cover the payload exactly.

- 771 PFS files use nested length-prefixed LZ4.
- 5 of these 771 use two compressed blocks.
- 541 PFS files are stored directly (raw bytes).
- 1,312 file payloads were successfully decoded in private validation.

The individual recovered resource files are **not published to this public repository**. Their names and SHA256 are available in the user's locally generated private manifest.

## Offline use

```bash
python3 -m pip install -r requirements.txt
python3 tools/p27_container_unpack.py /path/to/firmware.all \
  --verify-sha256 009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2 \
  --out experiments/p27_report.json \
  --manifest-private experiments/private_manifest.json \
  --export-private private-extracts/
python3 -m unittest discover -s tests -v
```

Do not commit private exports to public GitHub. Do not attempt a patched ROM upload based on the trailing MD5 field alone.

## Port readiness

The file-container format is now sufficiently understood to extract RTOS, DLM and UI assets. **Original DrayOS source code has not been recovered**. Still required: SoC identification on the physical board, RTOS runtime/ABI analysis, module relocations, exact boot memory mapping, complete vendor signature/checksum behavior and a validated recovery setup. For OpenWrt-style ports, independently verify the Ethernet switch, Wi-Fi chipset, calibration storage and supported Linux device tree/drivers.

Related independent research: [infobyte/draytek-arsenal](https://github.com/infobyte/draytek-arsenal).

Read-only analysis is safe on local firmware copies; no generated firmware is flash validated.
