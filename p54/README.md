# P54 — ALICE Guardian: defensive home-network AI (2026-10-22)

Built from the exact private **P53** baseline, SHA256 `114f75977e8c96e1e5072cdb874eb23ca20015cd69071cc11e420185b1494327`.

**Private experimental firmware:** 16,278,584 bytes, SHA256 `66a9dafb5e218223e02b9dcf06843e7260c9b675266232d1b69e915d35ee6920`. Under the 27 MB cap. **All 1,312 PFS resources** decoded and verified; only `V2000\\alice.htm` and `V2000\\DOC\\alice_ai.htm` changed to add an independent Guardian link. Original RTOS BIN unchanged; known BIN/WEB/MD5 integrity checks valid. **Never assume it is flashable or boot-tested.**

The browser in DrayOS remains a UI. The actual P54 Guardian is **a separate, unprivileged Python agent on the ThinkPad X270**, not an additional network kernel inside DrayOS. Installing this Guardian does **not** require router reflashing.

## Implemented and tested

- [guardian_core.py](guardian_core.py) and [unit tests](../tests/test_p54_guardian.py) implement threshold-based defensive signals from *verified structured source IPv4* in trusted router Syslog, with no local/private/gateway-IP ban recommendations.
- Read-only fair-share QoS calculations per internal client require real operator-measured WAN upload/download capacity and recent LAN client measurements. Interactive class receives greater share, 15% headroom is reserved. **All proposals set applied=false**; no real QoS/Smart Limit/Deco config is changed.
- X270 host-only firewall preview produces short-lived nftables commands, but never executes them or touches the router. No hostile code, retaliatory scanning, hack-back or unreviewed model-generated code execution.
- The local package includes a status/dashboard service on `127.0.0.1:8091`, optional safe reverse proxy through existing P46 Nginx at `http://192.168.2.210/alice-guardian/`, a sanitized opt-in DrayTek Syslog UDP receiver and a review-only policy proposal generator.
- Local package passed 12 unit tests, direct HTTP GET and POST rejection smoke tests, and 1,312 PFS codec roundtrip checks. GitHub CI tests public Python core only; private firmware and gateway secrets are not uploaded.

## Physical deployment blockers

X270 currently resides at `192.168.2.210`; DrayTek `192.168.4.1` is routed by `192.168.2.1`. The Ethernet port previously had carrier=0. Therefore the X270 is **not** in the Internet forwarding path and cannot filter or shape all house traffic. DrayOS and Deco write APIs/rollback have not been verified. Remote Syslog is supported by Vigor2133 but receiving it requires an actual router path to the X270 and explicit configuration.

Official source: https://www.draytek.com/support/knowledge-base/how-to-collect-routers-syslog and https://www.draytek.com/products/vigor2133/.

## Important firmware security baseline

The user previously reported DrayOS 3.9.7. The vendor advises upgraded firmware 3.9.9+ for some Vigor2133 security fixes and 3.9.9.5 for Vigor2133n WLAN fixes. Only install a **model-matched signed firmware** with verified backup and recovery; the research P54 WEB/PFS patch **does not upgrade or fix the original DrayOS executable**.

- https://draytek.com/about/security-advisory/denial-of-service%2C-information-disclosure%2C-and-code-execution-vulnerabilities/
- https://draytek.com/about/security-advisory/wlan-driver-vulnerabilities-november-2025/

## Safe next acceptance milestones

1. Install P54 Guardian read-only sidecar on the X270; verify `/api/status` on localhost and the proxy route; record actual source.
2. Deliver authenticated, sanitized router firewall Syslog to X270 through an explicitly configured trusted LAN path; confirm observed events only.
3. Read fresh, reliable device rates through Data Flow Monitor and WAN speed tests; validate QoS recommendations.
4. Test narrowly scoped actual configuration apply/verify/revert on Vigor2133n using proven API, backup and dry-run; only then enable unattended changes. Deco is managed via its own platform.
5. Keep per-device bandwidth and security actions auditable, reversible and protected from self-lockout.

This release does NOT promise immunity to all attacks, eliminate physical WAN congestion or perform hack-back.
