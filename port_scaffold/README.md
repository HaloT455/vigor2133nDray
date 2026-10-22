# Target-neutral HAL prototype (P31)

This is **newly written C**, not reconstructed DrayOS source. Host preflight tests and MIPS32r2 big-endian cross-compilation are verified locally.

```bash
make host-check
make mips-object
```

The output is a relocatable ELF32 MIPS object. **It is not a kernel, driver, executable image or flashable ROM.** All physical board MMIO locations, RAM size, flash partitions, NVRAM and Wi-Fi calibration depend on independently collected device information. Values in tests are fictitious examples only.
