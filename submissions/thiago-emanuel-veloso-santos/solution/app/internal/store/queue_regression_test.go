package store

import (
	"encoding/json"
	"strings"
	"testing"
	"time"
)

func TestClaimSkipsObsoletePendingIdentity(t *testing.T) {
	for _, change := range []string{"version", "policy"} {
		t.Run(change, func(t *testing.T) {
			reset(t)
			o := testDataset.Opportunities[0]
			u := User{ID: "test", Role: "admin"}
			old, e := testStore.Enqueue(testCtx, u, o.ID, 1)
			if e != nil {
				t.Fatal(e)
			}
			version := int64(1)
			if change == "version" {
				account := "Acme Corporation"
				if o.Account == account {
					account = ""
				}
				if _, e = testStore.SetAccount(testCtx, u, o.ID, 1, account); e != nil {
					t.Fatal(e)
				}
				version = 2
			} else if _, e = adminStore.DB.Exec(testCtx, "UPDATE settings SET policy_hash='changed-policy'"); e != nil {
				t.Fatal(e)
			}
			current, e := testStore.Enqueue(testCtx, u, o.ID, version)
			if e != nil {
				t.Fatal(e)
			}
			got, e := testStore.Claim(testCtx, 0)
			if e != nil || got == nil || got.ID != current.ID || got.Attempts != 1 {
				t.Fatalf("current claim: %+v %v", got, e)
			}
			var status string
			var attempts, events int
			if e = testStore.DB.QueryRow(testCtx, `SELECT status,attempts,(SELECT count(*) FROM job_attempts WHERE job_id=jobs.id) FROM jobs WHERE id=$1`, old.ID).Scan(&status, &attempts, &events); e != nil {
				t.Fatal(e)
			}
			if status != "stale" || attempts != 0 || events != 0 {
				t.Fatalf("obsolete dispatch consumed attempt: %s %d %d", status, attempts, events)
			}
		})
	}
}

func expireJob(t *testing.T, id string) {
	t.Helper()
	if _, e := adminStore.DB.Exec(testCtx, "UPDATE jobs SET lease_until=now()-interval '1 second' WHERE id=$1", id); e != nil {
		t.Fatal(e)
	}
}

func TestInterruptedAttemptsRecordedOnceAndFenced(t *testing.T) {
	reset(t)
	first := enqueueClaim(t, 0)
	expireJob(t, first.ID)
	second, e := testStore.Claim(testCtx, 0)
	if e != nil || second == nil || second.Attempts != 2 {
		t.Fatalf("recover: %+v %v", second, e)
	}
	if e = testStore.Fail(testCtx, first, "old worker", false, time.Second); e == nil {
		t.Fatal("old worker failure accepted")
	}
	if e = testStore.Complete(testCtx, first, responseFor(first), "test_fixture", time.Second); e == nil {
		t.Fatal("old worker response accepted")
	}
	if got, e := testStore.Claim(testCtx, 0); e != nil || got != nil {
		t.Fatal("live lease reclaimed", e)
	}
	if e = testStore.Complete(testCtx, *second, responseFor(*second), "test_fixture", 12*time.Millisecond); e != nil {
		t.Fatal(e)
	}
	var count, interruptions, measured int
	e = testStore.DB.QueryRow(testCtx, `SELECT count(*),count(*) FILTER(WHERE outcome='interrupted' AND elapsed_ms IS NULL),count(*) FILTER(WHERE outcome='succeeded' AND elapsed_ms=12) FROM job_attempts WHERE job_id=$1`, first.ID).Scan(&count, &interruptions, &measured)
	if e != nil || count != 2 || interruptions != 1 || measured != 1 {
		t.Fatalf("attempt history: %d %d %d %v", count, interruptions, measured, e)
	}
}

func TestExpiredObsoleteJobRecordsInterruptionWithoutRedispatch(t *testing.T) {
	reset(t)
	old := enqueueClaim(t, 0)
	expireJob(t, old.ID)
	if _, e := adminStore.DB.Exec(testCtx, "UPDATE settings SET policy_hash='changed-policy'"); e != nil {
		t.Fatal(e)
	}
	for i := 0; i < 2; i++ {
		if got, e := testStore.Claim(testCtx, 0); e != nil || got != nil {
			t.Fatal("obsolete lease dispatched", e)
		}
	}
	var status string
	var attempts, events int
	e := testStore.DB.QueryRow(testCtx, `SELECT status,attempts,(SELECT count(*) FROM job_attempts WHERE job_id=jobs.id AND outcome='interrupted' AND elapsed_ms IS NULL) FROM jobs WHERE id=$1`, old.ID).Scan(&status, &attempts, &events)
	if e != nil || status != "stale" || attempts != 1 || events != 1 {
		t.Fatalf("obsolete recovery: %s %d %d %v", status, attempts, events, e)
	}
}

