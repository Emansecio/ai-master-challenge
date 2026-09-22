// Browser-only test fixture. Inject into a disposable localhost tab before app.js.
// All /api requests are intercepted; no writes or model calls reach the server.
// rows: two historical cases from evidence/business-review.json.
export function installLeadDeskFixture(rows) {
 const originalFetch=window.fetch.bind(window);
 const state=window.leadDeskTest={rows:structuredClone(rows),pendingSave:null,reads:0,clipboard:'',clipboardFails:false,auditReads:0};
 for(const r of state.rows){r.classification=null;r.status='unclassified'}
 const json=value=>new Response(JSON.stringify(value),{headers:{'Content-Type':'application/json'}});
 Object.defineProperty(navigator,'clipboard',{configurable:true,value:{async writeText(text){if(state.clipboardFails)throw new Error('Clipboard test denial');state.clipboard=text}}});
 window.fetch=async(input,options={})=>{
  const url=new URL(String(input),location.href);
  if(!url.pathname.startsWith('/api/'))return originalFetch(input,options);
  if(url.pathname==='/api/meta')return json({user:{id:'teste-local',role:'admin'},filters:{sales_agent:[],manager:[],region:[]},accounts:['Acme Corporation','Globex'],key_configured:false});
  if(url.pathname==='/api/opportunities')return json({rows:state.rows,total:state.rows.length,scope_total:state.rows.length,counts:{identify_account:2},page:1,pages:1});
  const match=url.pathname.match(/^\/api\/opportunities\/([^/]+)(\/audit)?$/);
  if(match){
   const row=state.rows.find(r=>r.id===decodeURIComponent(match[1]));
   if(!row)throw new Error('Unknown fixture row');
   if(match[2]){
    state.auditReads++;
    return json({opportunity_id:row.id,current_version:row.version,policy_hash:'fixture-policy',policy_version:'test',dataset_sha256:'fixture',history_limit:20,version_count:1,classification_count:0,versions:[],classifications:[],attempt_count:1,attempts:[{job_id:'fixture-job',attempt:1,version:row.version,policy_hash:'fixture-policy',outcome:'interrupted',elapsed_ms:null,recorded_at:'2026-09-22T12:00:00Z'}]});
   }
   if(options.method==='PATCH'){
    const body=JSON.parse(options.body);
    return new Promise(resolve=>{state.pendingSave=()=>{row.account=body.account;row.version++;row.state.account_identified=true;row.decision.next_action='continue_negotiation_review';row.action_label='Definir próximo passo';state.pendingSave=null;resolve(json(row))}});
   }
   state.reads++;return json(row);
  }
  // Deliberately fail closed for every other API, including /api/classify.
  throw new Error('API not permitted by the local UI fixture: '+url.pathname);
 };
}
