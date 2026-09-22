"""Audita os recibos do ensaio sem executar novas chamadas."""
import collections
import hashlib
import json
import math
import statistics

from testar_jev_vercel import ROOT, RUN, load_key, validate_response, summarize


def main():
    records = [json.loads(line) for line in (RUN/"chamadas.jsonl").read_text(encoding="utf-8").splitlines()]
    cases = {c["case_id"]: c for c in (json.loads(line) for line in (ROOT/"resultados/casos_jev.jsonl").read_text(encoding="utf-8").splitlines())}
    questions_bytes = (ROOT/"resultados/perguntas_jev.json").read_bytes()
    questions = json.loads(questions_bytes)["questions"]
    manifest = json.loads((RUN/"manifesto.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(questions_bytes).hexdigest() == manifest["questions_sha256"]
    assert hashlib.sha256((ROOT/"resultados/casos_jev.jsonl").read_bytes()).hexdigest() == manifest["cases_sha256"]
    final = {r["case_id"]:r for r in records}
    assert set(final) == set(cases) and len(final) == 120
    by_split = collections.Counter(r["split"] for r in final.values())
    assert by_split == {"development":60,"evaluation":60}
    for r in records:
        case = cases[r["case_id"]]
        assert r["split"] == case["split"]
        assert r["expected_by_policy"] == case["expected_by_policy"]
        assert r["state"] == case["state"]
        sent = {"model":manifest["requested_model"],"state":case["state"],"questions":questions,
                "providerOptions":manifest["provider_options"]}
        assert hashlib.sha256(json.dumps(sent,ensure_ascii=False).encode("utf-8")).hexdigest() == r["request_sha256"]
        if r["http_status"] == 200:
            assert validate_response(r["response"],questions) == []
            predicted = {q:r["response"]["answers"][q]["choice"] for q in questions}
            assert r["both_correct"] == (predicted == case["expected_by_policy"])
            for q,a in r["response"]["answers"].items():
                assert a["probabilities"][a["choice"]] == max(a["probabilities"].values())
    assert all(r["http_status"]==200 and not r["validation_errors"] for r in final.values())
    key = load_key().encode("utf-8")
    for file in ROOT.rglob("*"):
        if file.is_file() and file.name != ".env":
            assert key not in file.read_bytes(), "Credencial encontrada fora do arquivo local."
    assert ".env" in (ROOT/".gitignore").read_text().splitlines()
    s = summarize(records)
    extra = {}
    for split in ["development","evaluation"]:
        rows=[r for r in final.values() if r["split"]==split]
        extra[split]={}
        for q in questions:
            confidence=[r["response"]["answers"][q]["confidence"] for r in rows]
            extra[split][q]={"confidence_min":min(confidence),"confidence_median":statistics.median(confidence),
                             "below_0_8":sum(c<.8 for c in confidence)}
        extra[split]["both_at_least_0_8"]=sum(all(r["response"]["answers"][q]["confidence"]>=.8 for q in questions) for r in rows)
    durations=[]
    for r in final.values():
        for m in r["response"]["providerMetadata"]["gateway"]["routing"].get("modelAttempts",[]):
            for a in m.get("providerAttempts",[]):
                if a.get("success"):
                    durations.append(a["endTime"]-a["startTime"])
    extra["gateway_provider_duration_ms"]={"n":len(durations),"median":statistics.median(durations)}
    checks={"status":"passed","unique_cases":120,"split_counts":dict(by_split),
            "request_hashes_verified":len(records),"policy_changed":False,
            "credential_found_outside_local_env":False,
            "checks":["source and question hashes unchanged","states and labels match prepared data",
                      "request hashes reconstructed without labels or split","response contract and chosen argmax valid",
                      "all 120 cases have final successful response","credentials absent from code/results/docs"]}
    (RUN/"verificacao.json").write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding="utf-8")
    (RUN/"diagnostico_confianca.json").write_text(json.dumps(extra,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"verification":checks,"summary":s,"confidence":extra},ensure_ascii=True))


if __name__ == "__main__":
    main()
