"""Read-only metadata and exact page-query plans using the application database role."""
import json
import re
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
APP=HERE.parents[1]
def sql(statement):
    result=subprocess.run(['docker','exec','-i','g4-leaddesk-db-1','psql','-U','leadadmin','-d','leaddesk','-X','-q','-A','-t','-v','ON_ERROR_STOP=1'],input=statement,text=True,capture_output=True,check=True)
    return result.stdout.strip()

source=(APP/'internal/store/read.go').read_text()
scope=re.search(r'const scopedWhere = `([^`]+)`',source).group(1)
order=re.search(r'const pageOrder = `([^`]+)`',source).group(1)
query=re.search(r'query := `(.*?)`\s*\n\terr := s.DB.QueryRow',source,re.S).group(1)
query=query.replace('` + scopedWhere + `',scope).replace('` + pageOrder + `',order)
assert '`' not in query and query.startswith('WITH candidates')

cases=[('admin-first',['admin','','','','','','',1]),('admin-last',['admin','','','','','','',105]),('seller',['seller','Maureen Marcano','','','','','',1]),('region',['admin','','','','East','','',1]),('search',['admin','','','','','Acme','',1])]
plans=[]
for name,args in cases:
    values=','.join(str(v) if isinstance(v,int) else "'"+v.replace("'","''")+"'" for v in args)
    command='BEGIN READ ONLY; SET LOCAL ROLE leaddesk; SET LOCAL statement_timeout=5000; PREPARE review_page(text,text,text,text,text,text,text,int) AS '+query+'; EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) EXECUTE review_page('+values+'); ROLLBACK;'
    plan=json.loads(sql(command))[0]
    (HERE/('plan-'+name+'.json')).write_text(json.dumps(plan,indent=2),encoding='utf-8')
    def nodes(n):
        yield n
        for child in n.get('Plans',[]):
            yield from nodes(child)
    indexes=sorted({n['Index Name'] for n in nodes(plan['Plan']) if 'Index Name' in n})
    plans.append({'case':name,'execution_ms':plan['Execution Time'],'planning_ms':plan['Planning Time'],'indexes':indexes,'disk_sorts':[n.get('Sort Space Used') for n in nodes(plan['Plan']) if n.get('Sort Space Type')=='Disk']})

metadata=json.loads(sql("""BEGIN READ ONLY;
SELECT json_build_object(
'settings',(SELECT json_object_agg(name,setting) FROM pg_settings WHERE name IN ('max_connections','statement_timeout','lock_timeout','idle_in_transaction_session_timeout','autovacuum','work_mem')),
'runtime_role',(SELECT row_to_json(r) FROM (SELECT rolname,rolsuper,rolcreatedb,rolcreaterole,rolbypassrls FROM pg_roles WHERE rolname='leaddesk') r),
'connections',(SELECT json_agg(r) FROM (SELECT usename,state,count(*) FROM pg_stat_activity WHERE datname='leaddesk' GROUP BY 1,2) r),
'activity',(SELECT row_to_json(r) FROM (SELECT deadlocks,temp_files,temp_bytes FROM pg_stat_database WHERE datname='leaddesk') r),
'tables',(SELECT json_agg(r) FROM (SELECT relname,n_live_tup,n_dead_tup,last_autoanalyze,last_autovacuum FROM pg_stat_user_tables ORDER BY relname) r),
'indexes',(SELECT json_agg(r) FROM (SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY tablename,indexname) r),
'counts',json_build_object('opportunities',(SELECT count(*) FROM opportunities),'versions',(SELECT count(*) FROM opportunity_versions),'classifications',(SELECT count(*) FROM classifications),'jobs',(SELECT count(*) FROM jobs),'attempts',(SELECT count(*) FROM job_attempts)));
ROLLBACK;"""))
report={'role_for_page_plans':'leaddesk','read_only_transactions':True,'plans':plans,'metadata':metadata}
(HERE/'postgres-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'plans':plans,'settings':metadata['settings'],'role':metadata['runtime_role'],'connections':metadata['connections'],'activity':metadata['activity'],'counts':metadata['counts']},indent=2))
