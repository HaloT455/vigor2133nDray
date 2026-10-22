#include "alice_guard.h"

static void zero(void *p,unsigned n){ag_u8 *b=(ag_u8*)p;while(n--)*b++=0;}
static ag_u32 min_u32(ag_u32 a,ag_u32 b){return a<b?a:b;}
static ag_u8 first(ag_u32 ip){return (ag_u8)(ip>>24);}
static ag_u8 second(ag_u32 ip){return (ag_u8)(ip>>16);}
static ag_u8 third(ag_u32 ip){return (ag_u8)(ip>>8);}
static int age_ok(ag_u32 now,ag_u32 before,ag_u32 limit){return before!=0 && now>=before && now-before<=limit;}
static int globally_forbidden(ag_u32 a){
 ag_u8 f=first(a),s=second(a),t=third(a);
 if(f==0||f==10||f==127||f>=224)return 1;
 if(f==100&&s>=64&&s<=127)return 1; /* carrier-grade NAT */
 if(f==169&&s==254)return 1;
 if(f==172&&s>=16&&s<=31)return 1;
 if(f==192&&(s==168||s==0||(s==88&&t==99)))return 1;
 if(f==198&&(s==18||s==19||(s==51&&t==100)))return 1;
 if(f==192&&s==0&&t==2)return 1;
 if(f==203&&s==0&&t==113)return 1;
 return 0;
}
int ag_is_public(ag_u32 ip){return !globally_forbidden(ip);}
int ag_is_private(ag_u32 ip){
 ag_u8 f=first(ip),s=second(ip);
 return (f==10)||(f==172&&s>=16&&s<=31)||(f==192&&s==168);
}
void ag_init(struct ag_engine *e){if(e)zero(e,sizeof(*e));}
int ag_protect(struct ag_engine *e,ag_u32 ip){
 unsigned i;if(!e||e->protected_count>=AG_MAX_PROTECTED)return 0;
 for(i=0;i<e->protected_count;i++)if(e->protected_ips[i]==ip)return 1;
 e->protected_ips[e->protected_count++]=ip;return 1;
}
static int protected_ip(const struct ag_engine *e,ag_u32 ip){
 unsigned i;for(i=0;i<e->protected_count;i++)if(e->protected_ips[i]==ip)return 1;
 return 0;
}
static void decision(struct ag_decision *d,enum ag_action type,ag_u32 ip,ag_u32 ttl){
 d->action=type;d->source_ip=ip;d->proposed_ttl_sec=ttl;d->applied=0;d->trusted_input=1;
}
int ag_set_measured_wan(struct ag_engine *e,ag_u32 down,ag_u32 up,ag_u32 now){
 if(!e||!down||!up||down>AG_MAX_WAN_KBPS||up>AG_MAX_WAN_KBPS||!now)return 0;
 e->wan_down_kbps=down;e->wan_up_kbps=up;e->wan_measured_sec=now;e->measured_wan=1;return 1;
}
static struct ag_device *device_slot(struct ag_engine *e,ag_u32 ip){
 unsigned i;struct ag_device *free_slot=0;
 for(i=0;i<AG_MAX_DEVICES;i++){
  if(e->devices[i].ip==ip)return &e->devices[i];
  if(!free_slot&&!e->devices[i].ip)free_slot=&e->devices[i];
 }
 if(free_slot){zero(free_slot,sizeof(*free_slot));free_slot->ip=ip;}
 return free_slot;
}
int ag_observe_device(struct ag_engine *e,ag_u32 ip,ag_u32 down,ag_u32 up,enum ag_class cls,ag_u32 now,struct ag_decision *out){
 struct ag_device *d;ag_u32 total;
 if(!out)return 0;
 zero(out,sizeof(*out));
 if(!e||!ag_is_private(ip)||protected_ip(e,ip)||cls>AG_INTERACTIVE||!now||
    down>AG_MAX_RATE_KBPS||up>AG_MAX_RATE_KBPS)return 0;
 d=device_slot(e,ip);if(!d)return 0;
 if(d->last_sample_sec&&now<=d->last_sample_sec)return 0;
 if(d->last_sample_sec&&now-d->last_sample_sec>300){d->samples=0;d->bursts=0;d->ema_kbps=0;}
 d->last_sample_sec=now;d->observed_down_kbps=down;d->observed_up_kbps=up;d->traffic_class=(ag_u8)cls;
 total=down+up;
 if(d->samples>=5 && total>1500 && total>d->ema_kbps*3u){
  if(d->bursts<3)d->bursts++;
 }else d->bursts=0;
 if(d->bursts==3){decision(out,AG_ALERT_DEVICE,ip,0);d->bursts=0;}
 if(d->samples==0)d->ema_kbps=total;
 else d->ema_kbps=(ag_u32)((d->ema_kbps*7u+total)/8u);
 if(d->samples<65535)d->samples++;
 return 1;
}
static struct ag_source *source_slot(struct ag_engine *e,ag_u32 ip){
 unsigned i;struct ag_source *spare=0;
 for(i=0;i<AG_MAX_SOURCES;i++){
  if(e->sources[i].ip==ip)return &e->sources[i];
  if(!spare&&!e->sources[i].ip)spare=&e->sources[i];
 }
 if(spare){zero(spare,sizeof(*spare));spare->ip=ip;}
 return spare;
}
int ag_event(struct ag_engine *e,ag_u32 ip,enum ag_event kind,ag_u32 now,ag_u8 authenticated_source,ag_u8 approved_quarantine,struct ag_decision *out){
 struct ag_source *s;struct ag_device *d;
 if(!out)return 0;
 zero(out,sizeof(*out));
 if(!e||!now||authenticated_source!=1||protected_ip(e,ip))return 0;
 if(kind==AG_FAILED_LOGIN||kind==AG_WAN_SCAN){
  if(!ag_is_public(ip))return 0;
  s=source_slot(e,ip);if(!s)return 0;
  if(!s->window_started_sec||now<s->window_started_sec||now-s->window_started_sec>AG_WINDOW_SECONDS){s->count=0;s->window_started_sec=now;}
  s->last_event_sec=now;if(s->count<255)s->count++;
  if(s->count>=8){decision(out,AG_ALERT_EXTERNAL,ip,AG_TTL_SECONDS);s->count=0;s->window_started_sec=now;}
  return 1;
 }
 if(kind!=AG_IDS_LATERAL&&kind!=AG_DNS_MALWARE)return 0;
 if(!ag_is_private(ip)||!approved_quarantine)return 0;
 d=device_slot(e,ip);if(!d)return 0;
 if(kind==AG_IDS_LATERAL){d->ids_seen=1;d->ids_time=now;}
 if(kind==AG_DNS_MALWARE){d->dns_seen=1;d->dns_time=now;}
 if(d->ids_seen&&d->dns_seen&&age_ok(now,d->ids_time,AG_WINDOW_SECONDS)&&age_ok(now,d->dns_time,AG_WINDOW_SECONDS)){
  decision(out,AG_SUGGEST_QUARANTINE,ip,AG_TTL_SECONDS);
  d->ids_seen=0;d->dns_seen=0;
 }
 return 1;
}
unsigned ag_qos_plan(const struct ag_engine *e,ag_u32 now,struct ag_qos *out,unsigned max_rows){
 unsigned i,count=0,denom=0;static const ag_u8 weights[4]={1,2,3,6};
 if(!e||!out||!max_rows||!e->measured_wan||!age_ok(now,e->wan_measured_sec,900))return 0;
 for(i=0;i<AG_MAX_DEVICES;i++)if(e->devices[i].ip&&!protected_ip(e,e->devices[i].ip)&&age_ok(now,e->devices[i].last_sample_sec,30)){
  denom+=weights[min_u32(e->devices[i].traffic_class,3)];
 }
 if(!denom)return 0;
 for(i=0;i<AG_MAX_DEVICES&&count<max_rows;i++){
  const struct ag_device *d=&e->devices[i];ag_u32 w;
  if(!d->ip||protected_ip(e,d->ip)||!age_ok(now,d->last_sample_sec,30))continue;
  w=weights[min_u32(d->traffic_class,3)];
  /* Numerically safe 32-bit split: denominator >= w; avoids __udivdi3
   and stays below 10,000,000*85 < UINT32_MAX at each step. */
  out[count].ip=d->ip;
  out[count].down_cap_kbps=((e->wan_down_kbps/denom)*w*85u)/100u +
    (((e->wan_down_kbps%denom)*w*85u)/(100u*denom));
  out[count].up_cap_kbps=((e->wan_up_kbps/denom)*w*85u)/100u +
    (((e->wan_up_kbps%denom)*w*85u)/(100u*denom));
  out[count].ready=1;out[count].applied=0;count++;
 }
 return count;
}
