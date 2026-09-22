"""Verificação HTTP local. --live autoriza uma nova classificação real, sem expor códigos."""
import argparse
import concurrent.futures
import json
import math
from pathlib import Path
import time
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    base = f'http://127.0.0.1:{args.port}'
    codes = json.loads((ROOT / '.local/access-codes.json').read_text())

    def request(path, role='admin', payload=None):
        headers = {'Authorization': 'Bearer ' + codes[role]}
        data = None
        if payload is not None:
            data = json.dumps(payload).encode()
            headers['Content-Type'] = 'application/json'
        start = time.perf_counter()
        with urllib.request.urlopen(urllib.request.Request(base + path, data=data, headers=headers), timeout=30) as response:
            result = json.load(response)
        return result, (time.perf_counter() - start) * 1000

    listing, elapsed = request('/api/opportunities')
    assert listing['total'] == 2089 and len(listing['rows']) == 20
    seller, _ = request('/api/meta', 'vendedor')
    restricted, _ = request('/api/opportunities', 'vendedor')
    assert 0 < restricted['total'] < listing['total']
    assert all(r['sales_agent'] == seller['user']['scope'] for r in restricted['rows'])
    foreign = next(r for r in listing['rows'] if r['sales_agent'] != seller['user']['scope'])
    try:
        request('/api/opportunities/' + foreign['id'], 'vendedor')
        raise AssertionError('Vendedor acessou oportunidade fora da carteira')
    except urllib.error.HTTPError as exc:
        assert exc.code == 404
    report = {'port': args.port, 'open_opportunities': listing['total'], 'first_page_ms': elapsed,
              'seller_scope_verified': True, 'live_executed': False, 'load': []}
    for concurrency in (35, 100):
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
            runs = list(pool.map(lambda _: request('/api/opportunities'), range(concurrency)))
        assert all(result['total'] == 2089 and len(result['rows']) == 20 for result, _ in runs)
        times = sorted(duration for _, duration in runs)
        report['load'].append({'concurrent_clients': concurrency, 'requests': len(runs), 'errors': 0,
                               'p50_ms': times[math.ceil(len(times)*.5)-1], 'p95_ms': times[math.ceil(len(times)*.95)-1]})
    if args.live:
        row = next(r for r in listing['rows'] if r['status'] == 'unclassified')
        job, _ = request('/api/classify', payload={'id': row['id'], 'version': row['version']})
        assert job['status'] in ('pending', 'running')
        start = time.perf_counter()
        while time.perf_counter() - start < 120:
            current, _ = request('/api/opportunities/' + row['id'])
            if current['status'] == 'classified':
                break
            if current['status'] == 'failed':
                raise AssertionError(current.get('error'))
            time.sleep(1)
        assert current['status'] == 'classified', current['status']
        assert current['classification']['model'] == 'typesafe-ai/jev'
        assert current['classification']['answers']['qualification']['choice'] == current['decision']['qualification']
        assert current['classification']['answers']['next_action']['choice'] == current['decision']['next_action']
        cached, cached_ms = request('/api/classify', payload={'id': row['id'], 'version': row['version']})
        assert cached['status'] == 'cached'
        report.update(live_executed=True, live_case_id=row['id'], job_id=job['id'], classified=True,
                      reused_without_new_job=True, cached_request_ms=cached_ms)
    destination = ROOT / 'evidence'
    destination.mkdir(exist_ok=True)
    (destination / ('http-live.json' if args.live else 'http-load.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
