"""Revisão reproduzível: lê recibos e API local; não altera dados nem chama Jev."""
import hashlib
import json
from pathlib import Path
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / 'analise/resultados'
SELECTION = [
    ('DB801ISB', 'Sem conta, negociação recente', 'Nove dias não demonstram urgência. Identificar a empresa é um requisito de cadastro, não um julgamento sobre a qualidade do cliente.'),
    ('197EQMY8', 'Sem conta, exatamente no P90', 'A idade igual ao P90 não ultrapassa a referência. A falta de conta prevalece; vincular uma empresa sem confirmação produziria uma classificação apoiada em dado falso.'),
    ('A7SA2L21', 'Sem conta, longa duração e produto raro', 'O preço alto não prova potencial de receita. A referência é global por falta de histórico suficiente do produto. Completar cadastro sozinho não resolve a necessidade de confirmar se a negociação continua ativa.'),
    ('0E8D6TCQ', 'Sem conta, prospecção', 'Não existe data de início para medir duração. Primeiro confirmar empresa e responsável, sem selecionar uma conta apenas para liberar a qualificação.'),
    ('DDHNCZMO', 'Com conta, prospecção de maior preço', 'A empresa identificada não confirma necessidade nem orçamento. O desempate por preço favorece este produto, mas não comprova melhor retorno por hora do vendedor.'),
    ('E6DGJSDW', 'Com conta, prospecção de menor preço', 'O baixo preço não justifica descartar o cliente. Sem quantidade, recorrência e esforço comercial, não é possível estimar o valor total da oportunidade.'),
    ('K9KGXL2E', 'Com conta, negociação recente', 'Estar abaixo da referência não prova que o negócio está saudável. Confirmar compromisso e data do próximo contato continua necessário.'),
    ('PSMWYTMB', 'Com conta, perto do P90', 'Dois dias abaixo do limite não estabelecem uma diferença comercial relevante. O limite orienta uma fila, mas não é um prazo prometido pelo cliente.'),
    ('7GDSUY9K', 'Com conta, acima do P90', 'A ultrapassagem pede checagem de status e obstáculos. Não autoriza tratar o cliente como perdido ou impor urgência comercial.'),
    ('QP006VDE', 'Com conta, duração elevada', 'A regra coloca negócios antigos antes dos demais. Isso pode concentrar esforço em negócios sem atividade; a base não permite comprovar nem refutar esse risco.'),
]


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def baseline(s):
    # Os 120 estados auditados são válidos; revisão humana não foi exercitada nesse ensaio.
    if not s['account_identified']:
        return {'qualification': 'incomplete_profile', 'next_action': 'identify_account'}
    if s['stage'] == 'Prospecting':
        return {'qualification': 'discovery_required', 'next_action': 'qualify_prospect'}
    return {'qualification': 'negotiation_reviewable', 'next_action':
            'review_old_negotiation' if s['age_days'] > s['reference_p90_days'] else 'continue_negotiation_review'}


