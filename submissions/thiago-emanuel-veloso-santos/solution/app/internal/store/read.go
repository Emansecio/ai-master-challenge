package store

import (
	"context"
	"encoding/json"
	"leaddesk/internal/core"
)

// Counts and page are read in one statement, sharing a PostgreSQL snapshot.
const scopedWhere = `($1='admin' OR ($1='manager' AND o.doc->>'manager'=$2) OR ($1='seller' AND o.doc->>'sales_agent'=$2))`
const pageOrder = `(doc->>'priority')::int,
 CASE WHEN (doc->>'priority')::int=1 THEN (doc->'state'->>'age_days')::float8 / NULLIF((doc->'state'->>'reference_p90_days')::float8,0) ELSE 0 END DESC NULLS LAST,
 (doc->'state'->>'catalog_price')::int DESC, id COLLATE "C"`

type Page struct {
	Rows       []View         `json:"rows"`
	Total      int            `json:"total"`
	ScopeTotal int            `json:"scope_total"`
	Counts     map[string]int `json:"counts"`
	Page       int            `json:"page"`
	Pages      int            `json:"pages"`
}

func (s *Store) Page(ctx context.Context, u User, f map[string]string, requested int) (Page, error) {
	var result Page
	var rows, counts []byte
	if requested < 1 {
		requested = 1
	}
	query := `WITH candidates AS MATERIALIZED (
 SELECT o.id,o.version,o.doc FROM opportunities o WHERE ` + scopedWhere + `
 AND ($3='' OR o.doc->>'sales_agent'=$3) AND ($4='' OR o.doc->>'manager'=$4) AND ($5='' OR o.doc->>'region'=$5)
 AND ($6='' OR concat_ws(' ',o.id,o.doc->>'account',o.doc->>'sales_agent',o.doc->'state'->>'product') ILIKE '%'||$6||'%')
 ), narrowed AS MATERIALIZED (SELECT * FROM candidates WHERE $7='' OR doc->'decision'->>'next_action'=$7),
 totals AS (SELECT (SELECT count(*) FROM candidates)::int scope_total, count(*)::int total, greatest(1,(count(*)+19)/20)::int pages FROM narrowed),
 bounds AS (SELECT *,least($8,pages)::int page FROM totals),
 selected AS (SELECT *,row_number() OVER (ORDER BY ` + pageOrder + `) ordinal FROM narrowed ORDER BY ` + pageOrder + `
 LIMIT 20 OFFSET (SELECT (page-1)*20 FROM bounds)),
 views AS (SELECT o.ordinal,o.doc || jsonb_build_object(
 'classification',c.response-'providerMetadata'-'usage',
 'status',CASE WHEN c.opportunity_id IS NOT NULL THEN 'classified' WHEN j.id IS NOT NULL THEN j.status
 WHEN EXISTS(SELECT 1 FROM classifications old WHERE old.opportunity_id=o.id) THEN 'stale' ELSE 'unclassified' END,
 'error',coalesce(j.error,'')) value FROM selected o CROSS JOIN settings s
 LEFT JOIN classifications c ON c.opportunity_id=o.id AND c.version=o.version AND c.policy_hash=s.policy_hash
 LEFT JOIN jobs j ON j.opportunity_id=o.id AND j.version=o.version AND j.policy_hash=s.policy_hash)
 SELECT coalesce((SELECT jsonb_agg(value ORDER BY ordinal) FROM views),'[]'::jsonb),
 coalesce((SELECT jsonb_object_agg(action,n) FROM (SELECT doc->'decision'->>'next_action' action,count(*) n FROM candidates GROUP BY 1) grouped),'{}'::jsonb),
 total,scope_total,page,pages FROM bounds`
	err := s.DB.QueryRow(ctx, query, u.Role, u.Scope, f["sales_agent"], f["manager"], f["region"], f["search"], f["action"], requested).Scan(&rows, &counts, &result.Total, &result.ScopeTotal, &result.Page, &result.Pages)
	if err != nil {
		return result, err
	}
	if err = json.Unmarshal(rows, &result.Rows); err != nil {
		return result, err
	}
	err = json.Unmarshal(counts, &result.Counts)
	return result, err
}

