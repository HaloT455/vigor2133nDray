# P42 — ALICE IP 192.168.4.145: diagnosis and conservative UI fix

## Network finding

P41 front-end points to `http://192.168.4.145/alice.htm`; its app JS also chooses `http://192.168.4.145` for the remote AI gateway. No deployed TCP/HTTP listener, ARP/alias ownership or native AI service at that address has been established. The authenticated modem ALICE page uses `/doc/alice_ai.htm`, while direct `/alice.htm` previously returned 404. **Changing PFS HTML/CSS/JS does not assign a LAN IP to the router, does not create a persistent DrayOS service or guarantee host-specific routing.**

Generic DrayTek documentation describes LAN IP Alias for some Vigor platforms, but this particular Vigor2133n 3.9.7 firmware has not been confirmed to offer that control. The Vigor2133 manual documents `ip addr [IP]` as changing the LAN IP; **do not execute it** to add .145 while intending to preserve management .1.

The .145 address was inside the previously reported P25 DHCP range .10–.209; avoid duplicate leasing before any static alias configuration.

## P42 offline UI-only patch

Built from user-provided P41 SHA256 `b4a9f39894418a0258b2223d491799c8b8765517bb3c3bdf129f537ac889efa2`.

- ROM **16,174,604 bytes**, SHA256 `ef7df2f2985eeaa436f01f9e7b78fafbbfc072ffc06be828264f85c3f1bae66e`.
- Corrects dead `Cổng Alice` link in both ALICE HTML pages to the existing authenticated router-side `/doc/alice_ai.htm`.
- Adds strong inline styles and removes old dynamically selected DrayTek banner image references on 4 login templates, while retaining original auth scripts and input fields.
- Exactly 6 WEB/PFS resources changed; 1,312/1,312 roundtrip checked, original BIN unchanged, known WEB/BIN checksum and MD5 valid.
- **No new .145 IP, listener or router-side AI daemon is installed.** Physical P42 boot not tested. Experimental output is NOT FLASH VERIFIED.

## Safe next technical check

From a Linux computer currently in the router's LAN:
```bash
bash check_alice_145.sh 192.168.4.1 192.168.4.145
```
Script performs read-only ICMP, HTTP and route checks without disclosing credentials or ARP MACs. If .145 is not reachable, no amount of repackaging HTML makes .145 ownable. A correctly implemented native router endpoint requires a validated LAN alias/static address and DrayOS HTTP routing/API backend, and an explicit proof of both.

Do not put a private .all ROM on this public repository. Keep a proven recovery image before any firmware experiment.
