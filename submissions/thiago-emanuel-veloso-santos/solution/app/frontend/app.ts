import {explainRecommendation,reasonPreview,conferenceSummary,type RecommendationInput} from './recommendation.js';
type Row = RecommendationInput & {id:string;version:number;account:string;sales_agent:string;manager:string;region:string;sector:string;priority:number;action_label:string;qualification_label:string;reasons:string[];decision:{next_action:string};state:{product:string;catalog_price:number;stage:string;age_days:number|null;reference_p90_days:number;duration_reference_scope:string;historical_product_closed_n:number};status:string;error?:string;classification:null|{answers:Record<string,{confidence:number}>}};
type Listing={rows:Row[];total:number;scope_total:number;counts:Record<string,number>;page:number;pages:number};
type Meta={user:{id:string;role:string};filters:Record<string,string[]>;accounts:string[];key_configured:boolean};
const el=<T extends HTMLElement=HTMLElement>(id:string)=>document.getElementById(id) as T;
const esc=(s:unknown)=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!));
const number=(n:number)=>n.toLocaleString('pt-BR');
const currency=(n:number)=>n.toLocaleString('pt-BR',{style:'currency',currency:'USD',maximumFractionDigits:0});
let meta:Meta;let page=1;let action='';let current:Row|undefined;let data:Listing|undefined;let sequence=0;let poll:number|undefined;
const filters=['sales_agent','manager','region'];
const selectionKeys=['search',...filters,'action','page'];
function selectionQuery(){
 const query=new URLSearchParams({page:String(page),action,search:el<HTMLInputElement>('search').value});
 for(const field of filters)query.set(field,el<HTMLSelectElement>(field).value);
 return query;
}
function writeLocation(mode:'push'|'replace',query=selectionQuery()){
 const url=new URL(location.href);
 for(const key of selectionKeys){const value=query.get(key)||'';url.searchParams.delete(key);if(value&&(key!=='page'||value!=='1'))url.searchParams.set(key,value)}
 if(url.href!==location.href){if(mode==='push')history.pushState(null,'',url);else history.replaceState(null,'',url)}
}
function restoreLocation(){
 const query=new URLSearchParams(location.search),requested=Number(query.get('page')||1);
 page=Number.isSafeInteger(requested)&&requested>0?requested:1;
 const requestedAction=query.get('action')||'';
 action=['human_review','review_old_negotiation','qualify_prospect','continue_negotiation_review','identify_account'].includes(requestedAction)?requestedAction:'';
 el<HTMLInputElement>('search').value=query.get('search')||'';
 for(const field of filters){const value=query.get(field)||'';el<HTMLSelectElement>(field).value=meta.filters[field].includes(value)?value:''}
}
function navigate(scrollToResults=false){clearTimeout(debounce);writeLocation('push');void load(scrollToResults)}
function rememberDraft(r:Row){
 const account=el<HTMLSelectElement>('account-select').value;
 if(account===r.account)drafts.delete(r.id);else drafts.set(r.id,{version:r.version,account});
 el<HTMLButtonElement>('save-account').disabled=account===r.account||saving.has(r.id);
 el('draft-status').textContent=account===r.account?'Nenhuma alteração pendente.':'Alteração ainda não salva. Mantida ao navegar nesta sessão.';
}
function stamp(value:string){return new Date(value).toLocaleString('pt-BR',{timeZone:'America/Sao_Paulo'})+' (Brasília)'}
type Audit={opportunity_id:string;current_version:number;policy_hash:string;policy_version:string;dataset_sha256:string;history_limit:number;version_count:number;classification_count:number;attempt_count:number;attempts:{job_id:string;attempt:number;version:number;policy_hash:string;outcome:string;elapsed_ms:number|null;recorded_at:string}[];versions:{version:number;actor:string;recorded_at:string;account:string}[];classifications:{version:number;policy_hash:string;origin:string;recorded_at:string;model:string;current:boolean;current_at_commit:boolean;qualification:string;next_action:string}[]};
async function showAudit(r:Row){
 const panel=el('audit-content');if(!panel.textContent)panel.textContent='Carregando histórico…';panel.setAttribute('aria-busy','true');
 const epoch=sessionEpoch;
 try{
  const a=await api<Audit>('/api/opportunities/'+encodeURIComponent(r.id)+'/audit');
  if(epoch!==sessionEpoch||!panel.isConnected||current?.id!==r.id)return;
  const origins:Record<string,string>={ensaio_validado:'Ensaio real importado',consulta_ao_vivo:'Consulta ao vivo',test_fixture:'Resposta controlada de teste'};
  const outcomes:Record<string,string>={succeeded:'Concluída',stale:'Resultado desatualizado',pending:'Falha transitória; nova tentativa agendada',failed:'Falha; revisão técnica necessária',interrupted:'Interrupção detectada: reserva de processamento vencida'};
  const expanded=Array.from(panel.querySelectorAll<HTMLDetailsElement>('details[id][open]')).map(d=>d.id);
  const focusId=panel.contains(document.activeElement)?(document.activeElement as HTMLElement).id:'';
  panel.innerHTML=`<p>Versão atual: ${a.current_version}. Política: ${esc(a.policy_version)}.</p><p>Mostrando até ${a.history_limit} registros mais recentes de cada histórico. As datas são dos registros locais ou do recibo importado; não representam contato com o cliente.</p><h4>Versões dos dados (${number(a.version_count)})</h4><ol>${a.versions.map(v=>`<li><strong>Versão ${v.version}</strong> · ${esc(v.account||'Sem empresa')}<br>${esc(v.actor)} · ${esc(stamp(v.recorded_at))}</li>`).join('')}</ol><h4>Classificações (${number(a.classification_count)})</h4>${a.classifications.length?`<ol>${a.classifications.map(c=>`<li><strong>${c.current?'Atual':'Histórica'}</strong> · versão ${c.version}<br>${esc(origins[c.origin]||c.origin)} · ${esc(c.model)}<br>${esc(stamp(c.recorded_at))}<br>Qualificação: <code>${esc(c.qualification)}</code><br>Ação: <code>${esc(c.next_action)}</code><br>${c.current_at_commit?'Correspondia à versão e política na gravação.':'Já estava desatualizada na gravação.'}<details id="classification-${esc(c.version)}-${esc(c.policy_hash)}"><summary>Assinatura da classificação</summary><code>${esc(c.policy_hash)}</code></details></li>`).join('')}</ol>`:'<p>Nenhuma classificação registrada. A orientação usa a política local.</p>'}<h4>Tentativas registradas (${number(a.attempt_count)})</h4><p>As datas indicam o registro local do resultado ou a detecção da interrupção. Uma reserva vencida não confirma se o provedor chegou a responder; duração e custo externos podem ser desconhecidos.</p>${a.attempts.length?`<ol>${a.attempts.map(t=>`<li><strong>${esc(outcomes[t.outcome]||'Estado a revisar')}</strong><br>Tentativa ${t.attempt} · versão ${t.version}<br>${esc(stamp(t.recorded_at))}<br>${t.elapsed_ms===null?'Duração não medida':`Tempo medido: ${number(t.elapsed_ms)} ms`}<details id="attempt-${esc(t.job_id)}-${t.attempt}"><summary>Identificação da tentativa</summary><p>Trabalho: <code>${esc(t.job_id)}</code><br>Política: <code>${esc(t.policy_hash)}</code></p></details></li>`).join('')}</ol>`:'<p>Nenhuma tentativa registrada neste histórico. Recibos importados e trabalhos ainda na fila não representam tentativas locais concluídas.</p>'}<details id="audit-sources"><summary>Identificação das fontes</summary><p>Assinatura da política ativa:<br><code>${esc(a.policy_hash)}</code></p><p>SHA-256 do dataset:<br><code>${esc(a.dataset_sha256)}</code></p></details>`;
  identifySummaries(panel);
  for(const id of expanded){const d=document.getElementById(id) as HTMLDetailsElement|null;if(d)d.open=true}
  if(focusId)document.getElementById(focusId)?.focus({preventScroll:true});
 }catch(e){if(panel.isConnected&&epoch===sessionEpoch)panel.textContent=(e as Error).message}finally{panel.setAttribute('aria-busy','false')}
}
function identifySummaries(root:HTMLElement){
 for(const disclosure of root.querySelectorAll<HTMLDetailsElement>('details[id]')){const summary=disclosure.querySelector('summary');if(summary)summary.id=disclosure.id+'-summary'}
}
function recommendationView(r:Row){
 const why=explainRecommendation(r),d=why.duration;
 return `<section class="detail-section recommendation" aria-labelledby="recommendation-title"><h3 id="recommendation-title">Por que esta ação?</h3><div class="recommendation-reason"><span class="evidence-label">Critério da política</span><strong>${esc(why.rule)}</strong><p>${esc(why.summary)}</p></div><dl class="evidence-facts">${why.facts.map(f=>`<div><dt>${esc(f.label)}</dt><dd>${esc(f.value)}</dd></div>`).join('')}</dl>${d?`<figure class="duration-comparison"><figcaption><strong>${esc(d.comparison)}</strong><span>Duração em ${esc(d.asOf)}</span></figcaption><div class="duration-row"><span>Negociação <strong>${number(d.age)} dias</strong></span><svg class="duration-chart" viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden="true"><rect class="chart-track" width="100" height="8" rx="2"/><rect class="chart-value" width="${d.ageWidth}" height="8" rx="2"/></svg></div><div class="duration-row reference"><span>Referência P90 <strong>${number(d.reference)} dias</strong></span><svg class="duration-chart" viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden="true"><rect class="chart-track" width="100" height="8" rx="2"/><rect class="chart-value" width="${d.referenceWidth}" height="8" rx="2"/></svg></div><p>${esc(d.scope)}</p><details id="duration-help"><summary>Como interpretar esta comparação</summary><p>O P90 abrange aproximadamente 90% das durações dos negócios encerrados usados como referência, incluindo ganhos e perdas. Comparamos o tempo em negociação; não é prazo do cliente, tempo sem contato ou chance de venda.</p></details></figure>`:''}${why.secondary?`<div class="secondary-signal"><strong>Também precisa de atenção</strong><p>${esc(why.secondary)}</p></div>`:''}<p class="recommendation-limit">${esc(why.limit)}</p></section><section class="detail-section next-steps"><h3>Como conduzir o atendimento</h3><p class="small muted">Perguntas sugeridas. Registre as respostas confirmadas no CRM de origem.</p><ol>${why.steps.map(step=>`<li><strong>${esc(step.title)}</strong><p>${esc(step.question)}</p><small><b>Resultado esperado:</b> ${esc(step.record)}</small></li>`).join('')}</ol></section>${why.missing.length?`<details id="missing-evidence" class="detail-section missing-evidence"><summary>O que ainda não sabemos (${why.missing.length})</summary><ul>${why.missing.map(item=>`<li>${esc(item)}</li>`).join('')}</ul><p class="small muted">Essas informações não constam nesta base. A recomendação orienta a conferência; não substitui a resposta do cliente.</p></details>`:''}`;
}

