# P36 — GHQ Halo logo and offline chat recovery

## Output identity and constraints

- Private P35 baseline SHA256: 6d3933970ce778eae7ac7b9fd315fda3ff0c948f7033063351b628538da34f9d
- Generated P36 image: **16,401,080 bytes**, under the **27,000,000-byte** limit.
- Output SHA256: 8dd06e2a7c95d6831b6105d9169d18effb778a1acf4f53a8b4ca2f4d71ed56e5
- WEB/PFS: **1,312/1,312 resources verified**, 6 HTML resources updated, original BIN unchanged.
- Known BIN+WEB additive checksums and DrayTekImageMD5 pass.
- Flash/physical boot of P36: **NOT VERIFIED**.

## User-observed faults

Screenshots show broken image loading in login and ALICE main panel, while the embedded offline model self-test succeeds and the full chat application never sets ALICE_BOOT_READY. This isolates a failed chat initialization but not the exact failing browser request or startup statement.

## Corrections in experimental P36

1. The unmodified original V2000/IMAGES/halo.png is embedded as a PNG data URI into 4 login and 2 ALICE pages to avoid asset-path/case/cache problems.
2. Keep wine-red GHQ Halo login design and native DrayOS authentication forms, CGI handlers and SSI fields.
3. Add a browser-only recovery handler, identical in function to [P36 offline fallback](../web/alice_p36_offline_fallback.js): if native app does not become ready, enable form submission, Enter, quick buttons, new-chat and ALICE_BRAIN.reply().
4. Keep uppercase /JS/ paths that loaded the offline model in observed P35, bump version to v=360.
5. Native router controls are not invoked by recovery. If native app is ready, recovery leaves it untouched.

## Checks

- Offline roundtrip PFS: all 1,312 resources agree with authorized changes.
- Models, controllers, network decoder, application and logo resource are unchanged at byte level.
- Five Python integration tests pass using P35 and P36; independent Node VM simulation sends a Wi-Fi message and verifies response, quick button, and native-bypass behavior.
- Public GitHub CI verifies synthetic JavaScript fallback and existing research tools. CI does NOT build proprietary P36 from the private P35 image in this public repository.

## Device validation

After a known-good recovery/backup is secured, open http://192.168.4.1/alice.htm?v=360 in an authenticated session and hard refresh. Check image, then send “Wi-Fi yếu cần làm gì?”. If native chat boot fails, window.ALICE_CHAT_MODE should show offline-fallback in the correct browser frame. The service at 192.168.4.145 is still external and NOT created by this firmware. The 15-intent model is not a ChatGPT-class LLM.

**Do not claim this experiment is flash/boot validated without actual hardware evidence.**
