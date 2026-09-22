"""Verificacoes focadas na integridade dos calculos e separacao temporal."""
import csv
import io
import json
import zipfile

import numpy as np
import pandas as pd

from analisar_dados import ROOT, CUTS, audit, scored_snapshot


def main():
    archive_path = ROOT / "dados" / "crm-sales-predictive-analytics.zip"
    p, summary, _ = audit(archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        rows = list(csv.DictReader(io.TextIOWrapper(archive.open("sales_pipeline.csv"), encoding="utf-8-sig")))
    wins = [r for r in rows if r["deal_stage"] == "Won"]
    assert sum(float(r["close_value"]) for r in wins) == summary["closed_revenue"] == 10005534
    assert sum(r["deal_stage"] in ("Engaging", "Prospecting") and not r["account"] for r in rows) == 1425
    b = pd.read_csv(ROOT / "resultados" / "benchmark.csv")
    assert len(b) == 30
    assert b.precision_at_k.between(0, 1).all()
    assert b.revenue_capture.between(0, 1).all()
    score_cols = ["catalog_price", "product_rate", "product_seller_rate", "price_x_product_rate"]
    for cutoff in CUTS:
        train, live = scored_snapshot(p, cutoff)
        assert train.close_date.max() <= pd.Timestamp(cutoff)
        assert (live.engage_date <= pd.Timestamp(cutoff)).all()
        # Alterar os resultados futuros sem alterar a elegibilidade temporal
        # nao pode mudar os atributos usados para ordenar as oportunidades.
        changed = p.copy()
        future = changed.close_date > pd.Timestamp(cutoff)
        changed.loc[future, "won"] = ~changed.loc[future, "won"]
        changed.loc[future, "close_value"] = 999999999
        changed.loc[changed.close_date.isna() | future, "account"] = "UNAVAILABLE_AT_CUTOFF"
        _, alternative = scored_snapshot(changed, cutoff)
        pd.testing.assert_frame_equal(live[score_cols], alternative[score_cols])
        order_price = live.sort_values(["sales_agent", "catalog_price", "opportunity_id"], ascending=[True, False, True]).opportunity_id.tolist()
        order_weighted = live.sort_values(["sales_agent", "price_x_product_rate", "opportunity_id"], ascending=[True, False, True]).opportunity_id.tolist()
        assert order_price == order_weighted
        # Reconciliar oracle monetario com leitura padrao do CSV, sem pandas.
        end = (pd.Timestamp(cutoff) + pd.Timedelta(days=90)).strftime("%Y-%m-%d")
        independent_value = sum(float(r["close_value"]) for r in rows
                                if r["deal_stage"] == "Won" and r["engage_date"] <= cutoff
                                and cutoff < r["close_date"] <= end)
        assert live.revenue90.sum() == independent_value
        for k in (5, 10):
            subset = b[(b.cutoff == cutoff) & (b.k == k)]
            assert (subset.selected == k * live.sales_agent.nunique()).all()
            left = subset[subset.method == "catalog_price"].iloc[0]
            right = subset[subset.method == "price_x_product_rate"].iloc[0]
            assert np.isclose(left.precision_at_k, right.precision_at_k)
            assert np.isclose(left.selected_revenue90, right.selected_revenue90)
    result = {
        "status": "passed",
        "checks": ["contagens e receita reconciliadas com csv.DictReader",
                   "unicidade e integridade das ligacoes apos alias em memoria",
                   "30 combinacoes de benchmark e metricas dentro dos limites",
                   "historico de treinamento anterior ou igual a cada corte",
                   "scores invariantes a alteracoes de resultados futuros e contas atuais",
                   "receita futura do conjunto elegivel reconciliada independentemente",
                   "capacidade por vendedor e equivalencia observada dos rankings verificados"],
        "limitations": "Estas verificacoes nao provam ausencia de vies de selecao nem validade prospectiva."
    }
    (ROOT / "resultados" / "verificacao.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
