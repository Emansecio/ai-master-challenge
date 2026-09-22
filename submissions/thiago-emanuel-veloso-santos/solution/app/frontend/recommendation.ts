// Presentation of the server's decision. This module never ranks or reclassifies a lead.
export type RecommendationInput = {
 account:string;
 decision:{next_action:string};
 state:{as_of:string;stage:string;account_identified:boolean;age_days:number|null;reference_p90_days:number;duration_reference_scope:string;historical_product_closed_n:number;unavailable:string[]};
};
type Step={title:string;question:string;record:string};
type Fact={label:string;value:string};
export type Explanation={rule:string;summary:string;facts:Fact[];steps:Step[];missing:string[];limit:string;secondary:string|null;duration:null|{age:number;reference:number;comparison:string;scope:string;asOf:string;ageWidth:number;referenceWidth:number}};
const number=(n:number)=>n.toLocaleString('pt-BR',{maximumFractionDigits:2});
const date=(s:string)=>/^\d{4}-\d{2}-\d{2}$/.test(s)?s.split('-').reverse().join('/'):'Data não informada';
const missingLabels:Record<string,string>={need:'Necessidade',budget:'Orçamento',authority:'Participantes da decisão',intent:'Intenção de compra',last_contact:'Último contato',next_contact_date:'Próximo contato'};
const identify:Step={title:'Confirme a empresa',question:'A qual empresa esta oportunidade pertence? Confira no CRM de origem antes de vincular.',record:'Empresa confirmada e responsável pelo atendimento. Não escolha uma conta apenas para completar o campo.'};
const status:Step={title:'Confira se a negociação segue ativa',question:'Quando ocorreu o último contato e o que o cliente respondeu?',record:'Data e resultado do contato, situação atual e eventual motivo de pausa ou encerramento, no CRM de origem.'};
const next:Step={title:'Combine um próximo passo verificável',question:'Qual ação foi combinada com o cliente, quem é responsável e para quando?',record:'Ação, responsável e data confirmados no CRM de origem. Não presuma um compromisso ainda não acordado.'};

export function explainRecommendation(r:RecommendationInput):Explanation{
 const s=r.state, action=r.decision.next_action;
 const facts:Fact[]=[{label:'Empresa',value:s.account_identified?r.account||'Identificação a conferir':'Não vinculada'},{label:'Estágio registrado',value:s.stage==='Engaging'?'Em negociação':s.stage==='Prospecting'?'Prospecção':'A revisar'}];
 const missing=(s.unavailable||[]).map(key=>missingLabels[key]||key);
 const result:Explanation={rule:'Revisão dos dados',summary:'Confira os dados antes de usar uma orientação comercial.',facts,steps:[{title:'Revise a origem dos dados',question:'Qual informação está ausente ou contraditória? Compare estágio, empresa e datas com o registro original.',record:'Correção confirmada na fonte. Reavalie a orientação somente depois da atualização.'}],missing,limit:'Os dados não permitem estimar a chance de fechamento.',secondary:null,duration:null};
 // Invalid states have no duration graphic: numerical precision must not imply valid evidence.
 if(action==='human_review'||!['identify_account','qualify_prospect','review_old_negotiation','continue_negotiation_review'].includes(action))return result;
 if(s.stage==='Engaging'&&s.age_days!==null&&Number.isFinite(s.age_days)&&s.age_days>=0&&Number.isFinite(s.reference_p90_days)&&s.reference_p90_days>0){
  const age=s.age_days,reference=s.reference_p90_days,delta=age-reference,max=Math.max(age,reference);
  const comparison=delta>0?`${number(delta)} dias acima da referência`:delta<0?`${number(-delta)} dias abaixo da referência`:'Na referência: não ultrapassou o limite';
  const scope=s.duration_reference_scope==='global_fallback'?`Referência global: o produto tem ${number(s.historical_product_closed_n)} negócios encerrados, menos que o mínimo de 30.`:`Referência do produto: ${number(s.historical_product_closed_n)} negócios encerrados.`;
  result.duration={age,reference,comparison,scope,asOf:date(s.as_of),ageWidth:100*age/max,referenceWidth:100*reference/max};
  facts.push({label:'Duração calculada',value:`${number(age)} dias em ${date(s.as_of)}`});
 }
 switch(action){
  case 'identify_account':
   result.rule='Empresa ainda não identificada';
   result.summary='A oportunidade ainda não está ligada a uma empresa. Confirme esse vínculo para avaliar o perfil e dar contexto ao atendimento.';
   result.steps=[identify,s.stage==='Engaging'?status:{title:'Entenda o motivo da prospecção',question:'Qual problema essa empresa busca resolver e quem pode confirmar essa necessidade?',record:'Necessidade relatada pelo cliente e interlocutor identificado no CRM de origem.'}];
   result.limit='Cadastro incompleto não indica baixo potencial comercial. A conta só deve ser vinculada após confirmação.';
   if(result.duration&&result.duration.age>result.duration.reference)result.secondary='Há duas verificações neste caso: identificar a empresa e confirmar se a negociação continua ativa. A duração acima da referência continua relevante, mesmo com cadastro pendente.';
   break;
  case 'qualify_prospect':
   result.rule='Empresa identificada em prospecção';
   result.summary='A empresa está identificada e o estágio é de prospecção. O cadastro permite iniciar a conversa, mas não confirma a necessidade nem o interesse do cliente.';
   result.steps=[{title:'Entenda a necessidade',question:'Qual problema o cliente quer resolver e que resultado espera?',record:'Necessidade e resultado nas palavras do cliente, no CRM de origem.'},{title:'Confirme as condições de decisão',question:'Quem participa da decisão? O orçamento foi discutido ou ainda está em aberto?',record:'Participantes e situação do orçamento. Se não houver resposta, mantenha como desconhecido.'},next];
   result.limit='Empresa identificada e preço do produto não comprovam adequação, orçamento ou intenção de compra.';
   break;
  case 'review_old_negotiation':
   result.rule='Empresa identificada e duração acima da referência';
   result.summary='A duração registrada ultrapassa a referência histórica. Verifique o status atual e os obstáculos antes de decidir como continuar o atendimento.';
   result.steps=[status,{title:'Identifique o obstáculo',question:'Há uma pendência do cliente, da equipe ou de outra pessoa que impeça o avanço?',record:'Obstáculo confirmado e responsável por resolvê-lo no CRM de origem.'},next];
   result.limit='Tempo em negociação não é tempo sem contato. A comparação não indica perda, urgência ou desinteresse.';
   break;
  case 'continue_negotiation_review':
   result.rule='Negociação sem ultrapassar a referência';
   result.summary='A oportunidade está em negociação e ainda não ultrapassou a referência histórica. Confirme o compromisso mais recente e combine a próxima ação.';
   result.steps=[{title:'Recupere o último compromisso',question:'O que ficou combinado no último contato? Alguma condição mudou?',record:'Compromisso e situação confirmados no CRM de origem.'},next];
   result.limit='Estar dentro da referência não prova que a negociação está saudável. O próximo contato ainda precisa ser confirmado.';
 }
 return result;
}

