#ifndef ALICE_RT_PLATFORM_H
#define ALICE_RT_PLATFORM_H
#include "alice_guard.h"
/* Platform contract: production must link authenticated OEM driver callbacks.
   No legitimate unverified DrayOS binding is assumed or shipped. */
#define AR_C_AUTH_EVENTS (1u<<0)
#define AR_C_FIREWALL (1u<<1)
#define AR_C_QUARANTINE (1u<<2)
#define AR_C_QOS (1u<<3)
#define AR_C_READBACK (1u<<4)
#define AR_C_ROLLBACK (1u<<5)
#define AR_C_BOOT_RECOVERY (1u<<6)
#define AR_C_RTOS_LOADER (1u<<7)
#define AR_C_CAP_REQUIRED_COMMON (AR_C_AUTH_EVENTS|AR_C_READBACK|AR_C_ROLLBACK|AR_C_BOOT_RECOVERY|AR_C_RTOS_LOADER)

struct ar_ops {
 void *ctx;
 unsigned (*capability_mask)(void *ctx);
 int (*deny_wan_ip_timed)(void *ctx,ag_u32 ip,ag_u32 ttl);
 int (*verify_wan_block)(void *ctx,ag_u32 ip,ag_u32 ttl);
 int (*revert_wan_block)(void *ctx,ag_u32 ip);
 int (*isolate_lan_ip_timed)(void *ctx,ag_u32 ip,ag_u32 ttl);
 int (*verify_lan_isolation)(void *ctx,ag_u32 ip);
 int (*revert_lan_isolation)(void *ctx,ag_u32 ip);
 int (*apply_device_caps)(void *ctx,const struct ag_qos *caps,unsigned count);
 int (*verify_device_caps)(void *ctx,const struct ag_qos *caps,unsigned count);
 int (*revert_device_caps)(void *ctx);
};
struct ar_state {
 struct ag_engine engine;struct ar_ops ops;
 unsigned required_proofs,locks,applied_blocks,applied_isolations,applied_qos_batches;
};
struct ar_outcome {int applied,verified,reverted,blocked_by_safety,locked;};
void ar_init(struct ar_state *s,struct ar_ops ops);
void ar_protect_default_addresses(struct ar_state *s);
int ar_bind_proved_abi(struct ar_state *s,unsigned proofs);
int ar_run_decision(struct ar_state *s,const struct ag_decision *d,struct ar_outcome *out);
int ar_commit_qos(struct ar_state *s,ag_u32 now,struct ar_outcome *out);
#endif
