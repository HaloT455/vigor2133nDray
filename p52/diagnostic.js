/* P52 read-only source-aware dashboard. No DrayOS writes, fake counters or credentials. */
(function(w,d){'use strict';
var $=function(id){return d.getElementById(id);};
function label(id,value){var e=$(id);if(e)e.textContent=value;}
function n(v){var s=String(v===null||v===undefined?'':v).trim();return /^(?:100|\d\d?|\d\d?\.\d+)%?$/.test(s)?+s.replace('%',''):null;}
function updateRouter(){
 var cpu=$('stat-cpu'),ram=$('stat-memory'),src=$('connection'),updated=$('stat-updated');
 if(!cpu||!ram)return;
 var cv=n(cpu.textContent),rv=n(ram.textContent),status=src?src.textContent:'';
 label('alice-p52-router-source',cv===null&&rv===null?
 'DrayTek: CHƯA CÓ CPU/RAM thực. '+(status||'Cần kiểm tra CGI và phiên đăng nhập.'):
 'DrayTek (số liệu từ trang quản trị): CPU '+(cv===null?'chưa có':cv+'%')+' · RAM '+(rv===null?'chưa có':rv+'%')+' · cập nhật '+(updated?updated.textContent:'chưa rõ')+'.');
 var e=$('elastic-state'),bw4=$('bw4'),bw6=$('bw6'),smart=$('smart');
 label('alice-p52-qos-state','Cấu hình đã đọc: Giới hạn IPv4 '+(bw4?bw4.textContent:'chưa đọc')+', IPv6 '+(bw6?bw6.textContent:'chưa đọc')+', Smart Limit '+(smart?smart.textContent:'chưa đọc')+', Auto-Adjustment '+(e?e.textContent:'chưa đọc')+'. Đây KHÔNG PHẢI phép đo cân bằng băng thông.');
}
async function updateHost(){
 try{var ac=new AbortController(),t=setTimeout(function(){ac.abort();},4000);
 try{var r=await fetch('http://192.168.2.210/alice-api/usage',{cache:'no-store',credentials:'omit',signal:ac.signal});
 if(!r.ok)throw new Error('HTTP '+r.status);
 var x=await r.json(),h=x.host||{};
 if(h.source!=='X270_Linux_not_router')throw new Error('Không xác minh được nguồn dữ liệu');
 label('alice-p52-host-source','X270 (không phải router): CPU '+(h.cpu_percent==null?'chưa đủ mẫu':h.cpu_percent+'%')+', RAM '+(h.memory_percent==null?'không có':h.memory_percent+'%')+'. Thiết bị: '+(x.router&&x.router.available?'có dữ liệu do trình duyệt gửi':'chưa có Data Flow DrayTek')+'.');
 }finally{clearTimeout(t);}
 }catch(e){label('alice-p52-host-source','X270: chưa đọc được Gateway. '+(e.name==='AbortError'?'quá thời gian':e.message)+'. Mở trang ALICE Gateway riêng để kiểm tra.');}
}
function start(){
 updateRouter();updateHost();var b=$('alice-p52-refresh');if(b)b.onclick=function(){var native=$('refresh-stats'),cfg=$('read-config');if(native)native.click();if(cfg)cfg.click();updateHost();setTimeout(updateRouter,2500);};
 w.setInterval(updateRouter,5000);w.setInterval(updateHost,30000);
}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',start);else start();
}(window,document));