func TestInterruptedExhaustionRecordsAllAttemptsOnce(t *testing.T) {
	reset(t)
	job := enqueueClaim(t, 0)
	for attempt := 1; attempt <= 3; attempt++ {
		expireJob(t, job.ID)
		next, e := testStore.Claim(testCtx, 0)
		if e != nil {
			t.Fatal(e)
		}
		if attempt < 3 {
			if next == nil || next.Attempts != attempt+1 {
				t.Fatalf("recovery %d: %+v", attempt, next)
			}
			job = *next
		} else if next != nil {
			t.Fatal("exhausted job dispatched")
		}
	}
	for i := 0; i < 2; i++ {
		if next, e := testStore.Claim(testCtx, 0); e != nil || next != nil {
			t.Fatal("terminal recovery", e)
		}
	}
	var status string
	var events int
	e := testStore.DB.QueryRow(testCtx, `SELECT status,(SELECT count(*) FROM job_attempts WHERE job_id=jobs.id AND outcome='interrupted' AND elapsed_ms IS NULL) FROM jobs WHERE id=$1`, job.ID).Scan(&status, &events)
	if e != nil || status != "failed" || events != 3 {
		t.Fatalf("exhausted history: %s %d %v", status, events, e)
	}
}

func TestAuditAttemptsAreBoundedScopedAndSafe(t *testing.T) {
	reset(t)
	j := enqueueClaim(t, 0)
	// Explicit fixture history spans policies, with deterministic recorded times.
	_, e := adminStore.DB.Exec(testCtx, `WITH fixture_jobs AS (
 INSERT INTO jobs(opportunity_id,version,policy_hash,state,policy,status,attempts,error)
 SELECT opportunity_id,version,'fixture-'||n,state,policy,'failed',3,'private transport details'
 FROM jobs CROSS JOIN generate_series(1,8) n WHERE id=$1 RETURNING id,policy_hash)
 INSERT INTO job_attempts(job_id,attempt,outcome,elapsed_ms,created_at)
 SELECT id,a,'interrupted',null,timestamptz '2020-01-01' + ((substring(policy_hash from 9)::int*3+a)*interval '1 second')
 FROM fixture_jobs CROSS JOIN generate_series(1,3) a`, j.ID)
	if e != nil {
		t.Fatal(e)
	}
	b, e := testStore.Audit(testCtx, User{Role: "admin"}, j.OpportunityID)
	if e != nil {
		t.Fatal(e)
	}
	var audit struct {
		AttemptCount int `json:"attempt_count"`
		HistoryLimit int `json:"history_limit"`
		Attempts     []struct {
			JobID    string    `json:"job_id"`
			Attempt  int       `json:"attempt"`
			Version  int64     `json:"version"`
			Policy   string    `json:"policy_hash"`
			Outcome  string    `json:"outcome"`
			Elapsed  *int64    `json:"elapsed_ms"`
			Recorded time.Time `json:"recorded_at"`
		} `json:"attempts"`
	}
	if e = json.Unmarshal(b, &audit); e != nil {
		t.Fatal(e)
	}
	if audit.AttemptCount != 24 || audit.HistoryLimit != 20 || len(audit.Attempts) != 20 {
		t.Fatalf("audit bounds: %d/%d", len(audit.Attempts), audit.AttemptCount)
	}
	for i, a := range audit.Attempts {
		if a.JobID == "" || a.Attempt < 1 || a.Attempt > 3 || a.Version != 1 || a.Outcome != "interrupted" || a.Elapsed != nil || !strings.HasPrefix(a.Policy, "fixture-") {
			t.Fatal("unexpected audit entry", i)
		}
		if i > 0 && a.Recorded.After(audit.Attempts[i-1].Recorded) {
			t.Fatal("attempt order")
		}
	}
	for _, forbidden := range []string{"lease_token", "private transport details", "providerMetadata", "state", "probabilities"} {
		if strings.Contains(string(b), forbidden) {
			t.Fatal("audit leaked", forbidden)
		}
	}
	for _, u := range []User{{Role: "seller", Scope: "foreign"}, {Role: "manager", Scope: "foreign"}} {
		if raw, e := testStore.Audit(testCtx, u, j.OpportunityID); e == nil || len(raw) > 0 {
			t.Fatal("foreign attempt audit allowed")
		}
	}
	owner := testDataset.Opportunities[0]
	if _, e = testStore.Audit(testCtx, User{Role: "seller", Scope: owner.Agent}, owner.ID); e != nil {
		t.Fatal("owner audit rejected", e)
	}
	if _, e = testStore.Audit(testCtx, User{Role: "manager", Scope: owner.Manager}, owner.ID); e != nil {
		t.Fatal("manager audit rejected", e)
	}
}
