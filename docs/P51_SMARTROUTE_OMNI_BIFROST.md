# P51 SmartRoute — OmniRoute/Bifrost-inspired network AI gateway

**Built on 2026-10-22.** This phase ports routing *patterns*, not the upstream Go/Node services or their trained model weights into DrayOS.

Upstream design references: https://github.com/cheaper-inference/OmniRoute and https://github.com/maximhq/bifrost

P51 source bundle delivered to user includes:
- `gateway/smart_route.py`: 100% standard-library Python OpenAI-compatible multi-provider request router, provider priority, bounded retries/failover, timeout, 2-error circuit breaker, per-hour upstream call quota, no secret exposure in status API.
- `gateway/alice_gateway.py`: existing authenticated telemetry/chat service with SmartRoute first, existing localhost llama.cpp next, and offline network rules last. No DrayOS config writes.
- `gateway/upgrade_p51.sh`: backup, software upgrade, restart, health verification and restore on failure; a disabled provider config example is installed on X270.
- `firmware/build_p51.py`: WEB/PFS-only P50->P51 ROM experiment, updates 2 ALICE HTML resources, keeps original BIN and all other resources.
- Offline tests: 7/7 synthetic network/request cases passed; integrated HTTP health, routes and chat were exercised locally.

Baseline private P50 SHA256: `3c3baa53d88c1253567277ce186cc703893d136f83b7ba87dee4b6cb391bfd22`.

Offline-built P51 ROM: **16,273,420 bytes** (below requested 27 MB); SHA256 `717addfa8655055efe3d9df03cd6e69f1c2ea894642b470de00f66cd4f9a8f24`. All **1,312/1,312** decoded PFS resources checked, original RTOS BIN identical, known BIN/WEB and MD5 validations pass.

**The firmware is NOT BOOT/FLASH VERIFIED.** CI and offline validation do not make the image safe for Vigor2133n bootloader. The Linux gateway upgrade can be applied separately and does not require flashing.

**No actual Bifrost, OmniRoute, provider API keys or LLM model binaries were shipped.** Provider URLs in the example are placeholders on local loopback. The service will continue returning the existing Offline network guidance until the operator starts and configures a compatible upstream. Route provider keys and remote network telemetry must never be embedded in router UI/ROM. Router hardware QoS adaptation, DNS DHCP configuration, subnet 192.168.4.210 and live WAN metrics remain unverified/not implemented.

The private P51 .all and reproducible Gateway/source ZIP are conversation attachments. Do not commit the private proprietary firmware to this public repo.
