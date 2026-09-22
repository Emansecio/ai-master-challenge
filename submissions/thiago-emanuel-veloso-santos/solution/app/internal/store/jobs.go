package store

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/jackc/pgx/v5"
	"leaddesk/internal/core"
	"time"
)

type Job struct {
	ID            string      `json:"id"`
	OpportunityID string      `json:"opportunity_id"`
	Version       int64       `json:"version"`
	PolicyHash    string      `json:"policy_hash"`
	State         core.State  `json:"-"`
	Policy        core.Policy `json:"-"`
	Status        string      `json:"status"`
	Attempts      int         `json:"attempts"`
	LeaseToken    string      `json:"-"`
}

func (s *Store) Enqueue(ctx context.Context, u User, id string, version int64) (Job, error) {
	tx, e := s.DB.Begin(ctx)
	if e != nil {
		return Job{}, e
	}
	defer tx.Rollback(ctx)
	var policy, doc []byte
	var hash string
	if e = tx.QueryRow(ctx, "SELECT policy_hash,policy FROM settings WHERE id=true FOR SHARE").Scan(&hash, &policy); e != nil {
		return Job{}, e
	}
	if e = tx.QueryRow(ctx, "SELECT doc FROM opportunities WHERE id=$1 FOR SHARE", id).Scan(&doc); e != nil {
		return Job{}, e
	}
	var o core.Opportunity
	if e = json.Unmarshal(doc, &o); e != nil {
		return Job{}, e
	}
	if !allowed(u, o) {
		return Job{}, ErrForbidden
	}
	if o.Version != version {
		return Job{}, ErrConflict
	}
	var exists bool
	if e = tx.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM classifications WHERE opportunity_id=$1 AND version=$2 AND policy_hash=$3)", id, version, hash).Scan(&exists); e != nil {
		return Job{}, e
	}
	if exists {
		return Job{OpportunityID: id, Version: version, PolicyHash: hash, Status: "cached"}, nil
	}
	state, _ := json.Marshal(o.State)
	job := Job{OpportunityID: id, Version: version, PolicyHash: hash}
	// Failed jobs are terminal after three attempts. Explicit new policy/data creates a new identity.
	e = tx.QueryRow(ctx, `INSERT INTO jobs(opportunity_id,version,policy_hash,state,policy,status) VALUES($1,$2,$3,$4,$5,'pending')
 ON CONFLICT(opportunity_id,version,policy_hash) DO UPDATE SET opportunity_id=excluded.opportunity_id
 RETURNING id::text,status,attempts`, id, version, hash, state, policy).Scan(&job.ID, &job.Status, &job.Attempts)
	if e != nil {
		return Job{}, e
	}
	return job, tx.Commit(ctx)
}
func (s *Store) Claim(ctx context.Context, interval time.Duration) (*Job, error) {
	tx, e := s.DB.Begin(ctx)
	if e != nil {
		return nil, e
	}
	defer tx.Rollback(ctx)
	// This gate is shared across workers and processes, not a per-process limiter.
	var ready bool
	if e = tx.QueryRow(ctx, "SELECT next_start<=now() FROM provider_gate WHERE id=true FOR UPDATE SKIP LOCKED").Scan(&ready); errors.Is(e, pgx.ErrNoRows) {
		return nil, nil
	} else if e != nil {
		return nil, e
	}
	// A lost worker has no trustworthy measured duration. Record its interrupted
	// attempt in the same transaction that releases its lease, exactly once.
	if _, e = tx.Exec(ctx, `WITH expired AS (
 SELECT id FROM jobs WHERE status='running' AND lease_until<now() FOR UPDATE SKIP LOCKED
 ), recovered AS (
 UPDATE jobs SET status=CASE WHEN attempts>=3 THEN 'failed' ELSE 'pending' END,
 error=CASE WHEN attempts>=3 THEN 'Processamento interrompido após o limite de tentativas.' ELSE 'Processamento interrompido; nova tentativa pendente.' END,
 lease_until=null,lease_token=null,available_at=now(),updated_at=now()
 FROM expired WHERE jobs.id=expired.id RETURNING jobs.id,jobs.attempts)
 INSERT INTO job_attempts(job_id,attempt,outcome,elapsed_ms)
 SELECT id,attempts,'interrupted',null FROM recovered ON CONFLICT(job_id,attempt) DO NOTHING`); e != nil {
		return nil, e
	}
	// Compare identities at the claim snapshot, without acquiring settings or
	// opportunity locks in the reverse order of writers. Complete checks again
	// because facts/policy can still change after a reservation is committed.
	if _, e = tx.Exec(ctx, `WITH obsolete AS (
 SELECT j.id FROM jobs j JOIN opportunities o ON o.id=j.opportunity_id CROSS JOIN settings s
 WHERE j.status='pending' AND (j.version<>o.version OR j.policy_hash<>s.policy_hash)
 FOR UPDATE OF j SKIP LOCKED)
 UPDATE jobs SET status='stale',error='Dados ou política alterados antes do processamento.',updated_at=now()
 FROM obsolete WHERE jobs.id=obsolete.id`); e != nil {
		return nil, e
	}
	if !ready {
		return nil, tx.Commit(ctx)
	}
	var running int
	if e = tx.QueryRow(ctx, "SELECT count(*) FROM jobs WHERE status='running' AND lease_until>now()").Scan(&running); e != nil {
		return nil, e
	}
	if running >= 2 {
		return nil, tx.Commit(ctx)
	}
	j := &Job{}
	var state, policy []byte
	e = tx.QueryRow(ctx, `WITH candidate AS (
 SELECT j.id FROM jobs j JOIN opportunities o ON o.id=j.opportunity_id CROSS JOIN settings s
 WHERE j.attempts<3 AND j.status='pending' AND j.available_at<=now()
 AND j.version=o.version AND j.policy_hash=s.policy_hash
 ORDER BY j.created_at,j.id FOR UPDATE OF j SKIP LOCKED LIMIT 1)
 UPDATE jobs SET status='running',attempts=attempts+1,lease_token=gen_random_uuid(),lease_until=now()+interval '45 seconds',updated_at=now()
 FROM candidate WHERE jobs.id=candidate.id RETURNING jobs.id::text,opportunity_id,version,policy_hash,state,policy,status,attempts,lease_token::text`).Scan(&j.ID, &j.OpportunityID, &j.Version, &j.PolicyHash, &state, &policy, &j.Status, &j.Attempts, &j.LeaseToken)
	if errors.Is(e, pgx.ErrNoRows) {
		return nil, tx.Commit(ctx)
	}
	if e != nil {
		return nil, e
	}
	if e = json.Unmarshal(state, &j.State); e != nil {
		return nil, e
	}
	if e = json.Unmarshal(policy, &j.Policy); e != nil {
		return nil, e
	}
	j.Policy.Hash = j.PolicyHash
	if _, e = tx.Exec(ctx, "UPDATE provider_gate SET next_start=now()+($1 * interval '1 millisecond') WHERE id=true", interval.Milliseconds()); e != nil {
		return nil, e
	}
	if e = tx.Commit(ctx); e != nil {
		return nil, e
	}
	return j, nil
}
func (s *Store) Complete(ctx context.Context, j Job, response core.Response, origin string, elapsed time.Duration) error {
	if e := core.Validate(response, j.Policy, j.State); e != nil {
		return e
	}
	tx, e := s.DB.Begin(ctx)
	if e != nil {
		return e
	}
	defer tx.Rollback(ctx)
	var valid bool
	if e = tx.QueryRow(ctx, "SELECT status='running' AND lease_token=$2::uuid AND lease_until>now() FROM jobs WHERE id=$1 FOR UPDATE", j.ID, j.LeaseToken).Scan(&valid); e != nil {
		return e
	}
	if !valid {
		return fmt.Errorf("lease vencida ou substituída")
	}
	var policy string
	var version int64
	if e = tx.QueryRow(ctx, "SELECT policy_hash FROM settings WHERE id=true FOR SHARE").Scan(&policy); e != nil {
		return e
	}
	if e = tx.QueryRow(ctx, "SELECT version FROM opportunities WHERE id=$1 FOR SHARE", j.OpportunityID).Scan(&version); e != nil {
		return e
	}
	current := version == j.Version && policy == j.PolicyHash
	status := "succeeded"
	if !current {
		status = "stale"
	}
	b, _ := json.Marshal(response)
	if _, e = tx.Exec(ctx, "INSERT INTO classifications(opportunity_id,version,policy_hash,response,origin,current_at_commit) VALUES($1,$2,$3,$4,$5,$6) ON CONFLICT DO NOTHING", j.OpportunityID, j.Version, j.PolicyHash, b, origin, current); e != nil {
		return e
	}
	if _, e = tx.Exec(ctx, "UPDATE jobs SET status=$2,error='',lease_until=null,updated_at=now() WHERE id=$1", j.ID, status); e != nil {
		return e
	}
	if _, e = tx.Exec(ctx, "INSERT INTO job_attempts(job_id,attempt,outcome,elapsed_ms) VALUES($1,$2,$3,$4)", j.ID, j.Attempts, status, elapsed.Milliseconds()); e != nil {
		return e
	}
	return tx.Commit(ctx)
}
func (s *Store) Fail(ctx context.Context, j Job, message string, retry bool, elapsed time.Duration) error {
	status := "failed"
	if retry && j.Attempts < 3 {
		status = "pending"
	}
	delay := time.Duration(j.Attempts*j.Attempts) * 2 * time.Second
	tx, e := s.DB.Begin(ctx)
	if e != nil {
		return e
	}
	defer tx.Rollback(ctx)
	tag, e := tx.Exec(ctx, `UPDATE jobs SET status=$3,error=$4,lease_until=null,available_at=now()+($5 * interval '1 millisecond'),updated_at=now()
 WHERE id=$1 AND lease_token=$2::uuid AND status='running' AND lease_until>now()`, j.ID, j.LeaseToken, status, message, delay.Milliseconds())
	if e != nil {
		return e
	}
	if tag.RowsAffected() != 1 {
		return fmt.Errorf("lease substituída")
	}
	if _, e = tx.Exec(ctx, "INSERT INTO job_attempts(job_id,attempt,outcome,elapsed_ms) VALUES($1,$2,$3,$4)", j.ID, j.Attempts, status, elapsed.Milliseconds()); e != nil {
		return e
	}
	return tx.Commit(ctx)
}
