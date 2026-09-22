"""Ensaio real via endpoint oficial Vercel; sem SDK, sem respostas simuladas.

python testar_jev_vercel.py --phase smoke
python testar_jev_vercel.py --phase development
python testar_jev_vercel.py --phase evaluation

Cada fase retoma o mesmo manifesto e reaproveita chamadas concluidas.
Politica e dados nao podem mudar durante o ensaio.
"""
from __future__ import annotations

import argparse
import collections
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENDPOINT = "https://ai-gateway.vercel.sh/v1/evaluate"
MODEL = "typesafe-ai/jev"
RUN = ROOT / "resultados" / "jev-vercel-v02"
MAX_REPORTED_COST_USD = 0.05


def load_key():
    for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("AI_GATEWAY_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if key and not any(c.isspace() for c in key):
                return key
    raise ValueError("AI_GATEWAY_API_KEY ausente ou invalida no arquivo local.")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def clean(value, key):
    text = json.dumps(value, ensure_ascii=False, default=str)
    text = text.replace(key, "[REDACTED]")
    text = re.sub(r"vck_[A-Za-z0-9_-]+", "[REDACTED]", text)
    return json.loads(text)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_response(response, questions):
    answers = response.get("answers", {})
    issues = []
    if set(answers) != set(questions):
        issues.append("question_ids_mismatch")
    for name, question in questions.items():
        answer = answers.get(name, {})
        if answer.get("type") != "choice" or answer.get("choice") not in question["criteria"]:
            issues.append(f"{name}:invalid_choice")
        probabilities = answer.get("probabilities", {})
        if set(probabilities) != set(question["criteria"]):
            issues.append(f"{name}:invalid_probability_keys")
        values = list(probabilities.values())
        if not values or not all(isinstance(v, (int, float)) and math.isfinite(v) and 0 <= v <= 1 for v in values):
            issues.append(f"{name}:invalid_probabilities")
        elif abs(sum(values) - 1) > 0.02:
            issues.append(f"{name}:probabilities_do_not_sum_to_one")
    return issues


def select_cases(cases, phase):
    if phase == "smoke":
        counts = collections.Counter()
        selected = []
        for case in cases:
            if case["split"] != "development":
                continue
            s = case["state"]
            group = (s["stage"], s["account_identified"], s["age_exceeds_reference_p90"])
            if counts[group] < 2:
                selected.append(case)
                counts[group] += 1
        assert len(selected) == 12
        return selected
    return [c for c in cases if c["split"] == phase]


def number(v):
    try:
        n = float(v)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError):
        return None