func (s *Store) Facets(ctx context.Context, u User) (map[string][]string, error) {
	var raw []byte
	err := s.DB.QueryRow(ctx, `SELECT jsonb_build_object(
 'sales_agent',coalesce(array_agg(DISTINCT doc->>'sales_agent' ORDER BY doc->>'sales_agent'),'{}'),
 'manager',coalesce(array_agg(DISTINCT doc->>'manager' ORDER BY doc->>'manager'),'{}'),
 'region',coalesce(array_agg(DISTINCT doc->>'region' ORDER BY doc->>'region'),'{}')) FROM opportunities o WHERE `+scopedWhere, u.Role, u.Scope).Scan(&raw)
	result := map[string][]string{}
	if err == nil {
		err = json.Unmarshal(raw, &result)
	}
	return result, err
}

// Audit exposes a bounded history with an explicit total, never provider metadata or credentials.
func (s *Store) Audit(ctx context.Context, u User, id string) (json.RawMessage, error) {
	var raw json.RawMessage
	query := `SELECT jsonb_build_object('opportunity_id',o.id,'current_version',o.version,
 'policy_hash',s.policy_hash,'policy_version',s.policy->>'policy_version','dataset_sha256',$4::text,
 'history_limit',20,
 'version_count',(SELECT count(*) FROM opportunity_versions WHERE opportunity_id=o.id),
 'classification_count',(SELECT count(*) FROM classifications WHERE opportunity_id=o.id),
 'attempt_count',(SELECT count(*) FROM job_attempts a JOIN jobs j ON j.id=a.job_id WHERE j.opportunity_id=o.id),
 'attempts',coalesce((SELECT jsonb_agg(value ORDER BY recorded_at DESC,job_id,attempt DESC) FROM (
 SELECT a.created_at recorded_at,a.job_id,a.attempt,jsonb_build_object('job_id',a.job_id,'attempt',a.attempt,
 'version',j.version,'policy_hash',j.policy_hash,'outcome',a.outcome,'elapsed_ms',a.elapsed_ms,'recorded_at',a.created_at) value
 FROM job_attempts a JOIN jobs j ON j.id=a.job_id WHERE j.opportunity_id=o.id
 ORDER BY a.created_at DESC,a.job_id,a.attempt DESC LIMIT 20) history),'[]'),
 'versions',coalesce((SELECT jsonb_agg(value ORDER BY version DESC) FROM (
 SELECT v.version,jsonb_build_object('version',v.version,'actor',v.actor,'recorded_at',v.created_at,'account',v.doc->>'account') value
 FROM opportunity_versions v WHERE v.opportunity_id=o.id ORDER BY v.version DESC LIMIT 20) history),'[]'),
 'classifications',coalesce((SELECT jsonb_agg(value ORDER BY recorded_at DESC,version DESC,policy_hash) FROM (
 SELECT c.created_at recorded_at,c.version,c.policy_hash,jsonb_build_object('version',c.version,'policy_hash',c.policy_hash,
 'origin',c.origin,'recorded_at',c.created_at,'model',c.response->>'model',
 'current',c.version=o.version AND c.policy_hash=s.policy_hash,
 'current_at_commit',c.current_at_commit,
 'qualification',c.response->'answers'->'qualification'->>'choice',
 'next_action',c.response->'answers'->'next_action'->>'choice') value
 FROM classifications c WHERE c.opportunity_id=o.id ORDER BY c.created_at DESC,c.version DESC,c.policy_hash LIMIT 20) history),'[]'))
 FROM opportunities o CROSS JOIN settings s WHERE ` + scopedWhere + ` AND o.id=$3`
	err := s.DB.QueryRow(ctx, query, u.Role, u.Scope, id, core.DatasetSHA).Scan(&raw)
	return raw, err
}
