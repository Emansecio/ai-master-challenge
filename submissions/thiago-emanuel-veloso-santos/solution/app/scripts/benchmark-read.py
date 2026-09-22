"""Carga local de leitura com contratos verificados; sem inferências ou mutações."""
import argparse
import concurrent.futures
import hashlib
import json
import math
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PATHS = ['/api/opportunities', '/api/opportunities?page=50',
         '/api/opportunities?action=identify_account&page=2',
         '/api/opportunities?search=ZZZ-SEM-RESULTADO',
         '/api/opportunities?sales_agent=Maureen%20Marcano', '/api/meta']

def contract(value):
    if 'rows' in value:
        return {k: value[k] for k in ['rows', 'total', 'scope_total', 'counts', 'page', 'pages']}
    return {k: value[k] for k in ['user', 'filters', 'accounts', 'actions']}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['before', 'after'])
    args = parser.parse_args()
    code = json.loads((ROOT / '.local/access-codes.json').read_text())['admin']
    def request(index):
        path = PATHS[index % len(PATHS)]
        start = time.perf_counter()
        req = urllib.request.Request('http://127.0.0.1:8766' + path, headers={'Authorization': 'Bearer ' + code})
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
        digest = hashlib.sha256(json.dumps(contract(json.loads(raw)), sort_keys=True).encode()).hexdigest()
        return path, digest, (time.perf_counter()-start)*1000, len(raw)
    reference = {p: d for p, d, _, _ in (request(i) for i in range(len(PATHS)))}
    before = ROOT / 'evidence/performance-before.json'
    if args.phase == 'after':
        assert reference == json.loads(before.read_text())['contracts'], 'API contract changed'
    results = []
    for clients in [1, 35, 100]:
        count = 30 if clients == 1 else clients * 5
        start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=clients) as pool:
            runs = list(pool.map(request, range(count)))
        elapsed = time.perf_counter()-start
        assert all(reference[p] == digest for p, digest, _, _ in runs)
        times = sorted(ms for _, _, ms, _ in runs)
        results.append(dict(clients=clients, requests=count, errors=0, elapsed_seconds=elapsed,
                            throughput_rps=count/elapsed, p50_ms=times[math.ceil(count*.5)-1],
                            p95_ms=times[math.ceil(count*.95)-1], p99_ms=times[math.ceil(count*.99)-1]))
    report = dict(phase=args.phase, workload='closed-loop mixed GET, fixed 30/175/500 requests; local machine',
                  paths=PATHS, contracts=reference, results=results, new_model_calls=0)
    start = time.perf_counter()
    def sustained(worker):
        runs = []
        index = worker
        while time.perf_counter() - start < 30:
            runs.append(request(index))
            index += 1
        return runs
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as pool:
        runs = [r for group in pool.map(sustained, range(100)) for r in group]
    elapsed = time.perf_counter() - start
    assert all(reference[p] == digest for p, digest, _, _ in runs)
    times = sorted(ms for _, _, ms, _ in runs)
    report['sustained'] = dict(clients=100, target_seconds=30, actual_seconds=elapsed, requests=len(runs),
                              errors=0, p95_ms=times[math.ceil(len(times)*.95)-1], throughput_rps=len(runs)/elapsed)
    (ROOT / f'evidence/performance-{args.phase}.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'waves': results, 'sustained': report['sustained']}, indent=2))

if __name__ == '__main__':
    main()
