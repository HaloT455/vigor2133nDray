#include "../src/alice_rt_platform.h"
#include <assert.h>
#include <stdio.h>
#define IP(a,b,c,d) (((ag_u32)(a)<<24)|((ag_u32)(b)<<16)|((ag_u32)(c)<<8)|(ag_u32)(d))
struct mock{unsigned caps;int apply,verify,revert,writes,restores;};
static unsigned caps(void*v){return ((struct mock*)v)->caps;}
static int block(void*v,ag_u32 ip,ag_u32 ttl){struct mock*m=v;assert(ip==IP(8,8,8,8)&&ttl==300);m->writes++;return m->apply;}
static int blocked(void*v,ag_u32 ip,ag_u32 ttl){(void)ip;(void)ttl;return ((struct mock*)v)->verify;}
static int undo(void*v,ag_u32 ip){struct mock*m=v;(void)ip;m->restores++;return m->revert;}
static int qos(void*v,const struct ag_qos *r,unsigned n){struct mock*m=v;assert(n==1&&r[0].applied==0);m->writes++;return m->apply;}
static int qos_check(void*v,const struct ag_qos*r,unsigned n){(void)r;(void)n;return ((struct mock*)v)->verify;}
static int qos_revert(void*v){struct mock*m=v;m->restores++;return m->revert;}
int main(void){
 struct mock m={0,1,1,1,0,0};struct ar_state s;struct ar_outcome out;struct ag_decision d={0};
 struct ar_ops ops={0};unsigned common=AR_C_CAP_REQUIRED_COMMON;
 ops.ctx=&m;ops.capability_mask=caps;
 ops.deny_wan_ip_timed=block;ops.verify_wan_block=blocked;ops.revert_wan_block=undo;
 ops.apply_device_caps=qos;ops.verify_device_caps=qos_check;ops.revert_device_caps=qos_revert;
 ar_init(&s,ops);ar_protect_default_addresses(&s);
 d.action=AG_ALERT_EXTERNAL;d.trusted_input=1;d.source_ip=IP(8,8,8,8);d.proposed_ttl_sec=300;
 assert(!ar_run_decision(&s,&d,&out)&&out.blocked_by_safety&&m.writes==0);
 assert(!ar_bind_proved_abi(&s,common|AR_C_FIREWALL));
 m.caps=common|AR_C_FIREWALL;assert(ar_bind_proved_abi(&s,m.caps));
 assert(ar_run_decision(&s,&d,&out)&&out.applied&&out.verified&&m.writes==1);
 m.verify=0;assert(!ar_run_decision(&s,&d,&out)&&out.reverted&&m.restores==1);
 m.revert=0;assert(!ar_run_decision(&s,&d,&out)&&out.locked);
 assert(!ar_run_decision(&s,&d,&out)&&out.blocked_by_safety);
 ar_init(&s,ops);ar_protect_default_addresses(&s);m.writes=0;m.restores=0;m.revert=1;m.verify=1;
 assert(!ar_run_decision(&s,&d,&out)&&m.writes==0);
 m.caps=common|AR_C_QOS;assert(ar_bind_proved_abi(&s,m.caps));
 assert(!ar_commit_qos(&s,220,&out)&&out.blocked_by_safety);
 assert(ag_set_measured_wan(&s.engine,100000,30000,200));
 assert(ag_observe_device(&s.engine,IP(192,168,4,20),1000,100,AG_NORMAL,210,&d));
 assert(ar_commit_qos(&s,215,&out)&&out.applied&&out.verified);
 assert(!ar_commit_qos(&s,500,&out)&&out.blocked_by_safety);
 puts("P60 host simulator: PASS");return 0;
}