def summarize(records):
    summary = {}
    groups = {"all": records,
              "development": [r for r in records if r["split"] == "development"],
              "evaluation": [r for r in records if r["split"] == "evaluation"]}
    for label, attempts in groups.items():
        if not attempts:
            continue
        group = list({r["case_id"]: r for r in attempts}.values())
        ok = [r for r in group if r["http_status"] == 200 and not r["validation_errors"]]
        latencies = sorted(r["elapsed_ms"] for r in ok) or [0]
        confusions = {}
        for q in ["qualification", "next_action"]:
            counts = collections.Counter((r["expected_by_policy"][q], r.get("actual", {}).get(q, "ERROR")) for r in group)
            confusions[q] = [{"expected": a, "actual": b, "n": n} for (a,b),n in sorted(counts.items())]
        costs = [number(r.get("response", {}).get("providerMetadata", {}).get("gateway", {}).get("cost")) for r in attempts]
        costs_known = [c for c in costs if c is not None]
        markets = [number(r.get("response", {}).get("providerMetadata", {}).get("gateway", {}).get("marketCost")) for r in attempts]
        markets_known = [c for c in markets if c is not None]
        usage = {"inputTokens": 0, "outputTokens": 0}
        for r in attempts:
            for key in usage:
                usage[key] += int(r.get("response", {}).get("usage", {}).get(key, 0) or 0)
        summary[label] = {
            "attempts": len(attempts), "unique_cases":len(group), "valid_responses": len(ok),
            "failed_attempts":sum(r["http_status"] != 200 or bool(r["validation_errors"]) for r in attempts),
            "both_correct": sum(r.get("both_correct", False) for r in group),
            "both_correct_rate": sum(r.get("both_correct", False) for r in group)/len(group),
            "question_correct": {q:sum(r.get("actual", {}).get(q)==r["expected_by_policy"][q] for r in group) for q in confusions},
            "confusions": confusions,
            "latency_ms": {"min":min(latencies), "median":statistics.median(latencies),
                           "p95_nearest_rank":latencies[math.ceil(.95*len(latencies))-1], "max":max(latencies)},
            "usage": usage, "gateway_reported_cost_usd": sum(costs_known) if costs_known else None,
            "calls_with_cost_metadata": len(costs_known),
            "gateway_reported_market_cost_usd":sum(markets_known) if markets_known else None,
            "latency_scope":"successful final response per case; retry delays not included",
        }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["smoke", "development", "evaluation"], default="smoke")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--retry-transient", action="store_true")
    parser.add_argument("--interval-seconds", type=float, default=1.0)
    args = parser.parse_args()
    key = load_key()
    cases_bytes = (ROOT/"resultados/casos_jev.jsonl").read_bytes()
    questions_bytes = (ROOT/"resultados/perguntas_jev.json").read_bytes()
    cases = [json.loads(line) for line in cases_bytes.decode("utf-8").splitlines()]
    contract = json.loads(questions_bytes)
    questions = contract["questions"]
    RUN.mkdir(parents=True, exist_ok=True)
    fixed = {"endpoint":ENDPOINT, "requested_model":MODEL, "policy_version":contract["policy_version"],
             "cases_sha256":digest(cases_bytes), "questions_sha256":digest(questions_bytes),
             "timeout_seconds":30, "automatic_retries":0, "max_reported_cost_usd":MAX_REPORTED_COST_USD,
             "provider_options":{"gateway":{"only":["typesafe-ai"]}},
             "latency_definition":"Client wall-clock HTTP round trip including connection/TLS; sequential calls, no SDK retries.",
             "model_version_note":"Gateway model alias; resolved revision recorded only if supplied by provider."}
    manifest = RUN/"manifesto.json"
    if manifest.exists():
        existing = json.loads(manifest.read_text(encoding="utf-8"))
        if any(existing.get(k) != v for k,v in fixed.items()):
            raise ValueError("Manifesto alterado. Use um novo ensaio para outra politica/configuracao.")
    else:
        manifest.write_text(json.dumps({**fixed,"started_at":datetime.now(timezone.utc).isoformat()},ensure_ascii=False,indent=2),encoding="utf-8")
    log = RUN/"chamadas.jsonl"
    records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    if not 0 <= args.interval_seconds <= 30:
        raise ValueError("Intervalo precisa estar entre 0 e 30 segundos.")
    latest = {r["case_id"]: r for r in records}
    counts = collections.Counter(r["case_id"] for r in records)
    ids = {case_id for case_id, r in latest.items()
           if not (args.retry_transient and r["http_status"] in [None,429,502,503,504] and counts[case_id] < 3)}
    if args.phase == "evaluation":
        dev = [r for r in latest.values() if r["split"] == "development"]
        if len(dev) != 60 or any(r["http_status"] != 200 or r["validation_errors"] for r in dev):
            raise ValueError("Complete a fase de desenvolvimento antes da avaliacao.")
    selected = [c for c in select_cases(cases, args.phase) if c["case_id"] not in ids]
    if args.limit is not None:
        if args.limit <= 0:
            raise ValueError("limit precisa ser positivo")
        selected = selected[:args.limit]
    opener = urllib.request.build_opener(NoRedirect)
    stopped_on_error = False
    with (RUN/"invocacoes.jsonl").open("a",encoding="utf-8") as handle:
        handle.write(json.dumps({"at":datetime.now(timezone.utc).isoformat(),"phase":args.phase,
                                 "retry_transient":args.retry_transient,"interval_seconds":args.interval_seconds,
                                 "runner_sha256":digest(Path(__file__).read_bytes())})+"\n")
    for case in selected:
        current_summary = summarize(records)
        known_cost = current_summary.get("all", {}).get("gateway_reported_cost_usd") or 0
        if known_cost >= MAX_REPORTED_COST_USD:
            raise RuntimeError("Limite local de custo reportado atingido.")
        # Somente estado e contrato; nunca rotulos, split ou chave no JSON enviado.
        payload = {"model":MODEL,"state":case["state"],"questions":questions,
                   "providerOptions":fixed["provider_options"]}
        body = json.dumps(payload,ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(ENDPOINT,data=body,method="POST",
                                         headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
        started = time.perf_counter()
        row = {"case_id":case["case_id"],"split":case["split"],"phase":args.phase,
               "timestamp":datetime.now(timezone.utc).isoformat(),"request_sha256":digest(body),
               "expected_by_policy":case["expected_by_policy"],"http_status":None,
               "validation_errors":[],"state":case["state"]}
        try:
            with opener.open(request,timeout=30) as response:
                row["http_status"] = response.status
                data = json.load(response)
            row["response"] = clean(data,key)
            row["validation_errors"] = validate_response(data,questions)
            row["actual"] = {q:data.get("answers",{}).get(q,{}).get("choice") for q in questions}
            row["both_correct"] = not row["validation_errors"] and row["actual"] == case["expected_by_policy"]
        except urllib.error.HTTPError as exc:
            row["http_status"] = exc.code
            row["error"] = clean(exc.read().decode("utf-8",errors="replace")[:2000],key)
            row["validation_errors"] = ["http_error"]
        except Exception as exc:
            row["error"] = clean(str(exc)[:1000],key)
            row["validation_errors"] = [type(exc).__name__]
        row["elapsed_ms"] = round((time.perf_counter()-started)*1000,2)
        row = clean(row,key)
        with log.open("a",encoding="utf-8") as handle:
            handle.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+"\n")
        records.append(row)
        (RUN/"resumo.json").write_text(json.dumps(summarize(records),ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps({"case_id":case["case_id"],"http_status":row["http_status"],
                          "valid":not row["validation_errors"],"both_correct":row.get("both_correct",False),
                          "elapsed_ms":row["elapsed_ms"]}),flush=True)
        if row["http_status"] != 200 or row["validation_errors"]:
            print("Lote interrompido para diagnosticar a resposta registrada.",flush=True)
            stopped_on_error = True
            break
        if args.interval_seconds:
            time.sleep(args.interval_seconds)
    print(json.dumps(summarize(records),ensure_ascii=True),flush=True)
    if stopped_on_error:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
