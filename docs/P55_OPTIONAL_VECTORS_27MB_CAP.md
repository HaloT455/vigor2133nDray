# P55 — 26.56 MB opt-in offline vector addon (research only)

Input images privately supplied by user:
- P54 SHA256 `66a9dafb5e218223e02b9dcf06843e7260c9b675266232d1b69e915d35ee6920`
- P38 donor SHA256 `a287ff316c37b64563d7b51c640017c0bc8bbd9656e0e7d037ba2b03035f9742`

**Actual privately generated output:** `ALICE_V2133n_P55_EXTENDED_VECTORS_NOT_FLASH_VERIFIED.all`, 26,555,188 bytes, SHA256 `aaa0f126fa98ebf3403f8315a1fd378c5e29d3d7bfb67de9af0243c1234c46ad`. This is **444,812 bytes below** the requested 27,000,000-byte cap. It was intentionally not padded to exactly 27 MB.

Original P54 BIN stays byte-identical. All 1,315 PFS resources verified in a full WEB decompression roundtrip; 1,310 original decoded assets are unchanged, 2 ALICE HTML pages add an opt-in button, and 3 new PFS assets supply the 40,000 synthetic example vectors from P38 and a lazy loader. The source package contains a SHA-guarded private builder and tests. The vector addon is **not a generative LLM or trained autonomous firewall**; it does not enable router QoS writes.

**Offline tests passed:** known BIN/WEB/trailing-MD5 checks, archive validation, JavaScript syntax, and Node.js executing the added lazy loader against both actual donor vector files (40,000 rows); it did not override a confident response from the original small ALICE model.

**HARDWARE NOT VERIFIED — DO NOT FLASH.** The P38/P39 expanded WEB research releases previously coincided with the user reporting OEM interface and missing ALICE resources; the router may not accept a 16.86 MB WEB partition or allocate enough RAM. A 27MB user budget is not proof of flash partition or bootloader compatibility. Original P54 remains the better-controlled ROM for functional and data-collection debugging.

This project deliberately does not publish the proprietary P38/P54/P55 firmware binaries to a public repo. Private P55 .all and reproducible source ZIP were delivered to the user as conversation files. Source ZIP includes `build_p55.py`, dependencies and read-only verification scripts.

Further work needed for real home-network automation: acquire fresh DrayTek DFM/CPU/WAN measurements, identify trusted management interfaces and rollback, and configure Linux sidecar in LAN routing path. Merely filling ROM storage does not satisfy these requirements.
