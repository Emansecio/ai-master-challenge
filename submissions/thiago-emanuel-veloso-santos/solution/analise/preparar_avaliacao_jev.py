"""Prepara casos reais e respostas de referencia da politica, sem chamar o Jev.

As respostas sao um oraculo deterministico de aderencia a regras propostas.
Nao sao anotacoes humanas nem rotulos de sucesso comercial.
"""
import json

import numpy as np
import pandas as pd

from analisar_dados import ROOT, AS_OF, SEED, audit


QUESTIONS = {
    "qualification": {
        "type": "choice",
        "instructions": "Classifique a situacao de qualificacao usando apenas os fatos fornecidos. Conta ausente: incomplete_profile. Conta presente em Prospecting: discovery_required. Conta presente em Engaging: negotiation_reviewable. Estas classes nao significam intencao de compra nem probabilidade de ganhar. Se o estado violar o contrato ou apresentar contradicao que impeça a escolha: human_review.",
        "criteria": {
            "incomplete_profile": "A conta nao esta identificada; faltam atributos para qualificacao do perfil.",
            "discovery_required": "Conta identificada, oportunidade em Prospecting; necessidades comerciais nao estao registradas.",
            "negotiation_reviewable": "Conta identificada e estagio Engaging; existe contexto cadastral para revisar a negociacao, sem afirmar adequacao ou intencao.",
            "human_review": "Estado invalido, contraditorio ou fora das classes previstas; nao inferir uma classe comercial."
        }
    },
    "next_action": {
        "type": "choice",
        "instructions": "Escolha a proxima acao segundo esta precedencia: estado invalido ou contraditorio -> human_review; conta ausente -> identify_account; conta presente em Prospecting -> qualify_prospect; conta presente em Engaging com age_exceeds_reference_p90=true -> review_old_negotiation; demais Engaging validos -> continue_negotiation_review. P90 e apenas referencia descritiva, nao SLA, urgencia ou inatividade. Nao contatar clientes ou alterar o CRM.",
        "criteria": {
            "identify_account": "Confirmar ou vincular a empresa ao registro antes de qualificar seu perfil.",
            "qualify_prospect": "Levantar necessidade, interlocutor e proximo passo; nao presumir essas informacoes.",
            "review_old_negotiation": "Verificar o status atual de negociacao que ultrapassou a referencia historica de duracao.",
            "continue_negotiation_review": "Revisar o proximo passo comercial; nao ha alerta de idade pela regra atual.",
            "human_review": "A inconsistencia do estado impede aplicar a politica."
        }
    }
}


def main():
    p, summary, _ = audit(ROOT / "dados" / "crm-sales-predictive-analytics.zip")
    o = p[p.is_open].copy()
    o["age"] = (AS_OF-o.engage_date).dt.days
    stats = summary["duration_by_product"]
    global_p90 = summary["duration_closed"]["90%"]
    o["ref"] = o["product"].map(lambda x: stats[x]["p90"] if stats[x]["n"] >= 30 else global_p90)
    o["old"] = o.age > o.ref
    o["known"] = o.account.notna()
    cases = []
    for (stage, known, old), block in o.groupby(["deal_stage", "known", "old"]):
        sample = block.sample(n=20, random_state=SEED)
        for i, row in enumerate(sample.itertuples(index=False)):
            qualification = "incomplete_profile" if not known else "discovery_required" if stage == "Prospecting" else "negotiation_reviewable"
            action = "identify_account" if not known else "qualify_prospect" if stage == "Prospecting" else "review_old_negotiation" if old else "continue_negotiation_review"
            facts = {
                "as_of": str(AS_OF.date()), "stage": stage, "account_identified": bool(known),
                "engage_date": None if pd.isna(row.engage_date) else str(row.engage_date.date()),
                "age_days": None if pd.isna(row.age) else int(row.age),
                "product": row.product, "catalog_price": int(row.sales_price),
                "reference_p90_days": float(row.ref), "age_exceeds_reference_p90": bool(old),
                "historical_product_closed_n": int(stats[row.product]["n"]),
                "duration_reference_scope": "product" if stats[row.product]["n"] >= 30 else "global_fallback",
                "unavailable": ["need", "budget", "authority", "intent", "last_contact", "next_contact_date"]
            }
            cases.append({"case_id": row.opportunity_id, "split": "development" if i < 10 else "evaluation",
                          "policy_version": "0.2-proposed", "source_kind": "real_dataset",
                          "state": facts, "expected_by_policy": {"qualification": qualification, "next_action": action}})
    assert len(cases) == 120 and len({x["case_id"] for x in cases}) == 120
    assert sum(c["split"] == "evaluation" for c in cases) == 60
    assert all("close_value" not in c["state"] and "close_date" not in c["state"] for c in cases)
    out = ROOT / "resultados"
    (out / "casos_jev.jsonl").write_text("".join(json.dumps(c,ensure_ascii=False,allow_nan=False)+"\n" for c in cases),encoding="utf-8")
    contract = {"policy_version": "0.2-proposed", "questions": QUESTIONS,
                "note": "Questions para futura integracao. Nenhuma chamada executada. Provider e versao de modelo devem ser fixados no ensaio. Nao enviar expected_by_policy nem split ao modelo."}
    (out / "perguntas_jev.json").write_text(json.dumps(contract,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"real_cases":len(cases),"development":60,"evaluation":60,"strata":6,"live_calls":0}))


if __name__ == "__main__":
    main()
