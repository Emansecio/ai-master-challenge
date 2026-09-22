"""Auditoria e benchmarks exploratorios; nao implementa o produto nem chama modelos.

Requer pandas e numpy. Leia AVALIACAO-TECNICA.md antes de interpretar resultados.
Execucao: python analisar_dados.py [--zip caminho.zip] [--output diretorio]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import platform
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
EXPECTED_SHA256 = "74d535826330b616758ebb6bb393abf701a5126364a72fbe71003cb6a7a87a9c"
AS_OF = pd.Timestamp("2017-12-31")  # Hipotese explicita, nao data de extracao confirmada.
CUTS = ["2017-03-31", "2017-06-30", "2017-09-30"]
HORIZON_DAYS = 90
PRIOR_STRENGTH = 20  # Parametro de comparacao fixado, nao ajustado aos resultados.
SEED = 22092026


def native(v):
    if isinstance(v, (np.integer, np.floating)):
        return v.item()
    if isinstance(v, (pd.Timestamp, Path)):
        return str(v)
    raise TypeError(type(v).__name__)


def wilson(wins, n):
    z = 1.96
    rate = wins / n
    den = 1 + z * z / n
    center = (rate + z * z / (2 * n)) / den
    radius = z * np.sqrt(rate * (1 - rate) / n + z * z / (4 * n * n)) / den
    return [float(center - radius), float(center + radius)]


def group_history(frame, key):
    g = frame.groupby(key).agg(n=("won", "size"), wins=("won", "sum"))
    g["win_rate"] = g.wins / g.n
    g["wilson95"] = [wilson(w, n) for w, n in zip(g.wins, g.n)]
    return g.to_dict(orient="index")


def smooth_rates(frame, key, prior):
    g = frame.groupby(key).won.agg(["sum", "count"])
    return (g["sum"] + PRIOR_STRENGTH * prior) / (g["count"] + PRIOR_STRENGTH)


def scored_snapshot(p, cutoff):
    """Features por produto/vendedor; conta atual nao entra no ranking historico.

    Reconstituicao parcial: assumimos produto/vendedor imutaveis. Nao existe
    log de mudancas para provar isso. Prospeccoes sem data ficam excluidas.
    """
    at = pd.Timestamp(cutoff)
    end = at + pd.Timedelta(days=HORIZON_DAYS)
    assert end <= AS_OF
    train = p[p.close_date.notna() & p.close_date.le(at)].copy()
    live = p[p.engage_date.le(at) & (p.close_date.isna() | p.close_date.gt(at))].copy()
    assert set(train.opportunity_id).isdisjoint(live.opportunity_id)
    prior = train.won.mean()
    prod = smooth_rates(train, "product", prior)
    seller = smooth_rates(train, "sales_agent", prior)
    pairs = train.groupby(["product", "sales_agent"]).won.agg(["sum", "count"])
    live["product_rate"] = live["product"].map(prod).fillna(prior)
    live["seller_rate"] = live.sales_agent.map(seller).fillna(prior)
    live["product_seller_rate"] = [
        (pairs.loc[(product, seller_name), "sum"] + PRIOR_STRENGTH * base)
        / (pairs.loc[(product, seller_name), "count"] + PRIOR_STRENGTH)
        if (product, seller_name) in pairs.index else base
        for product, seller_name, base in zip(live["product"], live.sales_agent, live.product_rate)
    ]
    live["catalog_price"] = live.sales_price
    live["price_x_product_rate"] = live.sales_price * live.product_rate
    # Oraculo de avaliacao: valores futuros nao sao passados aos scorers acima.
    live["win90"] = live.won & live.close_date.gt(at) & live.close_date.le(end)
    live["revenue90"] = np.where(live.win90, live.close_value, 0.0)
    live["age_days"] = (at - live.engage_date).dt.days
    return train, live


def benchmark(p):
    rows, seller_rows, sensitivity = [], [], []
    methods = ["catalog_price", "product_rate", "product_seller_rate", "price_x_product_rate"]
    # Ordenacao SHA por ID para desempate reproduzivel, sem recorrer ao resultado.
    # Repeticoes com outros desempates medem a fragilidade de rankings discretos.
    for cutoff in CUTS:
        train, live = scored_snapshot(p, cutoff)
        for k in [5, 10]:
            totals = {m: [0, 0.0, 0.0] for m in methods + ["random_expectation"]}
            for seller_name, block in live.groupby("sales_agent"):
                take = min(k, len(block))
                block = block.copy()
                block["tie"] = block.opportunity_id.map(
                    lambda x: hashlib.sha256(f"{SEED}:{x}".encode()).hexdigest()
                )
                for method in methods:
                    selected = block.sort_values([method, "tie"], ascending=[False, True]).head(take)
                    wins, revenue = float(selected.win90.sum()), float(selected.revenue90.sum())
                    totals[method] = [totals[method][0] + take, totals[method][1] + wins, totals[method][2] + revenue]
                    seller_rows.append(dict(cutoff=cutoff, k=k, seller=seller_name, method=method,
                                            selected=take, wins90=wins, revenue90=revenue))
                expected_wins = take * block.win90.mean()
                expected_revenue = take * block.revenue90.mean()
                totals["random_expectation"][0] += take
                totals["random_expectation"][1] += expected_wins
                totals["random_expectation"][2] += expected_revenue
                seller_rows.append(dict(cutoff=cutoff, k=k, seller=seller_name,
                                        method="random_expectation", selected=take,
                                        wins90=expected_wins, revenue90=expected_revenue))
            for method, (n, wins, revenue) in totals.items():
                rows.append(dict(cutoff=cutoff, horizon_days=HORIZON_DAYS, k=k, method=method,
                                 train_closed=len(train), eligible=len(live), selected=n,
                                 portfolio_win90=float(live.win90.mean()), precision_at_k=wins/n,
                                 wins90=wins, selected_revenue90=revenue,
                                 revenue_capture=revenue/live.revenue90.sum()))
            for method in methods:
                values = []
                for seed in range(30):
                    shuffled = live.sample(frac=1, random_state=SEED + seed)
                    ranked = shuffled.sort_values(method, ascending=False, kind="stable")
                    selected = ranked.groupby("sales_agent", sort=False).head(k)
                    values.append(float(selected.win90.mean()))
                sensitivity.append(dict(cutoff=cutoff, k=k, method=method,
                                        precision_tie_min=min(values), precision_tie_max=max(values)))
    detail = pd.DataFrame(seller_rows)
    comparisons = []
    for cutoff in CUTS:
        d = detail[(detail.cutoff == cutoff) & (detail.k == 5)]
        for method in ["product_rate", "product_seller_rate", "price_x_product_rate"]:
            one = d[d.method == method].set_index("seller")
            base = d[d.method == "catalog_price"].set_index("seller").loc[one.index]
            diff = (one.wins90 - base.wins90).to_numpy()
            count = one.selected.to_numpy()
            rng = np.random.default_rng(SEED)
            ix = rng.integers(0, len(diff), size=(2000, len(diff)))
            boot = diff[ix].sum(axis=1) / count[ix].sum(axis=1)
            comparisons.append(dict(cutoff=cutoff, k=5, method=method, reference="catalog_price",
                                    precision_delta=float(diff.sum()/count.sum()),
                                    cluster_bootstrap95=np.quantile(boot, [0.025, 0.975]).tolist()))
    return pd.DataFrame(rows), detail, sensitivity, comparisons


def audit(zip_path):
    payload = zip_path.read_bytes()
    sha = hashlib.sha256(payload).hexdigest()
    if sha != EXPECTED_SHA256:
        raise ValueError("Arquivo diferente da versao auditada; revise a proveniencia antes de comparar.")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        tables = {n: pd.read_csv(archive.open(n)) for n in
                  ["accounts.csv", "products.csv", "sales_teams.csv", "sales_pipeline.csv", "metadata.csv"]}
        independent = list(csv.DictReader(io.TextIOWrapper(archive.open("sales_pipeline.csv"), encoding="utf-8-sig")))
        file_hashes = {n: hashlib.sha256(archive.read(n)).hexdigest() for n in tables}
    raw = tables["sales_pipeline.csv"]
    p = raw.copy()
    p["product"] = p["product"].replace({"GTXPro": "GTX Pro"})
    for col in ["engage_date", "close_date"]:
        p[col] = pd.to_datetime(p[col], errors="raise")
    p["won"] = p.deal_stage.eq("Won")
    p["is_open"] = p.deal_stage.isin(["Engaging", "Prospecting"])
    p["duration"] = (p.close_date-p.engage_date).dt.days
    p = p.merge(tables["products.csv"], on="product", how="left", validate="many_to_one")
    a = tables["accounts.csv"]
    c = p[~p.is_open].copy()
    o = p[p.is_open].copy()
    o["age"] = (AS_OF-o.engage_date).dt.days
    assert len(p) == len(raw) == len(independent) == 8800
    assert p.opportunity_id.is_unique
    assert not p.sales_price.isna().any()
    assert set(p.sales_agent) <= set(tables["sales_teams.csv"].sales_agent)
    assert set(p.account.dropna()) <= set(a.account)
    assert (c.duration >= 0).all()
    assert c.close_value.notna().all() and o.close_value.isna().all()
    assert sum(r["deal_stage"] in ["Engaging", "Prospecting"] for r in independent) == len(o)
    assert sum(not r["account"] for r in independent) == int(p.account.isna().sum())
    by_prod = c.groupby("product").duration.agg(["size", "median", lambda s:s.quantile(.9), "max"])
    by_prod.columns = ["n", "median", "p90", "max"]
    fallback_p90 = c.duration.quantile(.9)
    o["reference_p90"] = o["product"].map(by_prod.p90.where(by_prod.n >= 30, fallback_p90))
    o["review_age"] = o.age > o.reference_p90
    summary = {
        "provenance": {"source": "https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics",
                       "download_endpoint": "https://www.kaggle.com/api/v1/datasets/download/agungpambudi/crm-sales-predictive-analytics",
                       "download_date_local": "2026-09-22", "zip_sha256": sha, "file_sha256": file_hashes,
                       "as_of_assumption": str(AS_OF.date()), "python": platform.python_version(),
                       "pandas": pd.__version__, "numpy": np.__version__},
        "tables": {n: {"rows": len(d), "columns": list(d.columns), "missing": d.isna().sum().to_dict(),
                       "duplicate_rows": int(d.duplicated().sum())} for n,d in tables.items()},
        "stage_counts": p.deal_stage.value_counts().to_dict(),
        "open_by_stage_account": o.groupby(["deal_stage", o.account.notna().rename("account_known")]).size().reset_index(name="n").to_dict(orient="records"),
        "alias_records": int(raw["product"].eq("GTXPro").sum()),
        "closed_product_history": group_history(c, "product"),
        "closed_sector_history": group_history(c.merge(a, on="account", validate="many_to_one"), "sector"),
        "closed_by_quarter": group_history(c.assign(quarter=c.close_date.dt.to_period("Q").astype(str)), "quarter"),
        "duration_closed": c.duration.describe(percentiles=[.5,.75,.9,.95]).to_dict(),
        "duration_by_product": by_prod.to_dict(orient="index"),
        "open_age": o.age.describe(percentiles=[.5,.75,.9,.95]).to_dict(),
        "open_beyond_max_closed": int((o.age > c.duration.max()).sum()),
        "review_age_over_p90": int(o.review_age.sum()),
        "over_p90_by_account": o.groupby(o.account.notna()).review_age.sum().to_dict(),
        "teams_total": len(tables["sales_teams.csv"]), "agents_with_deals": p.sales_agent.nunique(),
        "unique_open_accounts": o.account.nunique(),
        "closed_revenue": float(c.close_value.sum()),
        "unknown_account_closed": int(c.account.isna().sum()),
    }
    # Distinguir estado original do resultado do comparador deterministico.
    o["reference_action"] = np.select(
        [o.account.isna(), o.deal_stage.eq("Prospecting"), o.review_age],
        ["identify_account", "qualify_prospect", "review_old_negotiation"],
        default="continue_negotiation_review")
    summary["reference_action_counts"] = o.reference_action.value_counts().to_dict()
    # Amostra real deterministica cobrindo estado, ausencia e idade; sem rotulos Jev.
    o["account_known"] = o.account.notna()
    samples = o.sort_values("opportunity_id").groupby(
        ["deal_stage", "account_known", "review_age"], dropna=False).head(2)
    samples = samples[["opportunity_id", "sales_agent", "product", "account", "deal_stage",
                       "engage_date", "age", "sales_price", "reference_p90", "review_age", "reference_action"]]
    summary["methodology"] = {
        "cutoffs": CUTS, "horizon_days": HORIZON_DAYS, "prior_strength": PRIOR_STRENGTH,
        "k_per_seller": [5,10], "seed": SEED, "tie_sensitivity_seeds": 30,
        "bootstrap_clusters": "seller", "bootstrap_repetitions": 2000,
        "warnings": ["Exploratory retrospective stress test, not a prospective holdout.",
                     "Future account completeness cannot be reconstructed; excluded from scorers.",
                     "Products and assignments assumed unchanged; no change log available.",
                     "Observation through 2017-12-31 assumed, not source-confirmed.",
                     "No observed win within 90 days is not equivalent to eventual Lost.",
                     "Revenue capture is retrospective coverage, not causal uplift or ROI.",
                     "Same opportunities can appear in multiple cutoffs; do not pool independent samples.",
                     "Won rate among closed deals is not calibrated 90-day win probability for open deals."]}
    return p, summary, samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, default=ROOT/"dados"/"crm-sales-predictive-analytics.zip")
    parser.add_argument("--output", type=Path, default=ROOT/"resultados")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    p, summary, examples = audit(args.zip)
    results, per_seller, sensitivity, intervals = benchmark(p)
    summary["tie_sensitivity"] = sensitivity
    summary["bootstrap_comparisons"] = intervals
    (args.output/"auditoria.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False,
                                                         default=native, allow_nan=False), encoding="utf-8")
    results.to_csv(args.output/"benchmark.csv", index=False)
    per_seller.to_csv(args.output/"benchmark_por_vendedor.csv", index=False)
    examples.to_csv(args.output/"exemplos_reais.csv", index=False)
    print(json.dumps({k:summary[k] for k in ["stage_counts", "open_beyond_max_closed", "review_age_over_p90",
                                             "reference_action_counts", "duration_closed", "open_age"]},default=native))
    print(results[results.k.eq(5)].to_string(index=False))
    print(json.dumps(intervals, default=native))


if __name__ == "__main__":
    main()
