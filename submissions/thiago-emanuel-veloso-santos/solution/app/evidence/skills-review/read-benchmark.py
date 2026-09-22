"""Bounded mixed GET waves. No writes, classification requests, or old evidence overwrite."""
import concurrent.futures
import hashlib
import json
import math
import time
import urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent
APP=HERE.parents[1]
code=json.loads((APP/'.local/access-codes.json').read_text())['admin']
paths=['/api/opportunities','/api/opportunities?page=105','/api/opportunities?action=identify_account&page=2','/api/opportunities?search=SEMRESULTADO-REVISAO','/api/opportunities?sales_agent=Maureen%20Marcano','/api/meta']
def request(index):
    path=paths[index%len(paths)]
    start=time.perf_counter()
    req=urllib.request.Request('http://127.0.0.1:8766'+path,headers={'Authorization':'Bearer '+code})
    with urllib.request.urlopen(req,timeout=10) as response:
        value=json.load(response)
    duration=(time.perf_counter()-start)*1000
    keys=['rows','total','scope_total','counts','page','pages'] if 'rows' in value else ['user','filters','accounts','actions']
    digest=hashlib.sha256(json.dumps({k:value[k] for k in keys},sort_keys=True).encode()).hexdigest()
    return path,digest,duration

reference={path:digest for path,digest,_ in (request(i) for i in range(len(paths)))}
waves=[]
for clients,count in [(1,30),(35,175),(100,500)]:
    start=time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=clients) as pool:
        runs=list(pool.map(request,range(count)))
    elapsed=time.perf_counter()-start
    assert all(digest==reference[path] for path,digest,_ in runs)
    times=sorted(ms for _,_,ms in runs)
    waves.append({'clients':clients,'requests':count,'errors':0,'contract_mismatches':0,'seconds':elapsed,'p50_ms':times[math.ceil(count*.5)-1],'p95_ms':times[math.ceil(count*.95)-1],'p99_ms':times[math.ceil(count*.99)-1]})
report={'workload':'local bounded closed-loop GET waves, warmed by six reference requests','paths':paths,'waves':waves,'new_model_calls':0}
(HERE/'read-performance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(waves,indent=2))
