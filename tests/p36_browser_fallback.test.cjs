const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const src=fs.readFileSync('web/alice_p36_offline_fallback.js','utf8');
function probe(ready){
 const cache={},timers=[],messages=[];
 const el=id=>cache[id]||(cache[id]={id,children:[],value:'',disabled:true,textContent:'',
    appendChild(x){this.children.push(x); if(id==='messages')messages.push(x);}});
 const ids=['messages','chat-form','chat-input','send','boot-state','chat-progress','chat-error','model-state','new-chat','stop-chat'];
 ids.forEach(el);
 const doc={readyState:'complete',getElementById:el,querySelectorAll:()=>[],
   createElement:()=>({children:[],appendChild(x){this.children.push(x);},textContent:''}),
   createTextNode:s=>({textContent:s})};
 const context={window:null,document:doc,setTimeout:f=>{timers.push(f);},
    ALICE_BOOT_READY:ready,ALICE_BRAIN:{reply:q=>({text:'Gợi ý kiểm tra Wi-Fi '+q})}};
 context.window=context;
 vm.runInNewContext(src,context);
 while(timers.length)timers.shift()();
 return {context,cache,messages};
}
let a=probe(false);
assert.equal(a.context.ALICE_CHAT_MODE,'offline-fallback');
assert.equal(a.cache.send.disabled,false);
a.cache['chat-input'].value='wifi yếu';
a.cache['chat-form'].onsubmit({preventDefault(){}});
assert.ok(a.messages.length>=3);
assert.ok(a.messages.at(-1).children.map(n=>n.textContent).join(' ').includes('Wi-Fi'));
let b=probe(true);
assert.equal(b.cache['chat-form'].onsubmit,undefined);
assert.equal(b.context.ALICE_CHAT_MODE,undefined);
console.log('P36 PASS: offline send works, native app not overwritten');
