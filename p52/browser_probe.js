/* P52 DevTools read-only diagnostics. Run inside authenticated DrayOS ALICE frame.
 * Prints response shapes/status ONLY. No passwords, tokens, MACs or raw CGI data.
 */
(async()=>{
 const token=new URL(location.href).searchParams.get('sFormAuthStr');
 if(!token){console.warn('Open ALICE using the authenticated DrayOS menu.');return;}
 const urls=['/cgi-bin/cgidashboard.cgi?fid=1','/dashbctl.cgi?wannum=4&lannum=4','/cgi-bin/v2x00.cgi?fid=2096'];
 const results=[];
 for(const path of urls){
  let u=new URL(path,location.origin);u.searchParams.set('sFormAuthStr',token);
  const row={path:u.pathname,status:0,type:'unknown',keys:[],has_sysres:false,error:''};
  try{
   let ac=new AbortController(),timer=setTimeout(()=>ac.abort(),6000),res;
   try{res=await fetch(u,{credentials:'same-origin',cache:'no-store',signal:ac.signal});}
   finally{clearTimeout(timer);}
   row.status=res.status;
   const text=await res.text();let value;
   try{value=JSON.parse(text);}catch(e){}
   if(Array.isArray(value)){row.type='json_array';row.keys=value.filter(v=>typeof v==='string').map(s=>s.split('=')[0]).filter(s=>/^[\w]{1,64}$/.test(s)).slice(0,40);}
   else if(value&&typeof value==='object'){row.type='json_object';row.keys=Object.keys(value).filter(s=>/^[\w]{1,64}$/.test(s)).slice(0,40);}
   else row.type=/^\s*</.test(text)?'html':'other';
   row.has_sysres=row.keys.includes('sysres');
  }catch(e){row.error=e.name==='AbortError'?'Timeout':'Read failed';}
  results.push(row);
 }
 console.table(results);
 console.info('Only redacted schema, no credentials or complete CGI payload.');
})();
