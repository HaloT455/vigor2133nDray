/* P52: one same-origin session resolver and one configured gateway endpoint. */
(function(w,d){'use strict';
function valid(v){return typeof v==='string'&&v.length>0&&v.length<=256&&!/[<>"'\r\n]/.test(v);}
function token(frame){try{var u=new URL(frame.location.href);if(u.origin!==location.origin)return '';var t=u.searchParams.get('sFormAuthStr');return valid(t)?t:'';}catch(e){return '';}}
function host(){var p=w;for(var i=0;i<4;i++){try{if(p.location.origin!==w.location.origin)break;if(typeof p.setVle2Elmt==='function'&&typeof p.getVleFromElmt==='function'&&p.SHOW_SYS_ADMIN!==undefined)return p;if(p.parent===p)break;p=p.parent;}catch(e){break;}}return w.parent;}
function auth(){var t=token(w);if(t)return t;var el=d.getElementById('alice-form-auth');if(el&&valid(el.value))return el.value;var h=host();t=token(h);if(t)return t;try{if(h.main&&(t=token(h.main)))return t;if(h.menu){var menu=h.menu.document;var input=menu.querySelector('input[name="sFormAuthStr"]');if(input&&valid(input.value))return input.value;var m=/[?&]sFormAuthStr=([^'"<>\s&]+)/i.exec(menu.documentElement.innerHTML);if(m){t=decodeURIComponent(m[1]);if(valid(t))return t;}}}catch(e){}return '';}
function origin(value){try{var u=new URL(value);if(/^https?:$/.test(u.protocol)&&!u.username&&!u.password&&u.pathname==='/'&&!u.search&&!u.hash)return u.origin;}catch(e){}return '';}
function gateway(){var saved='';try{saved=origin(w.localStorage.getItem('alice.gateway.endpoint')||'');}catch(e){}if(saved&&!/^https?:\/\/(192\.168\.2\.210|192\.168\.4\.145|192\.168\.10\.1)(?::80)?$/.test(saved))return saved;var field=d.getElementById('gateway-url');return origin(field&&field.value)||'http://192.168.4.210';}
function endpoint(value){var v=origin(value);if(!v)throw Error('Nhập địa chỉ gốc HTTP/HTTPS của dịch vụ Alice.');try{w.localStorage.setItem('alice.gateway.endpoint',v);}catch(e){}var input=d.getElementById('gateway-url');if(input)input.value=v;w.dispatchEvent(new CustomEvent('alice:gateway',{detail:{origin:v}}));return v;}
function gatewayHeaders(){var out={'Content-Type':'application/json'};try{var v=w.sessionStorage.getItem('alice.p22.gateway');if(v)out.Authorization='Basic '+v;}catch(e){}return out;}
function links(){var selected=gateway();Array.prototype.forEach.call(d.querySelectorAll('a[href]'),function(a){try{var u=new URL(a.href);if(u.origin==='http://192.168.4.210')a.href=selected+u.pathname+u.search+u.hash;}catch(e){}});}
w.addEventListener('alice:gateway',links);if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',links);else links();
w.ALICE_CONTEXT={auth:auth,host:host,gateway:gateway,setGateway:endpoint,gatewayHeaders:gatewayHeaders};
if(typeof w.ALICE_UPDATE_CONFIG==='function')w.ALICE_UPDATE_CONFIG(w.ALICE_CONFIG_STATE||{ppa:null,bw4:null,bw6:null,smart:null});
}(window,document));
