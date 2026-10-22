# ALICE P60 — router-only native integration prototype

**Target:** DrayTek Vigor2133n, stand-alone — NO laptop, Nginx, Python, or browser is required by the *intended* deployed native runtime. **The intended runtime has NOT been deployed.**

## Completed in P60

1. Freestanding C11 P59 Guardian core: authentication-failure detection, suspicious source alerts, 2-source suspicious-client advisory, per-device moving-average baseline, weighted QoS recommendations from measured WAN.
2. New verified-platform **contract** `src/alice_rt_platform.{h,c}`:
   - No writes until authenticated event provenance, device firmware loader, firewall/QoS capabilities, readback, rollback, and boot-recovery proof are supplied by a model-matched OEM driver.
   - Timed external firewall deny and LAN client isolation with verification and automatic rollback on mismatch.
   - QoS application only with fresh real measurements and readback.
   - Fails closed and locks further application after failed rollback; protects the user's known management IPs.
3. Two C host test suites using mock OEM callbacks and MIPS32r2 big-endian relocatable build. This verifies algorithm, not on-device compatibility.
4. Private P58 ROM inspection: 4 `DLM/1.0` entries including `usr32alice.dlm` (**4,196 bytes**) and `usr32appe.dlm` (**154,180 bytes**). The Alice entry's 64-byte-header remainder is opaque/high entropy, without ELF header and with **unknown loader ABI**. Existence of a named module is not proof the RTOS will load a new arbitrary ELF object. Audit output is included in the attached source ZIP.

### Unmet blocking integration gates

- **RTOS loader/ABI** and suitable entry point to register a resident periodic task.
- Verified/authenticated native interfaces to read real CPU/RAM, per-device WAN rates, firewall state and write/revert IP Filter/DoS, Smart Bandwidth Limit, switch VLAN/client isolation.
- Flash partition map, hardware-specific boot/recovery, watchdog, model-matched firmware security upgrade.
- Verified third-party Mesh/Deco management interfaces. DrayTek central AP management does not automatically control Deco.
- Optional 24/7 locally resident autonomous threat detector needs actual trusted inputs; simple rule-based C is not a generative LLM.

**No new router-flashable P60 `.all` was created**, because link/load/boot validation is missing. P58's GUI-only image does not become a resident AI merely by appending the compiled object to WEB/PFS or to an opaque DLM body. This is an engineering bridge, not full completion of whole-home autonomous defense.

### Offline build

```bash
make test mips-object
python3 tools/audit_router_dlm.py --firmware /private/exact-P58.all --out build/dlm_audit.json
```

The auditor hash-pins the exact private P58 baseline SHA256 `6a2c9fbd3c18702dbf887c002689a48b41cd53a9ecc4bcd3c9c6199a1dc03807`. Do not publish private DLM blob bytes. The public repo includes source and synthetic tests, not proprietary firmware.

### What can run on the physical modem 24/7 NOW

The original DrayOS includes built-in DoS Defense, brute-force protection, IP Filter, VLAN and Smart Bandwidth Limit. Those need to be **enabled and validated in OEM settings**; P60 does not silently toggle them. The Vigor2133 series user guide documents `dos -V` (view) and `dos -A` (enable), plus native UI Firewall > DoS Defense. Use LAN management only and back up router settings before changes.

**Security:** The user's original 3.9.7-lineage RTOS binary does not incorporate later DrayTek vulnerability patches. Use region/variant-correct official patched firmware when hardware-compatible; custom WEB/PFS is not a security update.

CI builds **non-flashable MIPS ELF objects only**, not a valid DrayOS DLM nor a signed firmware.
