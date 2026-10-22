# P41: Minimal rose GHQ Halo rebrand based on user-confirmed P25

**Source input (user's working baseline):** `ALICE_V2133n_P25_CHAT_FIX_P12_BASE_NOT_FLASH_VERIFIED(2).all`, SHA256 `4dbef87394b8bffa1b7900b74aca4eb7a6ac8a70a21bd8e15b69e94d`, **15,761,824 bytes**.

**Private experimental output:** `ALICE_V2133n_P41_P25_ROSE_GHQ_ALICE_RESEARCH_NOT_FLASH_VERIFIED.all`, SHA256 `b4a9f39894418a0258b2223d491799c8b8765517bb3c3bdf129f537ac889efa2`, **16,175,040 bytes**. Under the user-specified 27 MB upper bound.

## Change rationale

P39’s greatly enlarged WEB partition was followed by a user report of an unchanged OEM dashboard and a 404 response from `/alice.htm`. Rather than patching P39 or P40 again, P41 is rebuilt from the **specific P25 image the user confirms working**, with restrained payload growth. P41 uses existing PFS entry names and retains all original CGI and firmware BIN data.

- 14 static branding images including **`01.jpg`, `01f.jpg`, `02f.jpg`, `2133-1.png`**, OEM login images, `draytek.gif`, and favicon now contain the original GHQ Halo emblem with a rose-color theme.
- Original `V2000/IMAGES/halo.png` is unchanged; the exact logo is embedded into four login pages, both ALICE views and shared UI bootstrap to avoid uncertain request casing.
- Theme CSS appended in PFS; menu/header/login/ALICE HTML use restrained cache-busting.
- Unchanged full P25 `alice_app.js`, `alice_ctrl.js`, `alice_net.js`. The `alice_local.js` extension from P36 adds a 15-topic browser-only classifier, a standalone offline chat fallback and bounded read-only CPU/RAM learning in two ALICE pages.
- Original **authenticated link flow** opens `/doc/alice_ai.htm?sFormAuthStr=...`; a direct `/alice.htm` URL is not a reliable acceptance test if DrayOS does not route it.
- Original P25 BIN is **bit-for-bit unchanged**.

Offline checks: **1,312/1,312 PFS resources** match all expected content; BIN+WEB checksum and footer MD5 pass; 14 replaced images decode, 7 JS resources pass Node syntax checks; the appended model predicts Wi-Fi properly in a VM execution test. **No P41 router flash, live HTTP or boot validation has been performed.**

The complete reproducible source package and private output are handed to the user in the ChatGPT conversation; no proprietary firmware, extracted brand art or router secrets are committed publicly.

## Acceptance check

From a machine on the router LAN use the packaged read-only `verify_live_p41.sh` to compare the actual `/images/01.jpg` response hash. The P41 image SHA256 is `94303a9228e9d5159371e89cd26a95845073190f41b279e57817369d3f493c14`; old P25 header image SHA256 `edaec9b7689ba142893a7f35f70f4f88b4b65f4548970f200308e59b75cc6cb9`. A mismatch, redirect or unavailable image warrants additional inspection before any firmware update.

**NOT FLASH VERIFIED**. Do not label a firmware safe merely because known checksums and static tests pass. Back up the known-good device state and confirm recovery and flash partition compatibility before any actual update.
