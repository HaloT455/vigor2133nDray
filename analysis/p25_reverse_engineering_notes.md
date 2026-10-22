# P25 reverse-engineering notes — Vigor2133n / 3.9.7_Anphat

## Scope and trust

This is **static binary observation** of the user-uploaded `.all`; no live router, bootloader, serial console, partition dump, vendor checksum source, or hardware revision was supplied. The name includes `BASE_NOT_FLASH_VERIFIED`; that remains true.

## Observed header layout (hex offsets)

| Offset | Finding | Confidence |
|---|---|---|
| 0x00000000–0x00000007 | Opaque 8-byte field `0093fdec07909618`; purpose/checksum **unknown** | exact raw bytes |
| 0x00000008–0x00000017 | Opaque identifier with printable bytes | exact raw bytes; meaning unknown |
| 0x00000018–0x0000001f | `v2133` | directly observed |
| 0x00000020–0x0000003f | `3.9.7` | directly observed |
| 0x00000040–0x0000005f | `3.9.7_Anphat` | directly observed |
| 0x00000068 | `V385` | directly observed |
| 0x00000100 | Code-like sequence; probable MIPS big-endian machine code | inferred, **not** independently disassembled |

Size: **15,761,588 bytes**. SHA256: `009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2`.

## Candidate regions / leads (NOT partition boundaries)

- Around `0x00691024`: `Vigor2133 Series` visible in printable bytes.
- Around `0x00735d4f` and `0x0073ae41`: embedded build path fragments resembling `/mnt/hdd/PL_firmware/v2133/V385/`.
- `0x00945de3`: first observed `PK 03 04` ZIP local-file magic. Additional entries near `0x00948850` and `0x0094b234` have `META-INF/DRAYTEK_.SF` and `META-INF/DRAYTEK_.RSA` names. **These are likely embedded Java/JAR resource fragments, not evidence the entire ROM is ZIP.** At the first marker, local header length fields are implausible; trying to open a naive carved span as ZIP failed. Do not use a magic hit as a validated extraction.
- Observed signatures: ZIP-local **57**, ZIP-central **4**, ZIP-end **2**, ELF **1**; common SquashFS, UBI erase-counter, uImage and gzip **0** under direct byte-pattern scans. Matches can occur by chance; the ELF match is not an ELF validation.
- Several regions near/after 0x00900000 have high byte entropy. This is not sufficient to distinguish compression, encryption and packed data.

## What is NOT known

- CPU model and effective load address; entry point; executable and data regions.
- Firmware header algorithm, signature authenticity, partition map and integrity validation.
- Valid filesystem extraction, complete human-readable source, linker maps and reproducible repacking.
- Whether the uploaded experimental build can boot or retains a safe recovery route.

## Next study

1. Identify exact board and ROM flash chip/partition layout via official hardware references and serial console.
2. Validate the first code region with a MIPS big-endian disassembler (e.g., Ghidra) and characterize the bootloader.
3. Verify archives through real headers, file-length fields, CRC and decompression; audit extracted files for secrets **before** any public Git commit.
4. Establish exact firmware checksum/signature/rebuild process and create offline round-trip verification.
5. Fix only one reproducible defect at a time on a separate branch and compare resulting binary hash/blocks.

**Not for flashing**: no modified ROM has been validated and no automated flashing workflow exists.
