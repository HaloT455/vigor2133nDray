# P59 Native Standalone Policy Core — MIPS32r2

**Goal:** build independently resident on the **Vigor2133n DrayOS RTOS**, without ThinkPad X270, web browser or cloud model.

**What was actually built:** from the preserved P58 baseline, a freestanding C11 **policy object** targeting MIPS32r2 big-endian: `ELF32 MSB MIPS32r2 relocatable`, 5,124 bytes, SHA256 `006ca8b3ab7d1828d8360e7e879de6de6d14070f41d1d9a1e39807dfb0a42788`. Host tests passed. The independently authored source archive is delivered in the conversation as `ALICE_P59_NATIVE_ENGINE_SOURCE_TESTS.zip` (includes `src/alice_guard.{h,c}`, unit tests, Makefile and compile proof).

It performs **read-only safety decisions**: protects management addresses from external blocks, validates trusted-source events for repeated login failures, flags suspicious rates after 5+ samples using an exponential moving average, proposes 300-second quarantine only after two distinct fresh trusted signals and operator policy consent, and computes an 85%-of-measured-WAN weighted rate plan. **Every output has applied=false.**

## Not integrated / no new .all

There is **no verified RTOS module loader ABI, scheduler callback, OEM QoS/firewall driver entry point, network statistics API, native device port/MAC isolation interface, watchdog/rollback, or router flash/boot test.** P58's WEB/PFS-only patch cannot load this relocatable object as a resident daemon. Therefore **no new flashable 'full AI P59 .all' is advertised**. This is not fully functional hardware-side automation. The user explicitly excludes a laptop, so X270 sidecar is not a valid substitute.

Official router-native facilities do work 24/7 if correctly configured: Firewall DoS Defense, Management Brute Force Protection, Smart Bandwidth Limit / Auto Adjustment, bandwidth/session limits and VLAN+IP Filter. Use those to protect the network pending actual RTOS integration.

Vendor reference: https://draytek.com/support/knowledge-base/how-to-use-bandwidth-limit and https://www.draytek.com/products/vigor2133/ . Hardware/region-matched official 3.9.9.6 is listed at https://www.draytek.com.au/support/downloads/vigor2133-series/ ; **the preserved 3.9.7-lineage BIN is not security-upgraded by P58**.

For an actual router-only release the required evidence is (1) exact board/flash partition map and full backup + UART recovery, (2) confirmed supported firmware executable/module loader ABI, (3) OEM API ability to read/write firewall and QoS and revert changes, (4) live authenticated per-client measurements, (5) independent full physical boot/WAN/LAN/Wi-Fi verification. Do not infer these gates from GUI screenshots or a passing offline checksum.
