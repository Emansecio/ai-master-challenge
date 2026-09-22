import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {explainRecommendation,reasonPreview,conferenceSummary} from '../static/recommendation.js';

const reviewed=JSON.parse(readFileSync(new URL('../evidence/business-review.json',import.meta.url),'utf8')).cases.map(c=>c.opportunity);
const row=id=>structuredClone(reviewed.find(r=>r.id===id));
test('a missing account and long duration retain both operational checks',()=>{
 const r=row('A7SA2L21'),before=JSON.stringify(r),e=explainRecommendation(r);
 assert.match(e.rule,/Empresa ainda não identificada/);
 assert.match(reasonPreview(r),/duração acima/);
 assert.doesNotMatch(reasonPreview(row('DB801ISB')),/duração acima/);
 assert.match(e.secondary,/duas verificações/);
 assert.equal(e.duration.comparison,'231 dias acima da referência');
 assert.match(e.duration.scope,/global.*25.*30/);
 assert.match(e.steps[0].title,/empresa/);
 assert.match(e.steps[1].title,/ativa/);
 assert.equal(JSON.stringify(r),before);
});
test('equality to the reference never becomes an above-reference signal',()=>{
 const e=explainRecommendation(row('197EQMY8'));
 assert.equal(e.duration.comparison,'Na referência: não ultrapassou o limite');
 assert.equal(e.secondary,null);
 assert.equal(e.duration.ageWidth,e.duration.referenceWidth);
});
test('prospecting has no fictitious duration and prompts discovery',()=>{
 for(const id of ['0E8D6TCQ','DDHNCZMO','E6DGJSDW']){
  const e=explainRecommendation(row(id));assert.equal(e.duration,null);assert.equal(e.secondary,null);
  assert.ok(e.steps.some(s=>s.question.includes('problema')));
 }
});
test('being below the reference is not presented as a healthy negotiation',()=>{
 const e=explainRecommendation(row('K9KGXL2E'));
 assert.equal(e.duration.comparison,'86 dias abaixo da referência');
 assert.match(e.limit,/não prova.*saudável/);assert.match(e.steps[1].record,/data confirmados/);
});
test('invalid or unknown decisions suppress numerical authority',()=>{
 for(const action of ['human_review','unrecognized']){
  const r=row('A7SA2L21');r.decision.next_action=action;
  const e=explainRecommendation(r);assert.equal(e.duration,null);assert.equal(e.secondary,null);
  assert.match(e.steps[0].question,/ausente ou contraditória/);
 }
});
test('all reviewed cases have actionable questions, provenance limits and unchanged decisions',()=>{
 for(const r of reviewed){
  const before=JSON.stringify(r),e=explainRecommendation(r);
  assert.ok(e.rule&&e.summary&&e.limit&&reasonPreview(r));
  assert.ok(e.steps.every(s=>s.title&&s.question&&s.record));
  assert.equal(e.missing.length,6);
  if(e.duration){assert.ok(e.duration.ageWidth>=0&&e.duration.ageWidth<=100);assert.ok(e.duration.referenceWidth>0&&e.duration.referenceWidth<=100)}
  assert.equal(JSON.stringify(r),before);
 }
});
test('fractional references are preserved and non-finite numbers are not graphed',()=>{
 const r=row('7GDSUY9K');r.state.reference_p90_days=116.5;
 assert.equal(explainRecommendation(r).duration.comparison,'0,5 dias acima da referência');
 for(const value of [0,-1,NaN,Infinity]){r.state.reference_p90_days=value;assert.equal(explainRecommendation(r).duration,null)}
});
test('unknown commercial fields follow the supplied state',()=>{
 const r=row('DDHNCZMO');r.state.unavailable=['last_contact'];
 assert.deepEqual(explainRecommendation(r).missing,['Último contato']);
});

test('conference handoff keeps historical provenance, unknowns and simultaneous alerts',()=>{
 const r=row('A7SA2L21'),before=JSON.stringify(r),summary=conferenceSummary(r);
 assert.match(summary,/ATENDIMENTO NÃO REGISTRADO/);
 assert.match(summary,/A7SA2L21 · versão 1/);
 assert.match(summary,/31\/12\/2017/);
 assert.match(summary,/duas verificações/);
 assert.match(summary,/SEM RESPOSTAS REGISTRADAS/);
 assert.match(summary,/Informações ausentes.*Orçamento.*Último contato/);
 assert.match(summary,/não comprova contato/);
 assert.equal(JSON.stringify(r),before);
});

test('conference handoff does not invent dates or duration for prospecting',()=>{
 const summary=conferenceSummary(row('DDHNCZMO'));
 assert.doesNotMatch(summary,/Duração calculada|Comparação de duração/);
 assert.match(summary,/PERGUNTAS A CONFIRMAR/);
 assert.match(summary,/Quem participa da decisão/);
});
test('all 2089 local opportunities produce consistent explanations without model calls',{skip:process.env.LEADDESK_LIVE_TEST!=='1'},async()=>{
 const code=JSON.parse(readFileSync(new URL('../.local/access-codes.json',import.meta.url),'utf8')).admin;
 const get=async page=>{const response=await fetch(`http://127.0.0.1:8766/api/opportunities?page=${page}`,{headers:{Authorization:`Bearer ${code}`}});assert.equal(response.status,200);return response.json()};
 const first=await get(1),rows=[...first.rows];
 for(let p=2;p<=first.pages;p+=8){const pages=await Promise.all(Array.from({length:Math.min(8,first.pages-p+1)},(_,i)=>get(p+i)));rows.push(...pages.flatMap(x=>x.rows))}
 assert.equal(rows.length,2089);assert.equal(new Set(rows.map(r=>r.id)).size,2089);
 for(const r of rows){
  const e=explainRecommendation(r);assert.ok(e.summary&&e.steps.length&&reasonPreview(r),r.id);
  const shouldHaveDuration=r.state.stage==='Engaging'&&r.decision.next_action!=='human_review';
  assert.equal(!!e.duration,shouldHaveDuration,r.id);
  if(e.duration){assert.equal(e.duration.age>e.duration.reference,r.state.age_exceeds_reference_p90,r.id);assert.ok(Number.isFinite(e.duration.ageWidth)&&Number.isFinite(e.duration.referenceWidth),r.id)}
  const secondary=r.decision.next_action==='identify_account'&&r.state.age_exceeds_reference_p90;
  assert.equal(!!e.secondary,secondary,r.id);
 }
});
