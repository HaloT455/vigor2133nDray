# P31 — Port completion gates and verified progress

The attached firmware is proprietary compiled DrayOS. Reverse engineering has recovered its BIN/WEB container and RTOS/DLM/PFS asset boundaries, not original C source.

### Static analysis on private P25 extract (SHA256 6018940fd0b28e905504db13e01d4b979bd0c03eda5241be8cf005912f8de612)

- Full 19,001,596-byte RTOS scanned: 19,711 heuristic stack-frame prologues; 51,832 jr-ra opcode words; 215,339 JAL-pattern words; 117 prologue sites with JAL low-28-bit references. This includes false positives, NOT proven function counts.
- All four DLM files pass size/version/sentinel checks; their real relocation ABI is still unknown.
- A target-neutral C HAL skeleton can be host-tested and cross-compiled to ELF32 MIPS32r2 big-endian relocatable machine code. It is not an RTOS/kernel, switch driver, flash driver or bootable image.
- P29 offline WEB/PFS repack, checksum BIN+WEB and footer MD5 validation are done; actual altered firmware has NOT been tested on a device.

### Completion evidence requirements

| Milestone | State | What is missing |
|---|---|---|
| Full DrayOS-equivalent source | NOT DONE | Independently written/legitimately obtained and equivalence-tested RTOS source |
| Actual BSP/ABI and drivers | NOT DONE | Board revision, SoC, RAM/flash map, switch/PHY and wireless IDs/calibration, validated driver binding |
| Bootable target firmware | NOT DONE | Target-specific link map, build, bootloader compatibility and safe rollback |
| Physical boot | NOT DONE | Serial boot, wired/wireless connectivity and recovery proven on exact target |

Do not label these as complete because Python CI or synthetic tests are green. Do not flash experimental binaries.

### Next data needed for physical port

Private, redacted serial boot transcript and chipset/PCB/flash identification for the intended destination router. Back up Wi-Fi calibration and MAC/NVRAM separately. Never upload router credentials or proprietary binary extracts to public GitHub.
