# P61 — Native RTOS integration audit (read-only)

The user requires a standalone Vigor2133n .all with resident AI for WAN blocking, per-device QoS, isolation, and network management; no X270.

## Exact private ROM comparison

- Baseline P25 SHA256: 009d4fa7eb4dc3428d9956505fa4463384d7e8a6c8bddea230b1abc907ebd2c2.
- Router-only UI P58 SHA256: 6a2c9fbd3c18702dbf887c002689a48b41cd53a9ecc4bcd3c9c6199a1dc03807.
- Native decoded RTOS image: all 19,001,596 bytes identical in P25 and P58. Both decoded RTOS SHA256: 6018940fd0b28e905504db13e01d4b979bd0c03eda5241be8cf005912f8de612.
- All four DLM payloads are byte-identical, including usr32alice.dlm (4,196 bytes, SHA256 f64221eb309aa88ef2f1f733b530a8fd72263e93730bd01e00849bdf686433e1).
- P58 has 1,312 WEB/PFS indexed assets. Footer MD5 matches, but this cannot prove hardware boot.

## Native execution blocker

The usr32alice.dlm body is an opaque proprietary module, not MIPS ELF. Presence of the module and DLM-related strings in the RTOS do not establish a verified loader ABI, relocation process, periodic task entrypoint, or secure Firewall/QoS read/write APIs.

P60 contains tested freestanding MIPS32 code and simulated OEM callback wrappers, NOT linked native code loaded on the device. Appending a P60 ELF relocatable object to this DLM is unsupported and risks an unbootable router.

## Outcome

No falsely advertised complete P61 .all was produced or recommended for flashing. Hardware integration needs verified OEM loader/SDK ABI (or validated equivalent), real traffic and system APIs, configuration readback and rollback, board flash/recovery data, then an independent boot/test on physical Vigor2133n. Third-party Deco automation additionally needs legitimate control APIs.

DrayOS built-in DoS Defense, Brute Force Protection, Bandwidth Limit and Auto Adjustment can be configured on the modem without an external laptop, but are NOT resident ALICE P60 AI.

All forensic comparisons were read-only and did not upload proprietary firmware to GitHub.