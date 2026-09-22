package store

import (
	"encoding/json"
	"reflect"
	"strings"
	"testing"
)

func TestPageMatchesOriginalOrderingAndScopes(t *testing.T) {
	reset(t)
	if _, e := testStore.ImportReceipts(testCtx, "../../../analise/resultados/jev-vercel-v02", "../../policy.json", testPolicy); e != nil {
		t.Fatal(e)
	}
	first := testDataset.Opportunities[0]
	users := []User{{Role: "admin"}, {Role: "seller", Scope: first.Agent}, {Role: "manager", Scope: first.Manager}, {Role: "seller", Scope: "absent"}}
	for _, u := range users {
		for _, filters := range []map[string]string{{}, {"search": "GTX"}, {"search": "ZZZ-SEM-RESULTADO"}, {"sales_agent": first.Agent}, {"manager": first.Manager}, {"region": first.Region}} {
			original, e := testStore.List(testCtx, u, filters)
			if e != nil {
				t.Fatal(e)
			}
			counts := map[string]int{}
			for _, v := range original {
				counts[v.Decision.Action]++
			}
			for _, action := range []string{"", "identify_account", "review_old_negotiation", "human_review", "invalid"} {
				f := map[string]string{}
				for k, v := range filters {
					f[k] = v
				}
				f["action"] = action
				expected := []View{}
				for _, v := range original {
					if action == "" || v.Decision.Action == action {
						expected = append(expected, v)
					}
				}
				pages := (len(expected) + 19) / 20
				if pages < 1 {
					pages = 1
				}
				for _, requested := range []int{-1, 1, 2, pages, 1000000} {
					got, e := testStore.Page(testCtx, u, f, requested)
					if e != nil {
						t.Fatal(e)
					}
					page := requested
					if page < 1 {
						page = 1
					}
					if page > pages {
						page = pages
					}
					end := page * 20
					if end > len(expected) {
						end = len(expected)
					}
					want := expected[(page-1)*20 : end]
					// JSON normalizes raw response key order while preserving all API values.
					a, _ := json.Marshal(got.Rows)
					b, _ := json.Marshal(want)
					var av, bv any
					json.Unmarshal(a, &av)
					json.Unmarshal(b, &bv)
					if !reflect.DeepEqual(av, bv) || !reflect.DeepEqual(got.Counts, counts) || got.Total != len(expected) || got.ScopeTotal != len(original) || got.Page != page || got.Pages != pages {
						t.Fatalf("pagination mismatch: user=%+v filters=%+v page=%d", u, f, requested)
					}
				}
			}
		}
	}
	// Every boundary in the full portfolio, not only the first and last page.
	original, _ := testStore.List(testCtx, User{Role: "admin"}, nil)
	for p := 1; p <= (len(original)+19)/20; p++ {
		got, e := testStore.Page(testCtx, User{Role: "admin"}, nil, p)
		if e != nil {
			t.Fatal(e)
		}
		for i, v := range got.Rows {
			if v.ID != original[(p-1)*20+i].ID {
				t.Fatal("ordering changed")
			}
		}
	}
	facets, e := testStore.Facets(testCtx, User{Role: "seller", Scope: first.Agent})
	if e != nil {
		t.Fatal(e)
	}
	if !reflect.DeepEqual(facets["sales_agent"], []string{first.Agent}) {
		t.Fatal("facet scope")
	}
}

func TestAuditScopeVersionsAndCurrentMeaning(t *testing.T) {
	reset(t)
	j := enqueueClaim(t, 0)
	if e := testStore.Complete(testCtx, j, responseFor(j), "test_fixture", 0); e != nil {
		t.Fatal(e)
	}
	u := User{ID: "reviewer", Role: "admin"}
	inspect := func() map[string]any {
		t.Helper()
		b, e := testStore.Audit(testCtx, u, j.OpportunityID)
		if e != nil {
			t.Fatal(e)
		}
		if strings.Contains(string(b), "providerMetadata") || strings.Contains(string(b), "token") {
			t.Fatal("unexpected private metadata")
		}
		var v map[string]any
		if e = json.Unmarshal(b, &v); e != nil {
			t.Fatal(e)
		}
		return v
	}
	before := inspect()
	c := before["classifications"].([]any)[0].(map[string]any)
	if c["current"] != true || c["origin"] != "test_fixture" || before["version_count"] != float64(1) {
		t.Fatal("initial audit")
	}
	row, e := testStore.Get(testCtx, u, j.OpportunityID)
	if e != nil {
		t.Fatal(e)
	}
	account := "Acme Corporation"
	if row.Account == account {
		account = ""
	}
	if _, e = testStore.SetAccount(testCtx, u, row.ID, row.Version, account); e != nil {
		t.Fatal(e)
	}
	after := inspect()
	c = after["classifications"].([]any)[0].(map[string]any)
	if c["current"] != false || c["current_at_commit"] != true || after["version_count"] != float64(2) {
		t.Fatal("stale audit")
	}
	if _, e = testStore.Audit(testCtx, User{Role: "seller", Scope: "foreign"}, row.ID); e == nil {
		t.Fatal("foreign audit allowed")
	}
	// Bounded result must state its full count rather than silently truncate history.
	for i := int64(2); i < 23; i++ {
		if i%2 == 0 {
			account = ""
		} else {
			account = "Acme Corporation"
		}
		v, _ := testStore.Get(testCtx, u, row.ID)
		if v.Account == account {
			account = "Betatech"
		}
		if _, e = testStore.SetAccount(testCtx, u, row.ID, v.Version, account); e != nil {
			t.Fatal(e)
		}
	}
	final := inspect()
	if final["version_count"].(float64) <= 20 || len(final["versions"].([]any)) != 20 {
		t.Fatal("audit limit/count")
	}
}
