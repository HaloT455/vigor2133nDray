#include <assert.h>
#include "alice_hal.h"
int main(void) {
 assert(alice_hal_board_preflight(0)==-1);
 struct alice_board_proof b={0};
 assert(alice_hal_board_preflight(&b)==-2);
 b.evidence_flags=0x3fu;
 assert(alice_hal_board_preflight(&b)==-3);
 b.soc_id=1;b.board_revision=1;b.ram_bytes=0x08000000u;b.flash_bytes=0x01000000u;
 assert(alice_hal_board_preflight(&b)==0);
 b.flash_bytes=123;
 assert(alice_hal_board_preflight(&b)==-4);
 assert(alice_hal_abi_probe(7)==(14u^0x12345678u));
 return 0;
}
