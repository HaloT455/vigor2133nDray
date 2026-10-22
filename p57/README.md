# ALICE P57 — timed external IP block and conditional device isolation

**Research release, 22 Oct 2026; not boot/flash tested.**

Compact private ROM derived from exact P56 SHA256 `9a265566047979e7af77b2fbc7ea1764f65fed7ff7b8e9d4e5d5881021f5bc07`, size **16,282,404 bytes** (<17,000,000), SHA256 `e0ac07ddd47e3439ffbff971d37630600449f2948ac19e674104d3575d48fcc1`.

ROM verification: **1,312** PFS files decoded and compared, only the two ALICE HTML pages modified, original RTOS BIN byte-identical, all known checksums valid. This does **not** verify DrayTek boot/update acceptance.

The complete P57 source ZIP, including the actual Linux files `guardian_enforce.py`, `auto_host_protect.py`, `auto_inline_quarantine.py`, `guardian_service.py`, `install_p57.sh`, `enable_auto_host.sh`, the two HTML resources, standalone private ROM builder and tests, is provided as a conversation attachment. Proprietary firmware images are NOT uploaded into this public repository.

## Function 1 — automatic external ban

- Tested X270-local nftables `inet alice_guard57` input chain with a timed IPv4 set.
- Opt-in `enable_auto_host.sh` installs an SSH journal watcher. Eight failed SSH authentications in five minutes from the same public IPv4 trigger a **300-second** host-only ban. Limits: 20 auto bans/hour, no private/reserved/management IP addresses, no raw logs/credentials exposed in UI.
- **Does not protect unsolicited traffic against other hosts, and does not write rules to DrayTek WAN**. The X270 is not in the router WAN path.
- The program does not auto-ban based on forgeable UDP router Syslog. The real X270 nftables backend still requires a kernel-level test on the user's X270; unit tests used a synthetic nft runner because the local build container did not include nft.

## Function 2 — conditional device quarantine

- Opt-in CLI supports temporary drops in Linux **FORWARD** when X270 is a verified inline IPv4 gateway; current Wi-Fi-connected X270 is NOT inline and should refuse enforcement.
- Requires operator-approved non-management IP/MAC binding and two fresh independent alerts from locally trusted root-controlled IDS and DNS detectors; no such detectors are currently connected. Does not isolate same-L2 Wi-Fi clients from one another.
- **DrayTek IP Filter and TP-Link Deco Device Isolation/Block List are not controlled automatically**: no verified authenticated read/write/rollback API for those specific hardware/firmware variants exists yet. Never pretend 'enabled' in the UI.

## Tests and security

- **13/13 local P57 tests passed**: public IP validation, local/router IP exclusion, SSH threshold, source separation, stale alerts, bounded temporary bans, refusal without inline path, source patch duplicate anchors.
- Synthetic local HTTP smoke test passed Gateway → Guardian with correct P57 `/api/status` and no router writes.
- The next integration gate is an authorized session with the actual Vigor2133n to document firewall filter API and a hardware recovery procedure, plus exact Deco model capabilities.
- No hack-back, autonomous remote code execution, credential storage in firmware, automatic WAN or DNS modification.

### Vendor-backed options while controller integration is unverified

- DrayTek `Firewall > Filter Setup` can create IP-source `Block Immediately` rules; order/precedence matters: https://www.draytek.com/support/knowledge-base/how-the-firewall-filter-rules-work
- Deco `Device Isolation` limits inter-device communication but **still permits Internet access** (model/firmware dependent): https://community.tp-link.com/us/home/kb/detail/412694
- Deco `Block` / Wi-Fi Access Control can deny Wi-Fi connection on supporting models: https://www.tp-link.com/gr/support/faq/3833/

**Bottom line:** both controller workflows have source, operator safeguards and local backend tests; **whole-home automatic WAN bans and Deco quarantine remain unimplemented on the user's hardware** until control paths are validated. The firmware is a compact UI integration, not a new firewall kernel.
