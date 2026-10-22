#ifndef ALICE_HAL_H
#define ALICE_HAL_H
/* Platform contract ONLY. Not a physical device driver or recovered DrayOS code. */
typedef unsigned int alice_u32;
#if defined(__STDC_VERSION__) && __STDC_VERSION__ >= 201112L
_Static_assert(sizeof(alice_u32)==4,"32-bit unsigned int required");
#endif
enum alice_probe_flags {
 ALICE_BOARD_REV_CONFIRMED=1u<<0, ALICE_SOC_ID_CONFIRMED=1u<<1,
 ALICE_MEMORY_MAP_CONFIRMED=1u<<2, ALICE_FLASH_LAYOUT_CONFIRMED=1u<<3,
 ALICE_SWITCH_PHY_CONFIRMED=1u<<4, ALICE_WIFI_CALIB_BACKED_UP=1u<<5
};
struct alice_board_proof {
 alice_u32 board_revision,soc_id,flash_bytes,ram_bytes,evidence_flags;
};
int alice_hal_board_preflight(const struct alice_board_proof *board);
alice_u32 alice_hal_abi_probe(alice_u32 x);
#endif
