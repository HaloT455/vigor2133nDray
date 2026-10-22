/* P32 architecture/link diagnostic ONLY. NO MMIO; NOT A BOOTABLE DEVICE FIRMWARE. */
#include "alice_hal.h"
volatile int alice_diagnostic_result = -127;
void alice_diagnostic_entry(void) {
    struct alice_board_proof absent = {0};
    int result = alice_hal_board_preflight(&absent);
    alice_diagnostic_result = (result == -2 &&
       alice_hal_abi_probe(7) == (14u ^ 0x12345678u)) ? 0 : -1;
    /* A controlled, inert loop. There is no UART, bootloader, or board support. */
    for (;;) { __asm__ volatile ("nop"); }
}
