package web

import (
	"net/http/httptest"
	"os"
	"strings"
	"testing"
)

func TestRecommendationModuleIsServed(t *testing.T) {
	api := API{Static: "../../static", Host: "127.0.0.1:8766"}
	w := httptest.NewRecorder()
	api.Handler().ServeHTTP(w, httptest.NewRequest("GET", "http://127.0.0.1:8766/recommendation.js", nil))
	want, err := os.ReadFile("../../static/recommendation.js")
	if err != nil {
		t.Fatal(err)
	}
	if w.Code != 200 || w.Body.String() != string(want) || !strings.Contains(w.Header().Get("Content-Type"), "javascript") {
		t.Fatalf("browser cannot load the explanation module: HTTP %d, %s", w.Code, w.Header().Get("Content-Type"))
	}
	if strings.Contains(w.Header().Get("Content-Security-Policy"), "unsafe-inline") {
		t.Fatal("module must work with the existing content policy")
	}
}
