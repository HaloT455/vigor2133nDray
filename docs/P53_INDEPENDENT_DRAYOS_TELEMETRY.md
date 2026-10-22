# P53 — independent read-only DrayOS telemetry fallback (2026-10-22)

This experiment addresses user screenshots where P52 shows CPU/RAM/uptime as dashes, and the older P36 offline chat fallback is active instead of the native DrayOS collection controller.

Private P52 baseline SHA256: `4b07306d3ca566535f8ed3990932234fb46a7081612a9e077e4b9efb9352a567`.

Private P53 research image SHA256: `114f75977e8c96e1e5072cdb874eb23ca20015cd69071cc11e420185b1494327`. Size **16,277,816 bytes** (under 27 MB).

### Data paths verified against embedded OEM HTML, not device response

- DrayOS originally updates Dashboard via `GET /dashbctl.cgi?sFormAuthStr=...&wannum=...&lannum=...`, returning a JSON array of key-value strings. `sysres=CPU,RAM` and `sSystime=uptime` may appear.
- The OEM HTML includes an SSI-expansion expression `makesysres(['<!--#echo var="sArpTbl35"-->','<!--#echo var="sArpTbl36"-->'])` and `ary_sysTime=[<!--#echo var="iSysUpHour"-->,...]`. After server-side rendering these can provide authenticated values even when the dynamic JSON fails.
- The P36 offline chat fallback is deliberately separate from dashboard collection; it being available **does not prove the native app initialized or that CGI data is readable**.

### P53 patch behavior

The added inline `alice_native_telemetry.js` module independently polls these two **read-only, same-origin** sources, using only the authenticated DrayOS page's current session parameter. It never sends the auth value to the X270 AI Gateway. It validates percent values and keeps missing values absent; it displays specific errors (missing session, HTTP error, wrong JSON, unpopulated SSI) instead of showing an unexplained dash. An explicit recheck button is shown.

Exactly 2 HTML resources patched: `V2000\\alice.htm` and `V2000\\DOC\\alice_ai.htm`. No modification to RTOS BIN, network settings, DrayOS auth or existing P52 QoS safeguards.

**Local verification**: exact P52 input hash guard; 1,312/1,312 PFS resources compared after repack; unchanged BIN; all known BIN/WEB/trailer-MD5 checks; Node.js synthetic test passed JSON `sysres`, SSI fallback, missing auth, and HTTP 403 cases. Reproduction source and actual privately patched firmware have been delivered as conversation files.

**NOT VERIFIED ON PHYSICAL ROUTER**. Do not confuse valid firmware checksums with successful boot or real CGI responses. Neither the existing DFM nor per-client traffic can be inferred from CPU/RAM samples. If P53 displays a server-side error, capture only sanitized error/status text (not tokens or full CGI replies) before further firmware changes.

This project does not put private proprietary firmware or secrets in public GitHub.