export function reasonPreview(r:RecommendationInput):string{
 switch(r.decision.next_action){
  case 'identify_account':{const d=explainRecommendation(r).duration;return d&&d.age>d.reference?'Sem empresa; duração acima da referência':'Falta identificar a empresa'}
  case 'qualify_prospect':return 'Empresa identificada; prospecção';
  case 'review_old_negotiation':{const d=explainRecommendation(r).duration;return d?d.comparison:'Conferir duração e referência'}
  case 'continue_negotiation_review':return 'Confirmar o próximo compromisso';
  default:return 'Dados exigem revisão humana';
 }
}

export function conferenceSummary(r:RecommendationInput & {id:string;version:number;action_label:string;state:{product:string;catalog_price:number}}):string{
 const why=explainRecommendation(r);
 return [
  'ROTEIRO DE CONFERÊNCIA — ATENDIMENTO NÃO REGISTRADO',
  `Oportunidade: ${r.id} · versão ${r.version}`,
  `Data da base histórica: ${date(r.state.as_of)}`,
  '', 'FATOS DISPONÍVEIS',
  ...why.facts.map(f=>`${f.label}: ${f.value}`),
  `Produto: ${r.state.product}`,
  `Preço de catálogo: ${r.state.catalog_price.toLocaleString('pt-BR',{style:'currency',currency:'USD'})}`,
  ...(why.duration?[`Comparação de duração: ${why.duration.comparison}`,why.duration.scope]:[]),
  '', 'ORIENTAÇÃO DA POLÍTICA',r.action_label,why.rule,why.summary,
  ...(why.secondary?[why.secondary]:[]),why.limit,
  '', 'PERGUNTAS A CONFIRMAR — SEM RESPOSTAS REGISTRADAS',
  ...why.steps.map((s,i)=>`${i+1}. ${s.question}\n   Após confirmar, registrar: ${s.record}`),
  ...(why.missing.length?['',`Informações ausentes na base: ${why.missing.join('; ')}.`]:[]),
  '', 'Este texto não comprova contato, resposta do cliente ou compromisso combinado. Confirme os dados atuais e registre o atendimento no CRM de origem.'
 ].join('\n');
}
