#include "alice_rt_platform.h"
static void clear(void *v,unsigned n){unsigned char *p=(unsigned char *)v;while(n--)*p++=0;}
void ar_init(struct ar_state *s,struct ar_ops ops){if(!s)return;clear(s,sizeof(*s));ag_init(&s->engine);s->ops=ops;}
void ar_protect_default_addresses(struct ar_state *s){if(!s)return;
 (void)ag_protect(&s->engine,0xc0a80401u);
 (void)ag_protect(&s->engine,0xc0a80201u);
 (void)ag_protect(&s->engine,0xc0a802d2u);
 (void)ag_protect(&s->engine,0xc0a80491u);
 (void)ag_protect(&s->engine,0xc0a804d2u);
}
int ar_bind_proved_abi(struct ar_state *s,unsigned proofs){
 unsigned actual;
 if(!s||!s->ops.capability_mask)return 0;
 actual=s->ops.capability_mask(s->ops.ctx);
 if(proofs!=actual||(proofs&AR_C_CAP_REQUIRED_COMMON)!=AR_C_CAP_REQUIRED_COMMON)return 0;
 s->required_proofs=proofs;return 1;
}
static int is_protected(const struct ar_state *s,ag_u32 ip){
 unsigned i;for(i=0;i<s->engine.protected_count;i++)if(s->engine.protected_ips[i]==ip)return 1;
 return 0;
}
static int ready(struct ar_state *s,unsigned feat){
 if(!s||s->locks||!s->ops.capability_mask)return 0;
 if((s->required_proofs&(AR_C_CAP_REQUIRED_COMMON|feat))!=(AR_C_CAP_REQUIRED_COMMON|feat))return 0;
 return s->ops.capability_mask(s->ops.ctx)==s->required_proofs;
}
static int guarded_write(struct ar_state *s,ag_u32 ip,ag_u32 ttl,int is_lan,struct ar_outcome *o){
 int r,verified;
 int (*apply)(void*,ag_u32,ag_u32)=is_lan?s->ops.isolate_lan_ip_timed:s->ops.deny_wan_ip_timed;
 int (*undo)(void*,ag_u32)=is_lan?s->ops.revert_lan_isolation:s->ops.revert_wan_block;
 if(!apply||!undo)return 0;
 if(is_lan){if(!s->ops.verify_lan_isolation)return 0;}
 else {if(!s->ops.verify_wan_block)return 0;}
 r=apply(s->ops.ctx,ip,ttl);
 if(r!=1)return 0;
 verified=is_lan?s->ops.verify_lan_isolation(s->ops.ctx,ip):s->ops.verify_wan_block(s->ops.ctx,ip,ttl);
 if(verified==1){o->applied=1;o->verified=1;
  if(is_lan)s->applied_isolations++;else s->applied_blocks++;
  return 1;
 }
 if(undo(s->ops.ctx,ip)==1){o->reverted=1;return 0;}
 s->locks|=1;o->locked=1;return 0;
}
int ar_run_decision(struct ar_state *s,const struct ag_decision *d,struct ar_outcome *o){
 if(!o)return 0;
 clear(o,sizeof(*o));
 if(!s||!d||is_protected(s,d->source_ip)||d->applied||d->trusted_input!=1||d->proposed_ttl_sec!=AG_TTL_SECONDS){
  o->blocked_by_safety=1;return 0;
 }
 switch(d->action){
 case AG_ALERT_EXTERNAL:
  if(!ag_is_public(d->source_ip)||!ready(s,AR_C_FIREWALL)){o->blocked_by_safety=1;return 0;}
  break;
 case AG_SUGGEST_QUARANTINE:
  if(!ag_is_private(d->source_ip)||!ready(s,AR_C_QUARANTINE)){o->blocked_by_safety=1;return 0;}
  break;
 default:o->blocked_by_safety=1;return 0;
 }
 return guarded_write(s,d->source_ip,d->proposed_ttl_sec,d->action==AG_SUGGEST_QUARANTINE,o);
}
int ar_commit_qos(struct ar_state *s,ag_u32 now,struct ar_outcome *o){
 struct ag_qos caps[AG_MAX_DEVICES];unsigned count;int checked;
 if(!o)return 0;
 clear(o,sizeof(*o));
 if(!ready(s,AR_C_QOS)||!s->ops.apply_device_caps||!s->ops.verify_device_caps||!s->ops.revert_device_caps){
  o->blocked_by_safety=1;return 0;
 }
 count=ag_qos_plan(&s->engine,now,caps,AG_MAX_DEVICES);
 if(!count){o->blocked_by_safety=1;return 0;}
 if(s->ops.apply_device_caps(s->ops.ctx,caps,count)!=1)return 0;
 checked=s->ops.verify_device_caps(s->ops.ctx,caps,count);
 if(checked==1){o->applied=1;o->verified=1;s->applied_qos_batches++;return 1;}
 if(s->ops.revert_device_caps(s->ops.ctx)==1){o->reverted=1;return 0;}
 s->locks|=1;o->locked=1;return 0;
}
