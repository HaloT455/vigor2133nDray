/* ALICE P37 | local browser-only adaptive monitor. No DrayOS configuration writes. */
(function(win,doc){'use strict';
if(win.ALICE_ADAPTIVE)return;
var KEY='alice.p37.trends.v1',MAX=144,VERSION=1;
var state={version:VERSION,samples:[],topics:{},alerts:[],lastSeen:0},lastWarn={};
function $(id){return doc.getElementById(id);}
function number(v){var n=parseFloat(String(v||'').replace(',','.'));return isFinite(n)&&n>=0&&n<=100?n:null;}
function clamp(v,n){return String(v||'').slice(0,n||140);}
function median(values){if(!values.length)return null;var copy=values.slice().sort(function(a,b){return a-b;});return copy[Math.floor(copy.length/2)];}
function save(){try{win.localStorage.setItem(KEY,JSON.stringify(state));}catch(e){}}
function restore(){
 try{var x=JSON.parse(win.localStorage.getItem(KEY)||'null');
 if(x&&x.version===VERSION&&Array.isArray(x.samples)&&x.topics&&typeof x.topics==='object'){
 state.samples=x.samples.filter(function(s){return s&&isFinite(s.t)&&s.t>=Date.now()-7*86400000&&(s.cpu===null||number(s.cpu)!==null)&&(s.ram===null||number(s.ram)!==null);}).slice(-MAX);
 Object.keys(x.topics).slice(0,30).forEach(function(k){if(/^[a-z_]{2,24}$/.test(k))state.topics[k]=Math.min(100,Math.max(0,Number(x.topics[k])||0));});
 state.alerts=Array.isArray(x.alerts)?x.alerts.slice(-20):[];
 }}catch(e){}
}
function baseline(key){
 var a=state.samples.map(function(s){return s[key];}).filter(function(v){return v!==null&&number(v)!==null;}).slice(-72);
 if(a.length<12)return null;
 var b=median(a);return {value:b,spread:median(a.map(function(v){return Math.abs(v-b);})),count:a.length};
}
function alert(msg,key){
 if(Date.now()-(lastWarn[key]||0)<900000)return;
 lastWarn[key]=Date.now();state.alerts.push({t:Date.now(),msg:clamp(msg,200)});
 state.alerts=state.alerts.slice(-20);save();
 var label=$('report-state');if(label)label.textContent='ALICE tự theo dõi: '+msg;
}
function observe(cpu,ram,timestamp){
 if(cpu===null&&ram===null)return {ok:false,reason:'Chưa có dữ liệu đo từ modem'};
 timestamp=typeof timestamp==='number'?timestamp:Date.now();
 if(state.samples.length&&timestamp-state.samples[state.samples.length-1].t<45000)return {ok:false,reason:'Chờ mẫu tiếp theo'};
 var c=baseline('cpu'),m=baseline('ram');
 state.samples.push({t:timestamp,cpu:cpu,ram:ram});state.samples=state.samples.slice(-MAX);
 if(cpu!==null&&c&&cpu>=Math.max(85,c.value+Math.max(20,3*c.spread)))alert('CPU '+cpu+'% cao hơn mức thường thấy '+c.value+'%. Kiểm tra tải, chưa tự thay đổi cấu hình.','cpu');
 if(ram!==null&&m&&ram>=Math.max(90,m.value+Math.max(15,3*m.spread)))alert('RAM '+ram+'% cao hơn mức thường thấy '+m.value+'%. Kiểm tra số phiên, chưa tự thay đổi cấu hình.','ram');
 save();return {ok:true,learned:state.samples.length};
}
function topic(label){
 label=String(label||'').toLowerCase();
 if(!/^[a-z_]{2,24}$/.test(label))return;
 state.topics[label]=Math.min(100,(state.topics[label]||0)+1);save();
}
function recordPrompt(q){
 if(!win.ALICE_BRAIN||typeof win.ALICE_BRAIN.predict!=='function')return;
 try{var r=win.ALICE_BRAIN.predict(q);if(r&&r.label&&r.confidence>0.25)topic(r.label);}catch(e){}
}
function summary(){
 var c=baseline('cpu'),m=baseline('ram'),leading=Object.keys(state.topics).sort(function(a,b){return state.topics[b]-state.topics[a];}).slice(0,3);
 return 'ALICE tự học cục bộ: '+state.samples.length+' mẫu đo thực, '+(c?'CPU trung vị '+c.value+'%':'CPU chưa đủ 12 mẫu')+', '+
 (m?'RAM trung vị '+m.value+'%':'RAM chưa đủ 12 mẫu')+'. '+
 (leading.length?'Nhóm câu hỏi thường gặp: '+leading.join(', ')+'. ':'')+
 (state.alerts.length?'Cảnh báo gần nhất: '+state.alerts[state.alerts.length-1].msg:'Chưa có bất thường được phát hiện.')+
 ' Dữ liệu chỉ lưu trong trình duyệt; không tự sửa ROM hay thay cấu hình router.';
}
function inspect(){
 var cpu=$('stat-cpu'),ram=$('stat-memory');if(!cpu||!ram)return;
 observe(number(cpu.textContent),number(ram.textContent));
 var el=$('model-state');if(el){
 if(el.textContent.indexOf('· tự học')<0)el.textContent=clamp(el.textContent,150)+' · tự học '+state.samples.length+' mẫu';
 else el.textContent=el.textContent.replace(/· tự học \d+ mẫu/,'· tự học '+state.samples.length+' mẫu');
 }}
function start(){
 var form=$('chat-form');if(form)form.addEventListener('submit',function(){var input=$('chat-input');if(input)recordPrompt(input.value);},true);
 doc.addEventListener('click',function(e){var n=e.target;if(n&&n.getAttribute){var prompt=n.getAttribute('data-prompt');if(prompt)recordPrompt(prompt);}},true);
 inspect();win.setInterval(inspect,60000);
}
restore();
win.ALICE_ADAPTIVE={observe:observe,baseline:baseline,summary:summary,topic:topic,recordPrompt:recordPrompt,
 getState:function(){return {sampleCount:state.samples.length,topicCounts:Object.assign({},state.topics),alertCount:state.alerts.length};},
 clearLearnedData:function(){state={version:VERSION,samples:[],topics:{},alerts:[],lastSeen:0};try{win.localStorage.removeItem(KEY);}catch(e){}}};
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',start);else start();
}(window,document));
