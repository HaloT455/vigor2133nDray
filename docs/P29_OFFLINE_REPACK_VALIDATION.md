# P29 — verified offline WEB/PFS rebuild laboratory

**DO NOT FLASH experimental output.** This is not a DrayOS source compiler or a vendor-signed image builder. A router bootloader and its recovery path have not been tested.

## Baseline verification (user's P25 firmware, run 2026-10-22)

Original image: `ALICE_V2133n_P25_CHAT_FIX_P12_BASE_NOT_FLASH_VERIFIED.all`, **15,761,588 bytes**, SHA256:

`009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2`

Results on the **actual user-provided ROM**:

| Offline test | Bytes | SHA256 | Resources checked | Outcome |
|---|---:|---|---:|---|
| Exact no-op composition (preserve existing LZ4 bytes) | 15,761,588 | `009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2` | 1,312 | Byte-for-byte identical |
| Full WEB/PFS LZ4 recompression without logical changes | 15,844,120 | `2c0e4c3be2fa3b3e98fac57f0a9e98d299d9112bb8f1fba98d1566eb0b9eb79d` | 1,312 | All content matches |
| Offline experimental replacement of `V2000\alice.htm` | 15,844,156 | `d673191315b7c6e7937caf1fc1aff098ee7895cb942fae198e03046ca2ee2d8c` | 1,312 | One resource changed; remaining 1,311 unchanged |

For each test, both 32-bit additive section checksums and the trailing MD5 matched; the binary BIN section was preserved verbatim. The changed UI file gained 39 decoded bytes containing a harmless lab comment. **The experimental image was not saved as a flashable firmware release.**

## CLI

```bash
python3 -m pip install -r requirements.txt

# Byte-identical no-op (no .all output):
python3 tools/p29_lab_repacker.py /path/to/baseline.all \
  --expected-sha256 009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2 \
  --no-recompress --report experiments/p29_exact_noop.json

# Full PFS re-compression and resource-equivalence verification:
python3 tools/p29_lab_repacker.py /path/to/baseline.all \
  --expected-sha256 009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2 \
  --report experiments/p29_recompression.json

# An OPTIONAL research-only local UI replacement:
python3 tools/p29_lab_repacker.py /path/to/baseline.all \
  --expected-sha256 009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2 \
  --replace-name 'V2000\alice.htm' --replace-file /path/to/private_alice.htm \
  --report experiments/p29_modified.json
```

The tool refuses mismatched baseline hash, unknown PFS entry names, unvalidated input checksums and dangerous firmware output extensions. If `--out` is explicitly used, only a new `*.lab.bin` file is permitted — **never flash it**.

## The difference between “green CI” and “port completed”

Confirmed: package decode/re-encode, resource integrity, offline lab patching and synthetic regression tests.

Not confirmed: MIPS RTOS source recovery; module relocation ABI; boot memory layout; actual SoC, RAM, flash, switch and Wi-Fi part IDs; alternate target model; Linux driver integration; bootloader acceptance; UART boot; functional router regression tests; reliable backup and unbrick.

DrayTek's [official Vigor2133 product page](https://www.draytek.com/products/vigor2133/) distinguishes Vigor2133, Vigor2133n, Vigor2133ac and Vac by radios and voice hardware. A string in a firmware binary is not sufficient to identify the assembled PCB.

OpenWrt's [Lantiq platform overview](https://openwrt.org/docs/techref/hardware/soc/soc.lantiq) is a reference for available SoC families, **not** proof of an existing supported image for Vigor2133n.

**No complete original DrayOS source, working firmware port or real-device boot test has been produced.**
