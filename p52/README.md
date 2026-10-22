# P52 — Verified offline build, read-only telemetry diagnosis, safe QoS controls

**Baseline:** the exact private P51 firmware SHA256 `717addfa8655055efe3d9df03cd6e69f1c2ea894642b470de00f66cd4f9a8f24`.

**Local experimental output:** `ALICE_V2133n_P52_SAFE_TELEMETRY_QOS_RESEARCH_NOT_FLASH_VERIFIED.all`, 16,274,408 bytes, SHA256 `4b07306d3ca566535f8ed3990932234fb46a7081612a9e077e4b9efb9352a567`.

All **1,312** private WEB/PFS resources were independently unpacked and compared to expected content. Original BIN unchanged byte-for-byte. Both additive checksums and trailer MD5 validated. **Not validated by real device bootloader or boot/flash on a router.**

## Actual bug and safety correction

P51’s `'optimize'` natural-language handler called `control('shared',false)`, disabling IPv4/IPv6 bandwidth limits and Smart Limit, then attempted to change PPA. Disabling limits is not equivalent to congestion management or per-device QoS. P52 changes the optimize handler to read-only diagnostics. The explicit “remove limits” control warns and requests confirmation before calling the legacy router form. The independent Auto-Adjustment form remains user-operated with native DrayOS authentication and rollback logic.

A reported PPA TCP/UDP **On** means the router form's configuration flags are on, not that actual TCP/UDP utilization was measured. Smart Limit **Off** can be an authentic router state; P52 does not falsify it.

## Telemetry limitation and diagnostic

The router chart depends on the authenticated `/cgi-bin/cgidashboard.cgi` and `/dashbctl.cgi` responses. A no-data dash is correct when CPU/RAM is not supplied; P52 accepts simple labeled percentage strings and keeps missing/ambiguous results as null.

The P52 panel labels each source explicitly:
- DrayOS CPU/RAM: authenticated router UI reading when available
- X270 Linux CPU/RAM: read-only `/alice-api/usage` and **not** router CPU/RAM
- PPA, Auto-Adjustment, IPv4/IPv6 limits and Smart Limit: current configuration states, **not QoS performance measurements**

For real router diagnostics after login, open ALICE from the DrayOS menu, choose its frame in DevTools and run [browser_probe.js](browser_probe.js). It prints only HTTP status, response format, and schema key names, without cookies, auth tokens, raw records, or MACs. The result determines whether the missing data arises from authentication, CGI routing, content format, or firmware limitations.

## Source and reproducible build

The new [P52 builder](build.py) accepts a **user-provided private** P51 `.all` and patches exactly five resources:
- `V2000\\JS\\alice_app.js`
- `V2000\\JS\\alice_ctrl.js`
- `V2000\\JS\\alice_local.js`
- `V2000\\alice.htm`
- `V2000\\DOC\\alice_ai.htm`

```bash
python3 -m pip install -r requirements.txt
python3 p52/build.py --base /private/P51.all --out /private/P52_NOT_FLASH_VERIFIED.all
python3 -m unittest discover -s tests -p 'test_p52_guard.py' -v
```

[CI workflow](../.github/workflows/p52-verified-build.yml) runs the safety tests and **builds an entirely synthetic 1,312-resource ROM to validate the real codec pipeline**. Its artifact is marked **NOT FLASHABLE**. The real P52 `.all` was built locally from private P51, not on public GitHub. Never upload the proprietary firmware to a public CI run.

**Remaining acceptance requirements:** inspect authenticated CGI output in a browser, confirm actual router data, characterize WAN and per-device load, validate effective QoS/Auto-Adjustment and rollback, then test hardware boot/update. No automatic real-router QoS management is enabled.
