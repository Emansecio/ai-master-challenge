package store

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"leaddesk/internal/config"
	"leaddesk/internal/core"
	"net/url"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"
)

var testStore, adminStore *Store
var testPolicy core.Policy
var testDataset core.Dataset
var testURL string
var testCtx = context.Background()

func TestMain(m *testing.M) {
	if os.Getenv("LEADDESK_INTEGRATION") != "1" {
		os.Exit(m.Run())
	}
	if e := setupTests(); e != nil {
		fmt.Fprintln(os.Stderr, "integration setup:", e)
		os.Exit(1)
	}
	code := m.Run()
	testStore.DB.Close()
	adminStore.DB.Close()
	parent, e := Open(testCtx, os.Getenv("ADMIN_DATABASE_URL"))
	if e == nil {
		u, _ := url.Parse(testURL)
		_, e = parent.DB.Exec(testCtx, "DROP DATABASE "+u.Path[1:]+" WITH (FORCE)")
		parent.DB.Close()
	}
	if e != nil {
		fmt.Fprintln(os.Stderr, "test database cleanup failed")
		code = 1
	}
	os.Exit(code)
}
func setupTests() error {
	if e := config.Load("../../.local/dev.env"); e != nil {
		return e
	}
	root, e := Open(testCtx, os.Getenv("ADMIN_DATABASE_URL"))
	if e != nil {
		return e
	}
	defer root.DB.Close()
	name := fmt.Sprintf("leaddesk_test_%d", time.Now().UnixNano())
	if _, e = root.DB.Exec(testCtx, "CREATE DATABASE "+name); e != nil {
		return e
	}
	u, e := url.Parse(os.Getenv("ADMIN_DATABASE_URL"))
	if e != nil {
		return e
	}
	u.Path = "/" + name
	adminStore, e = Open(testCtx, u.String())
	if e != nil {
		return e
	}
	if e = adminStore.Migrate(testCtx, os.Getenv("APP_DB_PASSWORD")); e != nil {
		return e
	}
	testDataset, e = core.LoadDataset("../../../analise/dados/crm-sales-predictive-analytics.zip")
	if e != nil {
		return e
	}
	testPolicy, e = core.LoadPolicy("../../policy.json", "2026-09-22")
	if e != nil {
		return e
	}
	dir, e := os.MkdirTemp("", "leaddesk-tests-")
	if e != nil {
		return e
	}
	defer os.RemoveAll(dir)
	if e = adminStore.Seed(testCtx, testDataset, testPolicy, filepath.Join(dir, "codes.json")); e != nil {
		return e
	}
	u, e = url.Parse(os.Getenv("DATABASE_URL"))
	if e != nil {
		return e
	}
	u.Path = "/" + name
	testURL = u.String()
	testStore, e = Open(testCtx, testURL)
	return e
}
func reset(t *testing.T) {
	t.Helper()
	if testStore == nil {
		t.Skip("set LEADDESK_INTEGRATION=1 for real PostgreSQL")
	}
	_, e := adminStore.DB.Exec(testCtx, `TRUNCATE job_attempts,jobs,classifications;
 UPDATE opportunities o SET version=1,doc=v.doc FROM opportunity_versions v WHERE v.opportunity_id=o.id AND v.version=1;
 DELETE FROM opportunity_versions WHERE version>1; UPDATE provider_gate SET next_start=now();`)
	if e != nil {
		t.Fatal(e)
	}
	b, _ := json.Marshal(testPolicy)
	if _, e = adminStore.DB.Exec(testCtx, "UPDATE settings SET policy_hash=$1,policy=$2", testPolicy.Hash, b); e != nil {
		t.Fatal(e)
	}
}
func responseFor(j Job) core.Response {
	d := core.Decide(j.State)
	choices := map[string]string{"qualification": d.Qualification, "next_action": d.Action}
	r := core.Response{Model: core.Model, Answers: map[string]core.Answer{}}
	for name, q := range j.Policy.Questions {
		ps := map[string]float64{}
		for c := range q.Criteria {
			ps[c] = 0
		}
		ps[choices[name]] = 1
		confidence := 1.0
		r.Answers[name] = core.Answer{Type: "choice", Choice: choices[name], Probabilities: ps, Confidence: &confidence}
	}
	return r
}
func enqueueClaim(t *testing.T, index int) Job {
	t.Helper()
	o := testDataset.Opportunities[index]
	if _, e := testStore.Enqueue(testCtx, User{Role: "admin"}, o.ID, 1); e != nil {
		t.Fatal(e)
	}
	j, e := testStore.Claim(testCtx, 0)
	if e != nil || j == nil {
		t.Fatalf("claim: %v", e)
	}
	return *j
}
func TestRealImportAndReceipts(t *testing.T) {
	reset(t)
	var n int
	if e := testStore.DB.QueryRow(testCtx, "SELECT count(*) FROM source_records WHERE table_name='sales_pipeline.csv'").Scan(&n); e != nil || n != 8800 {
		t.Fatalf("pipeline %d %v", n, e)
	}
	n, e := testStore.ImportReceipts(testCtx, "../../../analise/resultados/jev-vercel-v02", "../../policy.json", testPolicy)
	if e != nil || n != 120 {
		t.Fatalf("receipts %d %v", n, e)
	}
	n, e = testStore.ImportReceipts(testCtx, "../../../analise/resultados/jev-vercel-v02", "../../policy.json", testPolicy)
	if e != nil || n != 0 {
		t.Fatal("import must be idempotent", n, e)
	}
}
func TestConcurrentDedupAndPersistentResult(t *testing.T) {
	reset(t)
	o := testDataset.Opportunities[0]
	var wg sync.WaitGroup
	ids := make(chan string, 35)
	errs := make(chan error, 35)
	for i := 0; i < 35; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			j, e := testStore.Enqueue(testCtx, User{Role: "admin"}, o.ID, 1)
			ids <- j.ID
			errs <- e
		}()
	}
	wg.Wait()
	close(ids)
	close(errs)
	for e := range errs {
		if e != nil {
			t.Fatal(e)
		}
	}
	set := map[string]bool{}
	for id := range ids {
		set[id] = true
	}
	if len(set) != 1 {
		t.Fatal("duplicate jobs", set)
	}
	j, e := testStore.Claim(testCtx, 0)
	if e != nil || j == nil {
		t.Fatal(e)
	}
	other, e := testStore.Claim(testCtx, 0)
	if e != nil || other != nil {
		t.Fatal("double claim", e)
	}
	if e = testStore.Complete(testCtx, *j, responseFor(*j), "test_fixture", time.Millisecond); e != nil {
		t.Fatal(e)
	}
	// New connection pool reads the persisted result; fixture is explicitly labelled.
	reopened, e := Open(testCtx, testURL)
	if e != nil {
		t.Fatal(e)
	}
	defer reopened.DB.Close()
	v, e := reopened.Get(testCtx, User{Role: "admin"}, o.ID)
	if e != nil || v.Status != "classified" {
		t.Fatal(v.Status, e)
	}
	cached, e := reopened.Enqueue(testCtx, User{Role: "admin"}, o.ID, 1)
	if e != nil || cached.Status != "cached" {
		t.Fatal(cached, e)
	}
}
func TestConcurrentEditsAndLateResponse(t *testing.T) {
	reset(t)
	j := enqueueClaim(t, 0)
	o := testDataset.Opportunities[0]
	choices := []string{}
	for _, r := range testDataset.Tables["accounts.csv"] {
		if r["account"] != o.Account {
			choices = append(choices, r["account"])
		}
		if len(choices) == 2 {
			break
		}
	}
	errs := make(chan error, 2)
	for _, account := range choices {
		go func(name string) {
			_, e := testStore.SetAccount(testCtx, User{ID: "test", Role: "admin"}, o.ID, 1, name)
			errs <- e
		}(account)
	}
	success, conflict := 0, 0
	for i := 0; i < 2; i++ {
		e := <-errs
		if e == nil {
			success++
		} else if errors.Is(e, ErrConflict) {
			conflict++
		} else {
			t.Fatal(e)
		}
	}
	if success != 1 || conflict != 1 {
		t.Fatal(success, conflict)
	}
	if e := testStore.Complete(testCtx, j, responseFor(j), "test_fixture", time.Millisecond); e != nil {
		t.Fatal(e)
	}
	v, e := testStore.Get(testCtx, User{Role: "admin"}, o.ID)
	if e != nil || v.Version != 2 || string(v.Classification) != "null" || v.Status != "stale" {
		t.Fatalf("old response published: %+v %v", v, e)
	}
	var current bool
	if e = testStore.DB.QueryRow(testCtx, "SELECT current_at_commit FROM classifications WHERE opportunity_id=$1", o.ID).Scan(&current); e != nil || current {
		t.Fatal("history incorrectly current", e)
	}
}
func TestPolicyChangeDuringCall(t *testing.T) {
	reset(t)
	j := enqueueClaim(t, 0)
	if _, e := adminStore.DB.Exec(testCtx, "UPDATE settings SET policy_hash='new-policy'"); e != nil {
		t.Fatal(e)
	}
	if e := testStore.Complete(testCtx, j, responseFor(j), "test_fixture", 0); e != nil {
		t.Fatal(e)
	}
	v, e := testStore.Get(testCtx, User{Role: "admin"}, j.OpportunityID)
	if e != nil || v.Status != "stale" || string(v.Classification) != "null" {
		t.Fatal("policy change not respected", e)
	}
}
func TestLeaseRecoveryAndAttemptLimit(t *testing.T) {
	reset(t)
	old := enqueueClaim(t, 0)
	if _, e := adminStore.DB.Exec(testCtx, "UPDATE jobs SET lease_until=now()-interval '1 second' WHERE id=$1", old.ID); e != nil {
		t.Fatal(e)
	}
	j, e := testStore.Claim(testCtx, 0)
	if e != nil || j == nil || j.Attempts != 2 || j.LeaseToken == old.LeaseToken {
		t.Fatal("lease recovery", e)
	}
	if e = testStore.Complete(testCtx, old, responseFor(old), "test_fixture", 0); e == nil {
		t.Fatal("old worker accepted")
	}
	if e = testStore.Fail(testCtx, *j, "HTTP 429 controlado", true, 0); e != nil {
		t.Fatal(e)
	}
	if _, e = adminStore.DB.Exec(testCtx, "UPDATE jobs SET available_at=now()"); e != nil {
		t.Fatal(e)
	}
	j, e = testStore.Claim(testCtx, 0)
	if e != nil || j == nil || j.Attempts != 3 {
		t.Fatal(e)
	}
	if e = testStore.Fail(testCtx, *j, "HTTP 429 controlado", true, 0); e != nil {
		t.Fatal(e)
	}
	next, e := testStore.Claim(testCtx, 0)
	if e != nil || next != nil {
		t.Fatal("retry limit ignored", e)
	}
}
func TestAccessScopeAndRuntimePrivileges(t *testing.T) {
	reset(t)
	o := testDataset.Opportunities[0]
	wrong := User{Role: "seller", Scope: "not-the-owner"}
	if _, e := testStore.Get(testCtx, wrong, o.ID); !errors.Is(e, ErrForbidden) {
		t.Fatal("foreign read", e)
	}
	if _, e := testStore.Enqueue(testCtx, wrong, o.ID, 1); !errors.Is(e, ErrForbidden) {
		t.Fatal("foreign enqueue", e)
	}
	if _, e := testStore.SetAccount(testCtx, wrong, o.ID, 1, ""); !errors.Is(e, ErrForbidden) {
		t.Fatal("foreign edit", e)
	}
	rows, e := testStore.List(testCtx, wrong, map[string]string{"sales_agent": o.Agent})
	if e != nil || len(rows) != 0 {
		t.Fatal("filter bypass", e)
	}
	rows, e = testStore.List(testCtx, User{Role: "manager", Scope: o.Manager}, map[string]string{})
	if e != nil || len(rows) == 0 {
		t.Fatal(e)
	}
	for _, v := range rows {
		if v.Manager != o.Manager {
			t.Fatal("manager scope")
		}
	}
	var super, create bool
	if e = testStore.DB.QueryRow(testCtx, "SELECT rolsuper,rolcreatedb FROM pg_roles WHERE rolname=current_user").Scan(&super, &create); e != nil || super || create {
		t.Fatal("runtime privileges", e)
	}
	if _, e = testStore.DB.Exec(testCtx, "UPDATE opportunity_versions SET actor='changed'"); e == nil {
		t.Fatal("history must be immutable to runtime")
	}
}

