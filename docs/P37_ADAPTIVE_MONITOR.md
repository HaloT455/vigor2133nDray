# P37 — Adaptive local ALICE monitoring; P36 UI and logo preserved

Research-only PFS build. This is **not** a flash-verified firmware.

## Exact offline artifact (private, not committed)

- Input: P36 SHA256 `8dd06e2a7c95d6831b6105d9169d18effb778a1acf4f53a8b4ca2f4d71ed56e5`.
- P37 output: **16,409,384 bytes**, SHA256 `10b137645446d8d41a9391e496efd19925fa2ad518c550fc6b3fbd7791859232`.
- Limit: 27,000,000 bytes; image is **10,590,616 bytes below limit**.
- 2 modified WEB/PFS items: `V2000\alice.htm`, `V2000\DOC\alice_ai.htm`. **1,312/1,312** PFS resources roundtrip-verified.
- Login HTML/CSS, DrayOS auth and original inlined GHQ Halo logo: **identical to P36**, not redesigned. Embedded logo matches original `V2000\IMAGES\halo.png`; no HTTP image dependency.
- RTOS BIN bytes: unchanged. Known BIN/WEB checksums and trailer MD5: pass.
- P36 model, app, controller and network JS assets: unchanged.
- P36 offline chat fallback: remains embedded in both ALICE pages.

## What "self-learning" actually means

The browser-only [P37 adaptive monitor](../web/alice_p37_adaptive.js) learns normal CPU/RAM values **only from real measurements that the existing DrayOS dashboard successfully displays**, using a bounded history of up to 144 numerical samples (stored for at most 7 days). Baselines require at least 12 samples. High CPU/RAM relative to that baseline can generate notices. It also counts model-predicted *categories* of questions; it does not store chat text, credentials, MAC addresses, or browsing logs. A user can clear learned local data.

If there are no measurements because the original router integration is not authenticated or the original native chat/dashboard app failed, **there is no CPU/RAM learning**; the tool does not fabricate network observations.

The safe autonomous tasks are **read-only trend monitoring, alerts, and using P36 chat fallback to remain responsive**. This is not an independently running router-side service and it stops collecting when the browser page is closed. It does **not** rewrite the existing 15-intent model weights, train a general LLM, reboot routers or silently change WAN/DHCP/firewall/VLAN/mesh state.

The separate `192.168.4.145` AI server is still not installed or created by these web UI changes.

## How to build with private P36

Use the separate provided P37 source ZIP, which includes the actual firmware rebuild and verification script. The current public GitHub repository includes the privacy-safe P37 model/monitor tests but **not** the proprietary original firmware or user-customized ROM binaries.

## Acceptance and known limits

- Synthetic Node.js adaptive tests: PASS (learning, anomalies, bounded state, privacy, reset).
- Private offline firmware roundtrip and 8 P37 integration tests: PASS.
- Live router boot, ALICE visual behavior and physical auto networking actions: **NOT TESTED**.
- Avoid flashing without a verified rollback/recovery procedure. Checksums/MD5 are not bootloader or device safety certification.

The 27 MB allowance is a **limit, not a reason to fill flash unnecessarily**.
