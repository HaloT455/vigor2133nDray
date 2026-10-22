# P44: fix broken P43 login layout; correct X270 gateway instructions

The user booted P43 and showed the login fields panel extending beyond its rose-themed outer card. Root cause: DrayOS legacy login tables generated via `document.write()` still had fixed widths (e.g. 524px), while P43 set the outer form width to 460px. P43 styling gave the nested fields table an additional border/background, creating an overlapping second card.

## P44 offline ROM fix

- Exact private P43 input SHA256: `4aa54ed7885908ece08efd2850bb9df00e5a979cd6f59af6de41dc7bafbca742`.
- Output: **16,267,564 bytes**, SHA256 `4af220cf809c28f432d874f605fc090db0b96b4edca13493ce94cb6b7c6f8a5f`.
- Only 4 login HTML variants modified, **1,312/1,312** resources verified, RTOS BIN byte-identical, BIN+WEB checksums and footer MD5 valid.
- CSS and DOM code constrain all login tables to 100% of the card, eliminate nested box border, center branding, retain username/password, CGI, SSI and session/auth fields.
- Chromium render test of locally generated representative template: at 1366px viewport the 440px card is centered and table right edge stays within the card; at 375px the page has no horizontal overflow. This is **not on-router proof**.
- Experimental `.all` has NOT been booted/flash-certified. Do not commit proprietary ROM to public repository.

## Why .145 failed

On ThinkPad X270, user output: `wlp3s0 192.168.2.210/24` and `cd gateway` failed because the ZIP was not extracted. `curl http://192.168.4.145/alice-api/health` failed because that IP is not assigned to the host and no service is running.

New Gateway package has `gateway/start_local.sh`, `gateway/start_lan.sh`, `gateway/network_diagnose.sh`, `gateway/install_service.sh`. It runs first on **127.0.0.1:8080 without sudo** and can optionally listen at **192.168.2.210:8080** while the host retains that IP. It never changes Linux networking or router WAN/LAN automatically.

Do not blindly assign `192.168.4.145/24` to the `.2.x` Wi-Fi network or alter `192.168.4.1`; verify actual L2/L3 routing, interface and DHCP before selecting an alias. The embedded router ALICE UI still refers to .145 until this is correctly deployed; the standalone gateway works independently.

**P44 router boot and .145 connectivity: NOT VERIFIED**; local prototype rendering, firmware structural checks and HTTP/AI chat tests: VERIFIED.
