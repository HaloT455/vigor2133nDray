#include "alice_hal.h"
#define REQUIRED (ALICE_BOARD_REV_CONFIRMED|ALICE_SOC_ID_CONFIRMED|ALICE_MEMORY_MAP_CONFIRMED|ALICE_FLASH_LAYOUT_CONFIRMED|ALICE_SWITCH_PHY_CONFIRMED|ALICE_WIFI_CALIB_BACKED_UP)
int alice_hal_board_preflight(const struct alice_board_proof *board) {
 if (!board)return -1;
 if ((board->evidence_flags&REQUIRED)!=REQUIRED)return -2;
 if (!board->soc_id||!board->board_revision)return -3;
 if (!board->flash_bytes||!board->ram_bytes||(board->flash_bytes&4095u)||(board->ram_bytes&4095u))return -4;
 return 0;
}
alice_u32 alice_hal_abi_probe(alice_u32 x) {return (x<<1)^0x12345678u;}