let notice:{text:string;opportunityId?:string;placement?:'copy'}|undefined;
function renderMessage(){
 const text=notice?.text||'';
 const copy=document.getElementById('copy-status');
 const inline=!!copy&&notice?.placement==='copy'&&notice.opportunityId===current?.id&&el<HTMLDetailsElement>('conference-summary').open&&(!compactDetail.matches||detailDialog.open);
 el('message').textContent=inline?'':notice?.opportunityId?`${notice.opportunityId}: ${text}`:text;el('message').hidden=!text||inline;
 const local=document.getElementById('detail-message');
 if(local){const applies=!notice?.opportunityId||notice.opportunityId===current?.id;local.textContent=applies&&!inline?text:'';local.hidden=!applies||!text||inline}
 if(copy){copy.textContent=inline?text:'';copy.hidden=!inline||!text}
}
function message(text:string,opportunityId?:string,placement?:'copy'){notice=text?{text,opportunityId,placement}:undefined;renderMessage()}
function accountForm(r:Row){
 const primary=r.decision.next_action==='identify_account';
 return `<section class="detail-section ${primary?'account-action':''}" aria-labelledby="account-heading"><h3 id="account-heading">${primary?'Confirme e vincule a empresa':'Conta vinculada'}</h3>${primary?'<p class="small">Confira a empresa no CRM de origem antes de escolher. Não selecione uma conta apenas para completar o cadastro.</p>':''}<form id="account-form"><select id="account-select" aria-label="Empresa vinculada" aria-describedby="draft-status account-help" ${saving.has(r.id)?'disabled':''}><option value="">Sem empresa</option>${meta.accounts.map(a=>`<option ${a===r.account?'selected':''}>${esc(a)}</option>`).join('')}</select><button id="save-account" class="${primary?'primary':'secondary'}" type="submit" disabled>Salvar</button></form><p id="draft-status" class="small" role="status"></p><p id="account-help" class="small muted">Uma alteração invalida a classificação anterior e fica registrada no histórico local.</p></section>`;
}
function summaryView(r:Row){
 return `<details id="conference-summary" class="detail-section"><summary>Resumo para levar ao CRM</summary><p class="small muted">Revise o roteiro antes de copiar. Ele contém fatos históricos e perguntas pendentes; não registra um atendimento.</p><label class="sr-only" for="conference-text">Resumo de conferência da oportunidade ${esc(r.id)}</label><textarea id="conference-text" rows="10" readonly>${esc(conferenceSummary(r))}</textarea><p id="copy-status" class="message" role="status" hidden></p><button id="copy-summary" class="secondary" type="button">Copiar resumo de conferência</button></details>`;
}
const compactSummary=window.matchMedia('(max-width:700px)');
const summaryPanel=el<HTMLDetailsElement>('summary-panel');summaryPanel.open=!compactSummary.matches;
compactSummary.addEventListener('change',()=>{summaryPanel.open=!compactSummary.matches});
const compactDetail=window.matchMedia('(max-width:1100px)');
const detailDialog=el<HTMLDialogElement>('detail-dialog');
let returnToRow:string|undefined;
const detailPlaceholder='<div class="detail-placeholder"><h2>Um próximo passo por vez</h2><p>Selecione uma oportunidade para conferir os motivos e o roteiro de ação.</p></div>';
function restoreDetail(){
 el('detail-pane').append(el('detail'));document.body.classList.remove('detail-open');
 if(!el('shell').hidden&&returnToRow){const button=Array.from(el('rows').querySelectorAll<HTMLButtonElement>('button[data-id]')).find(b=>b.dataset.id===returnToRow);(button||el('search')).focus({preventScroll:true})}
 returnToRow=undefined;
 renderMessage();
}
detailDialog.addEventListener('close',restoreDetail);
detailDialog.addEventListener('keydown',event=>{
 if(event.key!=='Tab'||!detailDialog.open)return;
 const targets=Array.from(detailDialog.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),summary,[tabindex]:not([tabindex="-1"])')).filter(node=>node.getClientRects().length>0);
 const first=targets[0],last=targets[targets.length-1];
 if(!first)return;
 const focused=document.activeElement as HTMLElement;
 if(!targets.includes(focused)||(!event.shiftKey&&focused===last)||(event.shiftKey&&focused===first)){
  event.preventDefault();(event.shiftKey?last:first).focus();
 }
});
compactDetail.addEventListener('change',()=>{if(!compactDetail.matches&&detailDialog.open)detailDialog.close()});
function openDetail(r:Row){
 detail(r);
 if(compactDetail.matches){returnToRow=r.id;el('detail-mobile-host').append(el('detail'));document.body.classList.add('detail-open');if(!detailDialog.open)detailDialog.showModal();detailDialog.scrollTop=0}
 else el('detail').scrollTop=0;
 el('detail-title').focus({preventScroll:true});
 renderMessage();
}

