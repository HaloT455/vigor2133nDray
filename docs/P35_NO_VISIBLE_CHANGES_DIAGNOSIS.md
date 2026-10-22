# P35: Why P34 booted without visible ALICE changes

**Root cause confirmed on user supplied ROM bytes.** P34 retained the exact legacy HTML script references (`../js/alice_local.js?v=253`, `../js/alice_app.js?v=253`, etc.) while the model code had been updated in the PFS `V2000/JS` resources. The visible login pages were unchanged by P34, so they still rendered the older unstyled OEM login when external CSS/JS did not load.

## Corrective experiment

The offline P35 patch starts with the specific private P34 SHA256 `1f63d47053f79ab64c3c9895a30b732ac0e5d12bd19b65fa18d675abf119c14d`. The resulting experimental P35 image is **15,866,820 bytes**, SHA256 `6d3933970ce778eae7ac7b9fd315fda3ff0c948f7033063351b628538da34f9d`.

Six WEB/PFS HTML resources changed:
- `V2000/alice.htm` and `V2000/DOC/alice_ai.htm`: replace all 5 JS references with case-correct `/JS/*.js?v=350`, change CSS query versions, add visible P35 marker and button invoking `ALICE_BRAIN.reply` directly. No modem configuration actions are added.
- `V2000/WEBLOGIN.HTM`, `V2000/LOGIN.HTM`, `V2000/weblogin1.htm`, `V2000/weblogin1.HTM`: add inline wine/maroon login CSS with centered existing GHQ Halo logo, fix JS reference, leave native DrayOS auth logic and CGI/SSI intact.

The **P34 model weights, `alice_local.js`, `alice_app.js` and BIN executable bytes are unmodified**. Independent offline checks: 1,312/1,312 resource equivalence with six authorized changes; BIN/WEB checksums and tail MD5 correct; 6/6 new Python tests passed; Node.js parses model/app JS and classifies a Wi-Fi query correctly. **These checks do not certify flash acceptance or successful operation on the actual router.**

### Critical live diagnosis before repeated flashing

On the router's Chrome browser after login, open `http://192.168.4.1/alice.htm?alice_probe=350` with Ctrl+Shift+R and inspect Network responses. The page must contain `alice-p35-banner`; `/JS/alice_local.js?v=350` should load actual JavaScript, not return an HTML login page. If the marker is absent, the device is still serving old HTML (persistent cache, web partition not switched, CGI template, or unexpected firmware update behavior).

The address `192.168.4.145` is an external AI gateway address **only when a separate LAN host is configured**; changing HTML and embedding browser inference does not assign or expose that IP.

**DO NOT FLASH the P35 experimental image without a known-good backup and verified recovery method.** Nothing in this repository validates physical boot.
