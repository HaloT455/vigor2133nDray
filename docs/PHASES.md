# ALICE Vigor2133n roadmap

## Completed

- [x] Immutable P25 baseline: size, SHA256, header/version candidate.
- [x] Separate `baseline/v2133n-p25-3.9.7` and `work/v2133n-fixes` branches.
- [x] Read-only audit, binary diff and hash-guarded experimental patch script.
- [x] P26 limited MIPS big-endian decoder at `0x100`.
- [x] CRC and compressed/uncompressed size-validated embedded resource index.
- [x] Offline regression tests using synthetic firmware fixtures.

## Research pending

- [ ] Identify correct hardware model/revision and serial boot messages.
- [ ] Acquire proper supported vendor 3.9.9.6 release image (do not blindly switch regional versions).
- [ ] Identify header checksum/signature/firmware container map and verify image slicing.
- [ ] Examine loaded code and UI resource dependencies for login/VLAN/mesh with device logs.
- [ ] Define minimal reproducible bug(s), expected behavior and rollback.
- [ ] Independent roundtrip integrity test before even considering device flash.

**No generated firmware is flash verified.** Development artifacts and tools do not make vendor ROM open source.
