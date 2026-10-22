# P47 — Repair dead ALICE gateway references without altering router network settings

Based on P44 research ROM SHA256 `4af220cf809c28f432d874f605fc090db0b96b4edca13493ce94cb6b7c6f8a5f`.

The real X270 gateway is reachable on `http://192.168.2.210/` after P46 Nginx installation; the user has shown that `192.168.4.210` returns ERR_ADDRESS_UNREACHABLE and Ethernet `enp0s31f6` had `carrier=0`. A ROM web interface patch **cannot** assign a reachable IP or restore an unplugged link.

P47 offline research image: 16,268,276 bytes, SHA256 `99261cb46b8b8120054c4d865c795c0b47c964ead1e14bb88c1a866df6e811f4`.

Patched only:
- `V2000\\alice.htm` and `V2000\\DOC\\alice_ai.htm`: provide direct button to existing Gateway .2.210, replace dead .145 status/URL and display truthful reachability.
- `V2000\\JS\\alice_app.js`: gateway default and error messages no longer assume .145.

Offline QA: unchanged RTOS BIN, 1,312/1,312 PFS resources verified with only three authorized modifications, known BIN/WEB checksums and MD5 valid, 8/8 local tests pass, JavaScript syntax passes Node.js.

Optional Linux P46 proxy configuration tweak permits specifically `Origin: http://192.168.4.1` with OPTIONS 204, retaining the Nginx host allowlist and refusal for external origins; simulated Nginx integration test returned 204 for .4.1 and 403 for untrusted origin. Users must deploy that tweak separately (it is not in firmware). LAN routing between .4.x and .2.x remains a prerequisite.

**This is not a flash-verified firmware**; no real-device boot/update acceptance or .4.210 LAN path is proved. Preserve the known-working P44 and recovery plan. The private firmware and editable source bundle are supplied to the user in the conversation; no copyrighted user ROM is committed to the public repo.
