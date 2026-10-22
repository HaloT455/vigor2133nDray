const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('web/alice_p37_adaptive.js','utf8');
const local={};const fields={'stat-cpu':{textContent:'25%'},'stat-memory':{textContent:'40%'},
 'report-state':{textContent:'Chưa đọc'},'model-state':{textContent:'AI Offline'}};
const doc={readyState:'complete',getElementById:name=>fields[name]||null,
 addEventListener:()=>{}};
const storage={getItem:k=>local[k]||null,setItem:(k,v)=>{local[k]=v},removeItem:k=>delete local[k]};
const w={localStorage:storage,setInterval:()=>1,ALICE_BRAIN:{predict:()=>({label:'wifi',confidence:0.95})}};
w.window=w;
vm.runInNewContext(source,{window:w,document:doc,Date,Math,JSON,isFinite,parseFloat,String,Object,Array,Number});
const learner=w.ALICE_ADAPTIVE;
assert.equal(learner.getState().sampleCount,1);
let t=Date.now();
for(let n=1;n<=16;n++)learner.observe(25,40,t+n*65000);
assert.equal(learner.baseline('cpu').value,25);
learner.observe(95,95,t+17*65000);
assert.ok(learner.getState().alertCount>0);
learner.recordPrompt('wifi yếu');assert.ok(learner.getState().topicCounts.wifi>=1);
assert.match(learner.summary(),/CPU trung vị/);
assert.doesNotMatch(local['alice.p37.trends.v1'],/wifi yếu|password|mac-address/);
let previous=learner.getState().sampleCount;
learner.observe(null,null,t+18*65000);
assert.equal(learner.getState().sampleCount,previous);
learner.clearLearnedData();
assert.equal(learner.getState().sampleCount,0);
console.log('P37 PASS: bounded local learning, anomaly alerts and privacy guards');
