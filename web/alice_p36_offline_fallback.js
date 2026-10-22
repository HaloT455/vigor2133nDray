/* ALICE P36 fallback. Same JS embedded in experimental WEB/PFS pages; router controls remain disabled unless native app works. */
(function(win,doc){'use strict';
function elem(id){return doc.getElementById(id);}
function say(id,message){var e=elem(id);if(e)e.textContent=message;}
function push(role,message){var pane=elem('messages');if(!pane)return;var node=doc.createElement('div');node.className='message '+role;var name=doc.createElement('span');name.className='who';name.textContent=role==='assistant'?'ALICE':'BẠN';node.appendChild(name);node.appendChild(doc.createTextNode(String(message)));pane.appendChild(node);pane.scrollTop=pane.scrollHeight;}
function answer(query){if(win.ALICE_BRAIN&&typeof win.ALICE_BRAIN.reply==='function'){try{return win.ALICE_BRAIN.reply(query).text;}catch(e){return 'Mô hình nhúng có lỗi: '+String(e.message||e)+'. Kiểm tra bộ nhớ trình duyệt.';}}return 'Mô hình Offline chưa tải. Hãy kiểm tra /JS/alice_local.js trên router. Chế độ này không tự đổi cấu hình mạng.';}
function offlineSend(query){query=String(query||'').trim();if(!query)return;push('user',query);push('assistant',answer(query)+'\n\n[ALICE P36 Offline · suy luận trong trình duyệt; chưa đọc số liệu router]');var input=elem('chat-input');if(input)input.value='';say('chat-progress','Đã trả lời bằng AI Offline.');}
function recover(){if(win.ALICE_BOOT_READY)return;
 var form=elem('chat-form'),input=elem('chat-input'),send=elem('send');if(!form||!input||!send)return;
 win.ALICE_CHAT_MODE='offline-fallback';win.ALICE_BOOT_READY=true;
 say('boot-state','ALICE P36: AI Offline dự phòng đang chạy. Không phụ thuộc 192.168.4.145.');
 say('chat-progress','Sẵn sàng: Chat AI Offline. Các chức năng quản lý mạng cần phiên DrayOS và thư viện tương ứng.');
 say('chat-error','');say('model-state','AI Offline trong ROM · 15 chủ đề · chế độ dự phòng');
 send.disabled=false;send.textContent='Gửi yêu cầu';
 form.onsubmit=function(e){if(e&&e.preventDefault)e.preventDefault();offlineSend(input.value);};
 input.onkeydown=function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();offlineSend(input.value);}};
 var buttons=doc.querySelectorAll('[data-prompt]');for(var i=0;i<buttons.length;i++)buttons[i].onclick=function(){offlineSend(this.getAttribute('data-prompt'));};
 var clear=elem('new-chat');if(clear)clear.onclick=function(){var pane=elem('messages');if(pane)pane.textContent='';push('assistant','Xin chào. ALICE Offline đang hoạt động; hỏi về Wi-Fi, mesh, WAN, LAN, DNS, VPN, QoS và bảo mật.');};
 var stop=elem('stop-chat');if(stop){stop.disabled=true;stop.onclick=function(){};}
 push('assistant','ALICE Offline đã khôi phục khung chat. Bạn có thể gửi câu hỏi ngay, không cần máy chủ AI .145.');
}
function init(){win.setTimeout(recover,250);win.setTimeout(function(){if(!win.ALICE_BOOT_READY)recover();},1500);}
if(doc.readyState==='loading')doc.addEventListener('DOMContentLoaded',init);else init();
}(window,document));
