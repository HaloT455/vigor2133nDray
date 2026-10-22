# P58 — Vigor2133n standalone router UI (no laptop)

Private patched **P58 .all**: **16,280,056 bytes**; SHA256 `6a2c9fbd3c18702dbf887c002689a48b41cd53a9ecc4bcd3c9c6199a1dc03807`.

- Exact **P57** private base SHA256 `e0ac07ddd47e3439ffbff971d37630600449f2948ac19e674104d3575d48fcc1`.
- Modified three WEB/PFS assets only: `V2000\\JS\\alice_app.js`, `V2000\\alice.htm`, `V2000\\DOC\\alice_ai.htm`.
- Original RTOS BIN bit-for-bit unchanged, **1312/1312** PFS decoded resource checks and known BIN/WEB/footer MD5 checks valid.
- Local test: **6/6** Python unit tests, Node syntax on all inline scripts and patched `alice_app.js`, HTML structural parsing.
- ROM NOT tested on physical router for safe flash or boot. A successful repacker test does not certify it.

## Exact scope and functionality

The P58 HTML eliminates the active `192.168.2.210` Gateway polling and cloud chat path and hides obsolete P51–P57 Linux-only cards. Existing local rule-based AI, OEM management UI, authenticated CGI statistics and device flow reading remain. Added a standalone six-section panel to locate built-in DrayOS security features through the router’s own menu.

DrayOS **DoS Defense** and **Management Brute Force Protection** are persistent native protection mechanisms that can automatically block suspicious traffic or failed logins **only once configured and applied via the native OEM interface**. The firmware image does not pre-enable them, because overwriting operational firewall/NAT/management configuration blind could lock the owner out. The panel gives operational steps. `Bandwidth Limit > Smart Bandwidth Limit` and `Auto-Adjustment` are native QoS features, but still require authentic measured WAN capacity and actual operator configuration. Permanent VLAN and firewall segmentation provides guest/IoT isolation, not AI-triggered unattended per-device quarantine.

**Not implemented:** 24/7 AI daemon/LLM in router executable, autonomous malware-triggered device quarantine, autonomous device-specific AI QoS changes, verified CPU/RAM CGI values, management of TP-Link Deco APs or hack-back. No provider keys or OS binaries delivered. The existing 3.9.7 RTOS binary remains vulnerable to issues fixed in later vendor releases.

The **complete local reproducible source ZIP** (including the exact build script, HTML panel, codec dependencies and P57 hash guard, and unit tests) is attached in the conversation rather than posting private vendor firmware to GitHub.

## Important security baseline

Official source https://www.draytek.com.au/support/downloads/vigor2133-series/ lists Vigor2133 **3.9.9.6 (18 Sep 2026)**. DrayTek's WLAN advisory names **3.9.9.5** fixed for **Vigor2133n**: https://www.draytek.com/about/security-advisory/wlan-driver-vulnerabilities-november-2025/ . Verify actual regional hardware version and backup before installing matched official vendor firmware. P58 WEB/PFS changes do NOT include those RTOS security fixes.

**Safe acceptance steps**: enable and inspect native DoS Defense and Brute Force Protection on the actual router; use modem logs to verify drops, then configure VLAN/Filter Setup with management IP excluded and verify rollback. Do not flash this research .all without established hardware recovery.
