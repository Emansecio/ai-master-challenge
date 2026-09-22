"""Audita recibos locais contra casos, requests e configuracao congelados."""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "resultados" / "router-local-v01"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def js_number(value):
    return str(int(value)) if isinstance(value, (int, float)) and value == int(value) else str(value)


def text_for(state):
    age = "unknown" if state["age_days"] is None else js_number(state["age_days"])
    return (
        f"Account identified: {'yes' if state['account_identified'] else 'no'}. "
        f"Stage: {state['stage']}. Age days: {age}; reference days: {js_number(state['reference_p90_days'])}. "
        f"Age above reference: {'yes' if state['age_exceeds_reference_p90'] else 'no'}."
    )


def stats(rows):
    confusions = {}
    for q in ("qualification", "next_action"):
        counts = Counter((r["expected_by_policy"][q], r["outputs"][q]["predicted"]) for r in rows)
        confusions[q] = [{"expected": e, "predicted": p, "n": n} for (e, p), n in sorted(counts.items())]
    ordered = sorted(r["duration_ms"] for r in rows)
    return {
        "n": len(rows), "both_correct": sum(r["both_correct"] for r in rows),
        "question_correct": {q: sum(r["correct"][q] for r in rows) for q in confusions},
        "confusions": confusions,
        "latency_ms": {"p50_nearest_rank": ordered[math.ceil(len(rows)*.5)-1], "p95_nearest_rank": ordered[math.ceil(len(rows)*.95)-1]},
    }


def main():
    manifest = read(OUT / "manifesto.json")
    source = (ROOT / "resultados/casos_jev.jsonl").read_bytes()
    cases = {c["case_id"]: c for c in map(json.loads, source.decode().splitlines())}
    assert sha(source) == manifest["cases_sha256"]
    assert sha((ROOT / "testar_router_local.mjs").read_bytes()) == manifest["script_sha256"]
    assert sha(compact(manifest["config"]).encode()) == manifest["config_sha256"]
    for name, meta in manifest["assets"]["files"].items():
        with (ROOT / "router-assets" / name).open("rb") as source_file:
            assert hashlib.file_digest(source_file, "sha256").hexdigest() == meta["sha256"]
    seen, rows = set(), []
    for phase in ("development", "evaluation"):
        records = list(map(json.loads, (OUT / f"{phase}.jsonl").read_text(encoding="utf-8").splitlines()))
        assert len(records) == 60
        for r in records:
            assert r["case_id"] not in seen
            seen.add(r["case_id"])
            c = cases[r["case_id"]]
            assert r["split"] == c["split"] == phase
            assert r["expected_by_policy"] == c["expected_by_policy"]
            assert set(r["outputs"]) == set(manifest["config"]["questions"])
            for q, o in r["outputs"].items():
                spec = manifest["config"]["questions"][q]
                assert o["request"] == {"text": text_for(c["state"]), "cats": spec["cats"]}
                assert o["request_sha256"] == sha(compact(o["request"]).encode())
                assert len(o["probs"]) == len(spec["labels"])
                assert all(math.isfinite(p) and 0 <= p <= 1 for p in o["probs"])
                assert abs(sum(o["probs"])-1) < 1e-6
                assert o["topIndex"] == o["probs"].index(max(o["probs"]))
                assert o["predicted"] == spec["labels"][o["topIndex"]]
                assert r["correct"][q] == (o["predicted"] == c["expected_by_policy"][q])
                assert 0 < o["count"] <= 128
            assert r["both_correct"] == all(r["correct"].values())
        summary = read(OUT / f"{phase}-summary.json")
        assert summary["both_correct"] == sum(r["both_correct"] for r in records)
        assert summary["correct"] == stats(records)["question_correct"]
        for key, value in summary["frozen"].items():
            assert value == manifest[key]
        rows.extend(records)
    assert seen == set(cases)
    preflight = read(OUT / "preflight.json")
    assert len(preflight["full"]) == len(preflight["compact"]) == 240
    assert all(x["rejected"] and x["tokens"] > 128 for x in preflight["full"])
    assert all(x["tokens"] <= 128 for x in preflight["compact"])
    result = {"verified": True, "all": stats(rows)}
    for phase in ("development", "evaluation"):
        result[phase] = stats([r for r in rows if r["split"] == phase])
    result["evaluation_strata"] = []
    groups = {}
    for r in rows:
        if r["split"] != "evaluation":
            continue
        s = cases[r["case_id"]]["state"]
        key = (s["stage"], s["account_identified"], s["age_exceeds_reference_p90"])
        groups.setdefault(key, []).append(r)
    for (stage, identified, old), group in groups.items():
        result["evaluation_strata"].append({"stage": stage, "account_identified": identified, "age_above_reference": old, **stats(group)})
    (OUT / "verificacao.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verified": True, "all": {k: v for k, v in result["all"].items() if k != "confusions"}, "evaluation": result["evaluation"], "evaluation_strata": [{k: v for k, v in g.items() if k not in ("confusions", "latency_ms")} for g in result["evaluation_strata"]]}, indent=2))


if __name__ == "__main__":
    main()