let listRequest:AbortController|undefined;
let sessionEpoch=0;
const drafts=new Map<string,{version:number;account:string}>();
const saving=new Set<string>();
class ApiError extends Error {constructor(message:string,public status:number){super(message)}}
function resetSession(reason=''){
 returnToRow=undefined;if(detailDialog.open)detailDialog.close();
 sessionEpoch++;sequence++;listRequest?.abort();clearTimeout(poll);clearTimeout(debounce);
 drafts.clear();saving.clear();current=undefined;data=undefined;page=1;action='';
 for(const id of ['metric-total','metric-review','metric-discovery','metric-missing'])el(id).textContent='—';
 el('summary-count').textContent='';el('data-quality').hidden=true;el('page-label').textContent='';el('load-status').textContent='';message('');
 el('rows').replaceChildren();el('detail').replaceChildren();
 el('shell').hidden=true;el('login').hidden=false;el('login-error').textContent=reason;
 el<HTMLInputElement>('search').value='';el<HTMLInputElement>('access-code').focus();
}
async function api<T>(path:string,options:RequestInit={}):Promise<T>{
 const epoch=sessionEpoch;let response:Response;
 try{response=await fetch(path,{...options,headers:{'Content-Type':'application/json',...options.headers}})}catch(e){if((e as Error).name==='AbortError')throw e;throw new Error('Não foi possível conectar. Confira se o servidor está disponível e tente atualizar.')}
 if(epoch!==sessionEpoch)throw new DOMException('Sessão alterada','AbortError');
 let value:any;try{value=await response.json()}catch{throw new Error('O servidor retornou uma resposta inválida. Tente novamente.')}
 if(epoch!==sessionEpoch)throw new DOMException('Sessão alterada','AbortError');
 if(response.status===401)resetSession(value.error||'Entre novamente.');
 if(!response.ok)throw new ApiError(value.error||'Não foi possível concluir.',response.status);
 return value as T;
}
const statusLabel=(r:Row)=>({classified:'Jev · coerente com a política',pending:'Na fila',running:'Classificando…',failed:'Falha · regra local',stale:'Desatualizado · regra local',unclassified:'Política local'}[r.status]||'Política local');
async function start(){el('retry-start').hidden=true;try{meta=await api<Meta>('/api/meta');el('login').hidden=true;el('shell').hidden=false;el('user-name').textContent=meta.user.id;el('avatar').textContent=meta.user.id[0].toUpperCase();el('user-role').textContent=({admin:'Administrador',manager:'Gestor',seller:'Vendedor'}[meta.user.role]||meta.user.role);for(const field of filters){el(field).innerHTML=`<option value="">${field==='region'?'Todas':'Todos'}</option>`+meta.filters[field].map(v=>`<option>${esc(v)}</option>`).join('')}restoreLocation();await load()}catch(e){if((e as Error).name==='AbortError')return;if(!el('shell').hidden)message((e as Error).message);else{el('login').hidden=false;el('login-error').textContent=(e as Error).message;el('retry-start').hidden=e instanceof ApiError&&e.status===401}}}
async function load(scrollToResults=false){
 const seq=++sequence;listRequest?.abort();listRequest=new AbortController();
 const query=selectionQuery();
 el('results-region').setAttribute('aria-busy','true');el('load-status').textContent='Atualizando carteira…';
 el<HTMLButtonElement>('prev').disabled=true;el<HTMLButtonElement>('next').disabled=true;
 try{
  const value=await api<Listing>('/api/opportunities?'+query,{signal:listRequest.signal});if(seq!==sequence)return;
  const focusedQueue=(document.activeElement as HTMLElement)?.dataset.action;
  data=value;page=data.page;query.set('page',String(page));writeLocation('replace',query);render();
  if(focusedQueue!==undefined){for(const button of el('queues').querySelectorAll<HTMLButtonElement>('button'))if(button.dataset.action===focusedQueue)button.focus()}
  if(current){const fresh=data.rows.find(r=>r.id===current!.id);if(fresh)detail(fresh);else{current=undefined;el('detail').innerHTML=detailPlaceholder;if(detailDialog.open)detailDialog.close();clearTimeout(poll)}}else if(data.rows[0])detail(data.rows[0]);
  el('load-status').textContent=`${number(data.total)} ${data.total===1?'oportunidade encontrada':'oportunidades encontradas'}. Página ${data.page} de ${data.pages}.`;
  if(scrollToResults){el('portfolio-title').focus({preventScroll:true});el('results-region').scrollIntoView({block:'start'})}
 }catch(e){if(seq===sequence&&(e as Error).name!=='AbortError'){if(data)page=data.page;message((e as Error).message);el('load-status').textContent='Falha ao atualizar. Os dados visíveis são da última consulta concluída.'}}
 finally{if(seq===sequence){el('results-region').setAttribute('aria-busy','false');if(data){el<HTMLButtonElement>('prev').disabled=data.page===1;el<HTMLButtonElement>('next').disabled=data.page===data.pages}}}
}
function render(){if(!data)return;const activeFilters=filters.filter(f=>el<HTMLSelectElement>(f).value).length;el('toggle-filters').textContent=activeFilters?`Equipe (${activeFilters} ${activeFilters===1?'filtro':'filtros'})`:'Filtrar equipe';const missing=data.counts.identify_account||0;el('data-quality').hidden=missing===0;el('data-quality-text').textContent=`${number(missing)} sem empresa vinculada (${(data.scope_total?100*missing/data.scope_total:0).toLocaleString('pt-BR',{maximumFractionDigits:1})}% da seleção). Perfil incompleto não indica menor potencial comercial.`;el('summary-count').textContent=number(data.scope_total)+' oportunidades';el('metric-total').textContent=number(data.scope_total);el('metric-review').textContent=number(data.counts.review_old_negotiation||0);el('metric-discovery').textContent=number(data.counts.qualify_prospect||0);el('metric-missing').textContent=number(data.counts.identify_account||0);
 const queues=[['','Todas',data.scope_total],...(data.counts.human_review?[['human_review','Revisão humana',data.counts.human_review]]:[]),['review_old_negotiation','Revisar',data.counts.review_old_negotiation||0],['qualify_prospect','Qualificar',data.counts.qualify_prospect||0],['continue_negotiation_review','Próximo passo',data.counts.continue_negotiation_review||0],['identify_account','Cadastro',data.counts.identify_account||0]];
 el('queues').innerHTML=queues.map(([key,label,count])=>`<button class="queue ${key===action?'active':''}" data-action="${key}" aria-pressed="${key===action}">${label} <span>${number(Number(count))}</span></button>`).join('');el('rows').innerHTML=data.rows.map(r=>`<tr role="row" data-id="${esc(r.id)}" class="${current?.id===r.id?'selected':''}"><td role="cell"><button class="open-deal" aria-controls="detail" aria-pressed="${current?.id===r.id}" data-id="${esc(r.id)}">${esc(r.account||'Empresa não vinculada')} <span class="deal-product">${esc(r.state.product)}</span> <span class="deal-key">${esc(r.id)}</span></button></td><td role="cell"><span class="badge priority-${r.priority}">${esc(r.action_label)}</span><span class="decision-reason">${esc(reasonPreview(r))}</span><span class="subtext">${esc(r.sales_agent)}</span></td><td role="cell">${currency(r.state.catalog_price)}<span class="subtext">preço de catálogo</span></td><td role="cell"><span class="source ${r.classification?'jev':''}">${statusLabel(r)}</span></td></tr>`).join('');el('empty').hidden=data.total>0;el('page-label').textContent=`${number(data.total)} ${data.total===1?'oportunidade':'oportunidades'} · página ${data.page} de ${data.pages}`;el<HTMLButtonElement>('prev').disabled=data.page===1;el<HTMLButtonElement>('next').disabled=data.page===data.pages;
}
function detail(r:Row){const same=current?.id===r.id;const auditContent=same?el('audit-content')?.innerHTML||'':'';const expanded=same?Array.from(el('detail').querySelectorAll<HTMLDetailsElement>('details[id][open]')).map(d=>d.id):[];const scrollTop=same?el('detail').scrollTop:0;const focusId=same&&el('detail').contains(document.activeElement)?(document.activeElement as HTMLElement).id:'';current=r;clearTimeout(poll);const draft=drafts.get(r.id);if(draft&&draft.version!==r.version){drafts.delete(r.id);message('A oportunidade mudou de versão. A seleção de conta não salva foi descartada; confira os dados atuais.',r.id)}for(const row of document.querySelectorAll<HTMLTableRowElement>('tr[data-id]')){row.classList.toggle('selected',row.dataset.id===r.id);row.querySelector('button')?.setAttribute('aria-pressed',String(row.dataset.id===r.id))}const busy=['pending','running'].includes(r.status);const classified=!!r.classification;const confidence=classified?Object.entries(r.classification!.answers).map(([q,a])=>`${q==='qualification'?'Qualificação':'Próxima ação'}: ${Math.round(a.confidence*100)}%`).join(' · '):'';
 el('detail').innerHTML=`<div class="detail-topline"><span class="detail-eyebrow">Oportunidade</span><button id="close-detail" class="secondary detail-close" type="button">Voltar à lista</button></div><div id="detail-message" class="message" role="status" hidden></div><span class="badge priority-${r.priority}">${esc(r.action_label)}</span><h2 id="detail-title" tabindex="-1">${esc(r.account||'Empresa não vinculada')}</h2><div class="deal-id">${esc(r.id)} · versão ${r.version}</div><p class="detail-product">${esc(r.state.product)}<br>${currency(r.state.catalog_price)} <span class="muted">· preço de catálogo</span></p>${r.decision.next_action==='identify_account'?accountForm(r):''}${recommendationView(r)}${summaryView(r)}<details id="deal-facts" class="detail-section"><summary>Dados da oportunidade</summary><dl><dt>Produto</dt><dd>${esc(r.state.product)}</dd><dt>Preço de catálogo</dt><dd>${currency(r.state.catalog_price)}</dd><dt>Setor</dt><dd>${esc(r.sector||'Não informado')}</dd><dt>Vendedor</dt><dd>${esc(r.sales_agent)}</dd><dt>Gestor</dt><dd>${esc(r.manager)}</dd><dt>Região</dt><dd>${esc(r.region)}</dd><dt>Estágio</dt><dd>${r.state.stage==='Engaging'?'Em negociação':r.state.stage==='Prospecting'?'Prospecção':'Estágio a revisar'}</dd><dt>Qualificação</dt><dd>${esc(r.qualification_label)}</dd></dl></details><details id="model-check" class="detail-section"><summary>${statusLabel(r)}</summary>${r.error?`<p class="small muted">${esc(r.error)}</p>`:''}${classified?`<p class="small muted">As duas respostas concordam com a política local; isso não comprova a qualidade comercial da decisão. Concentração das respostas do modelo: ${esc(confidence)}. Esses percentuais não medem chance de venda nem a qualidade comercial da sugestão.</p>`:'<p class="small muted">A política local já fornece esta orientação. Consultar o Jev compara a classificação do modelo com os mesmos critérios.</p>'}<button id="classify" class="primary" ${busy||classified||r.status==='failed'||!meta.key_configured?'disabled':''}>${classified?'✓ Coerência com a política conferida':busy?'Classificação em andamento…':r.status==='failed'?'Revisão técnica necessária':'Classificar com Jev'}</button>${!meta.key_configured?'<p class="small muted">A credencial do Jev precisa ser configurada no servidor.</p>':''}</details>${r.decision.next_action!=='identify_account'?accountForm(r):''}<details id="audit" class="detail-section audit"><summary>Histórico e rastreabilidade</summary><div id="audit-content" aria-live="polite">${auditContent}</div></details>`;
 renderMessage();
 identifySummaries(el('detail'));
 el('close-detail').addEventListener('click',()=>detailDialog.close());
 el('conference-summary').addEventListener('toggle',renderMessage);
 el('copy-summary').addEventListener('click',async()=>{
  const epoch=sessionEpoch,button=el<HTMLButtonElement>('copy-summary'),text=conferenceSummary(r);button.disabled=true;
  try{
   await navigator.clipboard.writeText(text);
   if(epoch===sessionEpoch)message(`Resumo da versão ${r.version} copiado. Atendimento não registrado.`,r.id,'copy');
  }catch{
   if(epoch!==sessionEpoch)return;
   message('A cópia automática não está disponível. Selecione e copie o texto do resumo manualmente.',r.id,'copy');
   if(current?.id===r.id){const field=el<HTMLTextAreaElement>('conference-text');field.focus();field.select()}
  }finally{
   button.disabled=false;
   if(epoch===sessionEpoch&&current?.id===r.id){const status=document.getElementById('copy-status');if(status&&!status.hidden)el('copy-summary').scrollIntoView({block:'nearest'})}
  }
 });
 const accountSelect=el<HTMLSelectElement>('account-select');
 const restored=drafts.get(r.id);if(restored)accountSelect.value=restored.account;
 rememberDraft(r);accountSelect.addEventListener('change',()=>rememberDraft(r));
 el('audit').addEventListener('toggle',()=>{if(el<HTMLDetailsElement>('audit').open)void showAudit(r)});
 for(const id of expanded){const disclosure=document.getElementById(id) as HTMLDetailsElement|null;if(disclosure)disclosure.open=true}el('detail').scrollTop=scrollTop;
 if(focusId){const target=document.getElementById(focusId) as HTMLButtonElement|null;if(target&&!target.disabled)target.focus({preventScroll:true});else el('detail-title').focus({preventScroll:true})}

 el('classify').addEventListener('click',async()=>{const epoch=sessionEpoch;const button=el<HTMLButtonElement>('classify');button.disabled=true;message('');try{await api('/api/classify',{method:'POST',body:JSON.stringify({id:r.id,version:r.version})});const fresh=await api<Row>('/api/opportunities/'+encodeURIComponent(r.id));if(current?.id===r.id)detail(fresh);await load()}catch(e){if(epoch===sessionEpoch&&(e as Error).name!=='AbortError')message((e as Error).message,r.id);button.disabled=false}});
 el('account-form').addEventListener('submit',async event=>{
  event.preventDefault();if(saving.has(r.id))return;
  const account=el<HTMLSelectElement>('account-select').value;if(account===r.account)return;
  saving.add(r.id);el<HTMLButtonElement>('save-account').disabled=true;accountSelect.disabled=true;
  const epoch=sessionEpoch;
  try{
   const fresh=await api<Row>('/api/opportunities/'+encodeURIComponent(r.id),{method:'PATCH',body:JSON.stringify({version:r.version,account})});
   if(epoch!==sessionEpoch)return;
   drafts.delete(r.id);message('Conta salva. A nova versão está registrada no histórico.',r.id);
   saving.delete(r.id);if(current?.id===r.id)detail(fresh);await load();
  }catch(e){if(epoch!==sessionEpoch)return;message((e as Error).message,r.id);if(e instanceof ApiError&&e.status===409){drafts.delete(r.id);await load()}}
  finally{saving.delete(r.id);if(epoch===sessionEpoch&&current?.id===r.id){el<HTMLSelectElement>('account-select').disabled=false;rememberDraft(current)}}
 });
 if(busy){const epoch=sessionEpoch;poll=window.setTimeout(async()=>{try{const fresh=await api<Row>('/api/opportunities/'+encodeURIComponent(r.id));if(current?.id===r.id){detail(fresh);if(!['pending','running'].includes(fresh.status))await load()}}catch(e){if(epoch===sessionEpoch&&(e as Error).name!=='AbortError')message((e as Error).message,r.id)}},2000);}
}
el('toggle-filters').addEventListener('click',()=>{const button=el('toggle-filters');const expanded=button.getAttribute('aria-expanded')!=='true';button.setAttribute('aria-expanded',String(expanded));el('team-filters').classList.toggle('expanded',expanded)});
for(const link of document.querySelectorAll<HTMLAnchorElement>('a[href="#method"]'))link.addEventListener('click',event=>{event.preventDefault();el<HTMLDetailsElement>('method').open=true;el('method').scrollIntoView({block:'start'});el('method').querySelector('summary')?.focus({preventScroll:true})});
el('retry-start').addEventListener('click',()=>void start());
el('login-form').addEventListener('submit',async e=>{e.preventDefault();const button=(e.currentTarget as HTMLFormElement).querySelector('button')!;button.disabled=true;el('login-error').textContent='';try{await api('/api/login',{method:'POST',body:JSON.stringify({code:el<HTMLInputElement>('access-code').value})});el<HTMLInputElement>('access-code').value='';await start()}catch(e){el('login-error').textContent=(e as Error).message}finally{button.disabled=false}});
el('logout').addEventListener('click',async()=>{if(drafts.size&&!window.confirm('Há alterações de conta não salvas. Sair e descartá-las?'))return;try{await api('/api/logout',{method:'POST',body:'{}'});resetSession()}catch(e){message((e as Error).message)}});
el('open-missing').addEventListener('click',()=>{action='identify_account';page=1;navigate()});
el('queues').addEventListener('click',e=>{const button=(e.target as HTMLElement).closest<HTMLButtonElement>('button[data-action]');if(button){action=button.dataset.action||'';page=1;navigate()}});
el('rows').addEventListener('click',e=>{const button=(e.target as HTMLElement).closest<HTMLButtonElement>('button[data-id]');const row=data?.rows.find(r=>r.id===button?.dataset.id);if(row)openDetail(row)});
for(const field of filters)el(field).addEventListener('change',()=>{page=1;navigate()});let debounce:number|undefined;el('search').addEventListener('input',()=>{clearTimeout(debounce);debounce=window.setTimeout(()=>{page=1;navigate()},250)});
function clearFilters(){for(const field of filters)el<HTMLSelectElement>(field).value='';el<HTMLInputElement>('search').value='';action='';page=1;message('');navigate()}el('clear').addEventListener('click',clearFilters);el('clear-empty').addEventListener('click',()=>{clearFilters();el('search').focus()});el('refresh').addEventListener('click',()=>{message('');void load()});el('prev').addEventListener('click',()=>{page--;navigate(true)});el('next').addEventListener('click',()=>{page++;navigate(true)});window.addEventListener('popstate',()=>{clearTimeout(debounce);if(el('shell').hidden)return;restoreLocation();message('');void load()});window.addEventListener('beforeunload',event=>{if(drafts.size){event.preventDefault();event.returnValue=''}});void start();