func TestGlobalConcurrencyGate(t *testing.T) {
	reset(t)
	for i := 0; i < 3; i++ {
		o := testDataset.Opportunities[i]
		if _, e := testStore.Enqueue(testCtx, User{Role: "admin"}, o.ID, 1); e != nil {
			t.Fatal(e)
		}
	}
	a, e := testStore.Claim(testCtx, 0)
	if e != nil || a == nil {
		t.Fatal(e)
	}
	b, e := testStore.Claim(testCtx, 0)
	if e != nil || b == nil {
		t.Fatal(e)
	}
	c, e := testStore.Claim(testCtx, 0)
	if e != nil || c != nil {
		t.Fatal("global concurrency limit", e)
	}
	if e = testStore.Complete(testCtx, *a, responseFor(*a), "test_fixture", 0); e != nil {
		t.Fatal(e)
	}
	c, e = testStore.Claim(testCtx, 0)
	if e != nil || c == nil {
		t.Fatal("queue did not progress", e)
	}
}

func TestExhaustedLeaseBecomesTerminal(t *testing.T) {
	reset(t)
	j := enqueueClaim(t, 0)
	if _, e := adminStore.DB.Exec(testCtx, "UPDATE jobs SET attempts=3,lease_until=now()-interval '1 second' WHERE id=$1", j.ID); e != nil {
		t.Fatal(e)
	}
	next, e := testStore.Claim(testCtx, 0)
	if e != nil || next != nil {
		t.Fatal(e)
	}
	var status string
	if e = testStore.DB.QueryRow(testCtx, "SELECT status FROM jobs WHERE id=$1", j.ID).Scan(&status); e != nil || status != "failed" {
		t.Fatal("exhausted lease left running", status, e)
	}
}

func TestModelEpochCannotReuseOldReceipts(t *testing.T) {
	reset(t)
	changed, e := core.LoadPolicy("../../policy.json", "new-validation-epoch")
	if e != nil {
		t.Fatal(e)
	}
	if changed.Hash == testPolicy.Hash {
		t.Fatal("epoch missing from identity")
	}
	n, e := testStore.ImportReceipts(testCtx, "../../../analise/resultados/jev-vercel-v02", "../../policy.json", changed)
	if e != nil || n != 0 {
		t.Fatal("old receipts imported as new validation", n, e)
	}
}
