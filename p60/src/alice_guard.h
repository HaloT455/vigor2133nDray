#ifndef ALICE_GUARD_H
#define ALICE_GUARD_H
/* Portable, freestanding C policy core for a future DrayOS integration.
 * No networking, hardware control, RTOS hooks, filesystem, or code execution.
 * Build against a *verified* vendor SDK before any on-router use.
 */
typedef unsigned int ag_u32;
typedef unsigned short ag_u16;
typedef unsigned char ag_u8;
#if defined(__STDC_VERSION__) && __STDC_VERSION__ >= 201112L
_Static_assert(sizeof(ag_u32)==4,"requires 32-bit unsigned int");
#endif
#define AG_MAX_DEVICES 64u
#define AG_MAX_SOURCES 32u
#define AG_MAX_PROTECTED 16u
#define AG_TTL_SECONDS 300u
#define AG_WINDOW_SECONDS 300u
#define AG_MAX_WAN_KBPS 10000000u
#define AG_MAX_RATE_KBPS 10000000u

enum ag_class {AG_IOT=0,AG_BULK=1,AG_NORMAL=2,AG_INTERACTIVE=3};
enum ag_event {AG_FAILED_LOGIN=1,AG_WAN_SCAN=2,AG_IDS_LATERAL=3,AG_DNS_MALWARE=4};
enum ag_action {AG_NONE=0,AG_ALERT_EXTERNAL=1,AG_ALERT_DEVICE=2,AG_SUGGEST_QUARANTINE=3};
struct ag_device {
 ag_u32 ip; /* ipv4 in host order, e.g. 0xc0a80414 */
 ag_u32 observed_down_kbps,observed_up_kbps;
 ag_u32 ema_kbps,last_sample_sec;
 ag_u16 samples;
 ag_u8 traffic_class,bursts,ids_seen,dns_seen;
 ag_u32 ids_time,dns_time;
};
struct ag_source {ag_u32 ip,window_started_sec,last_event_sec;ag_u8 count;};
struct ag_engine {
 struct ag_device devices[AG_MAX_DEVICES];
 struct ag_source sources[AG_MAX_SOURCES];
 ag_u32 protected_ips[AG_MAX_PROTECTED];
 ag_u32 wan_down_kbps,wan_up_kbps,wan_measured_sec;
 ag_u8 measured_wan,protected_count;
};
struct ag_decision {
 enum ag_action action;
 ag_u32 source_ip;
 ag_u32 proposed_ttl_sec;
 ag_u8 trusted_input;
 ag_u8 applied; /* always 0: no SDK implementation */
};
struct ag_qos {
 ag_u32 ip,down_cap_kbps,up_cap_kbps;
 ag_u8 ready,applied; /* no OEM QoS writer */
};
void ag_init(struct ag_engine *e);
int ag_protect(struct ag_engine *e,ag_u32 ip);
int ag_is_public(ag_u32 ip);
int ag_is_private(ag_u32 ip);
int ag_set_measured_wan(struct ag_engine *e,ag_u32 down,ag_u32 up,ag_u32 now);
int ag_observe_device(struct ag_engine *e,ag_u32 ip,ag_u32 down,ag_u32 up,enum ag_class cls,ag_u32 now,struct ag_decision *out);
int ag_event(struct ag_engine *e,ag_u32 ip,enum ag_event kind,ag_u32 now,ag_u8 authenticated_source,ag_u8 approved_quarantine,struct ag_decision *out);
unsigned ag_qos_plan(const struct ag_engine *e,ag_u32 now,struct ag_qos *out,unsigned max_rows);
#endif