def main():
    cases = {c['case_id']: c for c in read_jsonl(RESULTS / 'casos_jev.jsonl')}
    receipts_path = RESULTS / 'jev-vercel-v02/chamadas.jsonl'
    attempts = read_jsonl(receipts_path)
    receipts = {r['case_id']: r for r in attempts if r['http_status'] == 200}
    assert len(cases) == len(receipts) == 120
    agreement = {}
    for split in ('development', 'evaluation'):
        group = [c for c in cases.values() if c['split'] == split]
        local_correct = jev_correct = same = 0
        for c in group:
            r = receipts[c['case_id']]
            assert r['state'] == c['state'] and not r['validation_errors']
            local = baseline(c['state'])
            actual = {q: a['choice'] for q, a in r['response']['answers'].items()}
            local_correct += local == c['expected_by_policy']
            jev_correct += actual == c['expected_by_policy']
            same += local == actual
        agreement[split] = dict(n=len(group), local_correct=local_correct, jev_correct=jev_correct, same=same)
        assert local_correct == jev_correct == same == len(group)

    code = json.loads((ROOT / 'app/.local/access-codes.json').read_text())['admin']
    def get(path):
        req = urllib.request.Request('http://127.0.0.1:8766' + path, headers={'Authorization': 'Bearer ' + code})
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)

    listing = get('/api/opportunities')
    selected = []
    for identifier, rationale, critique in SELECTION:
        row = get('/api/opportunities/' + identifier)
        case, receipt = cases[identifier], receipts[identifier]
        assert case['split'] == 'evaluation'
        assert row['state'] == case['state'] and row['decision'] == case['expected_by_policy']
        assert row['classification']['answers'] == receipt['response']['answers']
        selected.append(dict(selection_reason=rationale, technical_business_review=critique,
                             human_validation='pending', opportunity=row,
                             receipt_timestamp=receipt['timestamp'], new_inference=False))
    strata = {(r['opportunity']['state']['account_identified'], r['opportunity']['state']['stage'],
               r['opportunity']['state']['age_exceeds_reference_p90']) for r in selected}
    assert len(selected) == 10 and len(strata) == 6
    report = dict(generated_at=datetime.now(timezone.utc).isoformat(), scope='technical_business_desk_review',
                  selection='purposeful coverage of six audited strata and four boundary/value cases; not random',
                  source_receipts_sha256=hashlib.sha256(receipts_path.read_bytes()).hexdigest(),
                  human_validation=False, new_model_calls=0, total_open=listing['scope_total'],
                  queues=listing['counts'], agreement=agreement, cases=selected)
    (ROOT / 'app/evidence/business-review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    lines = ['# Revisão de dez oportunidades reais', '',
             'Revisão técnica e de negócio assistida por IA em 22/09/2026. **Não é validação por vendedor.**', '',
             'Seleção intencional entre os 60 casos de avaliação já classificados pelo Jev: cobre os seis estratos (conta, estágio e duração), além de limites e contrastes de preço. Não é amostra aleatória nem estimativa da qualidade de toda a carteira. Os registros vêm do dataset histórico; “reais” não significa clientes atuais da G4.', '',
             'As dez respostas já existiam. Foram confrontadas com o estado atual da API e os recibos originais; não houve nova inferência ou edição de oportunidades.', '']
    for i, item in enumerate(selected, 1):
        r, s = item['opportunity'], item['opportunity']['state']
        age = 'indisponível' if s['age_days'] is None else f"{s['age_days']} dias"
        ref = 'global' if s['duration_reference_scope'] == 'global_fallback' else 'por produto'
        confidence = ' / '.join(f"{a['confidence']:.0%}" for q, a in sorted(r['classification']['answers'].items()))
        lines += [f"## {i}. {r['id']} — {item['selection_reason']}", '',
                  f"**Fatos:** {r['account'] or 'empresa não vinculada'}; vendedor {r['sales_agent']}; {s['stage']}; {s['product']}; preço de catálogo US$ {s['catalog_price']:,}. Idade: {age}; P90 {s['reference_p90_days']:g} dias ({ref}; {s['historical_product_closed_n']} encerrados do produto).", '',
                  f"**Orientação atual:** {r['action_label']}. Qualificação: {r['qualification_label']}. Jev e regra local concordam nas duas respostas. Confianças próxima ação / qualificação: {confidence}; não medem chance de fechamento.", '',
                  f"**Avaliação crítica:** {item['technical_business_review']}", '',
                  '**Validação humana pendente:** o responsável concorda com esta ação? Qual fato falta? Qual ação faria primeiro e por quê? Qual informação precisa ser registrada antes da decisão?', '']
    lines += ['## Conclusão da revisão', '',
              'As dez orientações são coerentes com a política e com os fatos limitados disponíveis. Essa coerência não demonstra que a ordem maximiza vendas. Em especial, o caso A7SA2L21 mostra que corrigir cadastro e verificar status podem ser necessários na mesma oportunidade. A interface deve apoiar as duas verificações, sem alterar a política sem evidência.', '',
              'Problemas confirmados na interface anterior: rótulo “Jev validado” não explicitava o objeto da validação; a referência global não era distinguida da referência do produto no detalhe; havia orientação geral, mas não perguntas práticas por ação; a proporção sem empresa vinculada exigia cálculo pelo usuário.', '',
              'Resultado: tornar explícita a concordância com a política, mostrar origem e tamanho do histórico do produto, oferecer roteiro de conferência e dar acesso direto à fila de cadastro. A ordenação e os contratos de classificação permanecem iguais.', '',
              'Reprodução: com a aplicação local ativa, executar `python app/scripts/review-business.py` na raiz. O script falha se os dez estados ou respostas divergirem dos recibos; alterações futuras exigem nova revisão identificada.', '',
              'Evidências: [JSON da revisão](../app/evidence/business-review.json) e [avaliação da contribuição do Jev](CONTRIBUICAO-JEV.md).', '']
    (ROOT / 'analise/REVISAO-COMERCIAL-10-CASOS.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'reviewed': len(selected), 'strata': len(strata), 'agreement': agreement,
                      'new_model_calls': 0, 'human_validation': False, 'total_open': listing['scope_total']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
