package service

import (
	"context"
	"encoding/json"
	"leaddesk/internal/core"
	"leaddesk/internal/store"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHTTPFailuresAndNoLabelLeak(t *testing.T) {
	policy, e := core.LoadPolicy("../../policy.json", "test")
	if e != nil {
		t.Fatal(e)
	}
	d, e := core.LoadDataset("../../../analise/dados/crm-sales-predictive-analytics.zip")
	if e != nil {
		t.Fatal(e)
	}
	j := store.Job{State: d.Opportunities[0].State, Policy: policy}
	for _, status := range []int{429, 503, 401} {
		t.Run(http.StatusText(status), func(t *testing.T) {
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.Header.Get("Authorization") != "Bearer test-only-key" {
					t.Error("auth missing")
				}
				var body map[string]json.RawMessage
				if e := json.NewDecoder(r.Body).Decode(&body); e != nil {
					t.Error(e)
				}
				if len(body) != 4 || body["state"] == nil || body["questions"] == nil || body["expected_by_policy"] != nil {
					t.Error("payload contract")
				}
				w.WriteHeader(status)
				w.Write([]byte("do not echo upstream test-only-key"))
			}))
			defer server.Close()
			_, e := (Client{Key: "test-only-key", Endpoint: server.URL}).Evaluate(context.Background(), j)
			failure, ok := e.(*Failure)
			if !ok || failure.Retry != (status == 429 || status >= 500) {
				t.Fatalf("wrong retry behavior: %v", e)
			}
		})
	}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(`{"model":"typesafe-ai/jev","answers":{}}`))
	}))
	defer server.Close()
	_, e = (Client{Key: "test-only-key", Endpoint: server.URL}).Evaluate(context.Background(), j)
	if e == nil {
		t.Fatal("malformed contract accepted")
	}
}
