#include "../src/alice_guard.h"
#include <assert.h>
#include <stdio.h>
#define IP(a,b,c,d) (((ag_u32)(a)<<24)|((ag_u32)(b)<<16)|((ag_u32)(c)<<8)|(ag_u32)(d))
int main(void){
 struct ag_engine e;struct ag_decision d;struct ag_qos qos[3];unsigned i,n;
 ag_init(&e);assert(e.measured_wan==0);
 assert(!ag_is_public(IP(192,168,4,1)));
 assert(!ag_is_public(IP(100,64,0,1)));
 assert(!ag_is_public(IP(203,0,113,11)));
 assert(ag_is_public(IP(8,8,8,8)));
 assert(ag_is_private(IP(192,168,4,42)));
 assert(ag_protect(&e,IP(192,168,4,1)));
 assert(!ag_observe_device(&e,IP(192,168,4,1),100,100,AG_NORMAL,10,&d));
 assert(!ag_event(&e,IP(192,168,4,1),AG_FAILED_LOGIN,100,1,0,&d));
 assert(!ag_event(&e,IP(8,8,8,8),AG_FAILED_LOGIN,100,0,0,&d));
 for(i=0;i<7;i++){assert(ag_event(&e,IP(8,8,8,8),AG_FAILED_LOGIN,100+i,1,0,&d));assert(d.action==AG_NONE);}
 assert(ag_event(&e,IP(8,8,8,8),AG_FAILED_LOGIN,108,1,0,&d));
 assert(d.action==AG_ALERT_EXTERNAL && d.proposed_ttl_sec==300 && d.applied==0);
 assert(!ag_event(&e,IP(192,168,4,42),AG_IDS_LATERAL,100,1,0,&d));
 assert(ag_event(&e,IP(192,168,4,42),AG_IDS_LATERAL,150,1,1,&d));
 assert(d.action==AG_NONE);
 assert(ag_event(&e,IP(192,168,4,42),AG_DNS_MALWARE,170,1,1,&d));
 assert(d.action==AG_SUGGEST_QUARANTINE && d.applied==0);
 assert(!ag_qos_plan(&e,200,qos,3)); /* no WAN measured */
 assert(ag_set_measured_wan(&e,100000,20000,200));
 for(i=0;i<5;i++){
  assert(ag_observe_device(&e,IP(192,168,4,42),300,30,AG_INTERACTIVE,210+i,&d));
  assert(ag_observe_device(&e,IP(192,168,4,43),300,30,AG_BULK,210+i,&d));
 }
 n=ag_qos_plan(&e,214,qos,3);assert(n==2);
 assert(qos[0].applied==0 && qos[1].applied==0);
 assert(qos[0].down_cap_kbps>qos[1].down_cap_kbps);
 assert(qos[0].down_cap_kbps+qos[1].down_cap_kbps<=85000);
 assert(!ag_qos_plan(&e,2000,qos,3)); /* stale data rejected */
 assert(!ag_observe_device(&e,IP(192,168,4,44),0xffffffffu,0,AG_NORMAL,220,&d));
 printf("P59 C policy host tests: PASS\n");return 0;
}
