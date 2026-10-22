# P56 — Compact ALICE operations and X270 bridge (2026-10-22)

**ROM (private, attached in chat):** `ALICE_V2133n_P56_COMPACT_OPERATIONS_UNTESTED.all` — **16,281,556 bytes**, SHA256 `9a265566047979e7af77b2fbc7ea1764f65fed7ff7b8e9d4e5d5881021f5bc07`.

**Base:** audited P54, SHA256 `66a9dafb5e218223e02b9dcf06843e7260c9b675266232d1b69e915d35ee6920`; **not P55**. 1,312/1,312 PFS decoded and compared, only `V2000\\alice.htm` and `V2000\\DOC\\alice_ai.htm` modified, original RTOS BIN identical, checksum+MD5 valid. This is a research image **NOT TESTED FOR BOOT/FLASH on real hardware**. Only compatible hardware trials with backup and recovery can establish that.

The private reproducible **full Gateway+Guardian+firmware source ZIP** is attached in the conversation, not uploaded as proprietary router firmware to a public GitHub repo. The source uses P54's compressed BIN/WEB/PFS builder, caps output under 17,000,000 bytes and refuses wrong baseline hashes.

## What's actually implemented

- HTML Network Operations panel distinguishing native DrayOS CPU/RAM, X270 Gateway, per-client rate collection and SmartRoute/LLM status.
- New Linux gateway `telemetry_bridge.py`: sanitized browser-observed per-private-client TX/RX => local mode-0700 Guardian data directory => atomic snapshot, no router credentials and no network writes.
- Per-device weighted QoS **review-only** plans requiring fresh client TX/RX and an operator's real WAN download/upload measurements. Optional private-IP `interactive / normal / bulk / iot` classes supplied via root-only CLI; do not infer application category from traffic volume.
- `device_learning.py`: after five distinct traffic samples learns a conservative per-device EMA baseline; three consecutive >3x bursts produce advisory alerts, not bans.
- P54 Syslog-driven abnormal failed-login/scan detection, optional opt-in trusted router listener, safe local nftables proposal retained.
- SmartRoute's multiple OpenAI-compatible LLM providers/fallback retained; no provider activated without credentials/config.
- Installer creates backups and performs three API health checks with rollback.

**Synthetic tests:** 14/14 Python unit tests, 1 cross-process HTTP smoke test (Gateway POST `/alice-api/observe` -> sanitized local file -> Guardian `/api/status`), Node.js syntax check from real compressed HTML. No actual DrayOS/Deco controls were tested.

## What remains unimplemented

Router/Deco configuration write APIs, confirmed physical DrayOS measurements, whole-LAN firewall enforcement, safe unattended changes/revert and distributed system access; the X270 at `192.168.2.210` is not inline with all packets. So `router_autotune_enabled=false`, `router_rules_applied=0`, `applied=false`. DNS AdGuard is documented but DHCP router/Mesh not changed. This release **does not** claim fully autonomous whole-home security, real AI self-code execution, or hack-back.

To install the attached Linux source on X270 (requires previous P51 Gateway and P54 Guardian installed):

```bash
unzip -o ~/Downloads/ALICE_P56_SOURCE_AND_GATEWAY.zip -d ~/ALICE_P56
cd ~/ALICE_P56/ALICE_P56_SOURCE
python3 -m unittest discover -s tests -v
python3 tests/p56_http_smoke.py
sudo bash gateway/install_p56.sh
```

Measured WAN speed is required for a nonempty QoS plan:
```bash
sudo python3 /opt/alice-guardian/set_wan_capacity.py --down-mbps YOUR_MEASURED_DOWN --up-mbps YOUR_MEASURED_UP
sudo python3 /opt/alice-guardian/set_device_class.py --ip 192.168.4.X --class interactive
```

A CORS/CGI diagnostic and authorized DrayOS/Deco management API validation are the next acceptance gates. Do not use synthetic traffic values to configure live router QoS. Keep the official model-matched DrayOS firmware security patched.
