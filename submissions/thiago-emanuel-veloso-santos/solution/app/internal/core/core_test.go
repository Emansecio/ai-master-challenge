package core

import (
	"bufio"
	"encoding/json"
	"os"
	"testing"
)

func TestAuditedCases(t *testing.T) {
	d, e := LoadDataset("../../../analise/dados/crm-sales-predictive-analytics.zip")
	if e != nil {
		t.Fatal(e)
	}
	if len(d.Tables["sales_pipeline.csv"]) != 8800 || len(d.Tables["accounts.csv"]) != 85 {
		t.Fatal("table counts")
	}
	index := map[string]Opportunity{}
	for _, o := range d.Opportunities {
		index[o.ID] = o
	}
	f, e := os.Open("../../../analise/resultados/casos_jev.jsonl")
	if e != nil {
		t.Fatal(e)
	}
	defer f.Close()
	scanner := bufio.NewScanner(f)
	n := 0
	for scanner.Scan() {
		var row struct {
			ID       string   `json:"case_id"`
			State    State    `json:"state"`
			Expected Decision `json:"expected_by_policy"`
		}
		if e = json.Unmarshal(scanner.Bytes(), &row); e != nil {
			t.Fatal(e)
		}
		o := index[row.ID]
		if Hash(o.State) != Hash(row.State) {
			t.Fatalf("state differs: %s", row.ID)
		}
		if o.Decision != row.Expected {
			t.Fatalf("policy differs: %s", row.ID)
		}
		n++
	}
	if e = scanner.Err(); e != nil {
		t.Fatal(e)
	}
	if n != 120 {
		t.Fatal(n)
	}
}
func TestContradictionAndBoundary(t *testing.T) {
	age := 100
	engage := "2017-09-22"
	s := State{AsOf: "2017-12-31", Stage: "Engaging", AccountIdentified: true, EngageDate: &engage, AgeDays: &age, Reference: 100}
	if Decide(s).Action != "continue_negotiation_review" {
		t.Fatal("equal to P90 must not be old")
	}
	s.Old = true
	if Decide(s).Action != "human_review" {
		t.Fatal("contradiction must be reviewed")
	}
	s.Reference = 99
	if Decide(s).Action != "review_old_negotiation" {
		t.Fatal("above P90")
	}
	s.AccountIdentified = false
	if Decide(s).Action != "identify_account" {
		t.Fatal("missing account precedence")
	}
	s.AsOf = "invalid"
	if Decide(s).Action != "human_review" {
		t.Fatal("invalid date")
	}
}
