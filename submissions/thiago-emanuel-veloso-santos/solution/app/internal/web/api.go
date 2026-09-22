package web

import (
	"encoding/json"
	"errors"
	"github.com/jackc/pgx/v5"
	"io"
	"leaddesk/internal/core"
	"leaddesk/internal/store"
	"net/http"
	"strconv"
	"strings"
	"time"
)

type API struct {
	Store         *store.Store
	KeyConfigured bool
	Static        string
	Host          string
}

func write(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(value)
}
func failure(w http.ResponseWriter, e error) {
	status := 500
	message := "Não foi possível concluir. Tente novamente."
	if errors.Is(e, store.ErrConflict) {
		status = 409
		message = e.Error()
	} else if errors.Is(e, store.ErrForbidden) || errors.Is(e, pgx.ErrNoRows) {
		status = 404
		message = "Oportunidade não encontrada."
	}
	write(w, status, map[string]string{"error": message})
}
func decode(w http.ResponseWriter, r *http.Request, value any) bool {
	r.Body = http.MaxBytesReader(w, r.Body, 4096)
	d := json.NewDecoder(r.Body)
	d.DisallowUnknownFields()
	if e := d.Decode(value); e != nil {
		write(w, 400, map[string]string{"error": "Solicitação inválida."})
		return false
	}
	if d.Decode(&struct{}{}) != io.EOF {
		write(w, 400, map[string]string{"error": "Solicitação inválida."})
		return false
	}
	return true
}
func (a API) Handler() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "no-store")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'")
		if r.Host != a.Host && r.Host != strings.Replace(a.Host, "127.0.0.1", "localhost", 1) {
			write(w, 403, map[string]string{"error": "Host inválido."})
			return
		}
		bearer := strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")
		hasBearer := strings.HasPrefix(r.Header.Get("Authorization"), "Bearer ")
		if r.Method != "GET" && r.Method != "HEAD" && !hasBearer && r.Header.Get("Origin") != "http://"+r.Host {
			write(w, 403, map[string]string{"error": "Origem inválida."})
			return
		}
		if r.URL.Path == "/api/login" && r.Method == "POST" {
			var input struct {
				Code string `json:"code"`
			}
			if !decode(w, r, &input) {
				return
			}
			u, e := a.Store.Authenticate(r.Context(), input.Code, false)
			if e != nil {
				write(w, 401, map[string]string{"error": "Código de acesso inválido."})
				return
			}
			token, e := a.Store.Session(r.Context(), u)
			if e != nil {
				failure(w, e)
				return
			}
			http.SetCookie(w, &http.Cookie{Name: "leaddesk_session", Value: token, Path: "/", HttpOnly: true, SameSite: http.SameSiteStrictMode, MaxAge: 28800})
			write(w, 200, u)
			return
		}
		if !strings.HasPrefix(r.URL.Path, "/api/") {
			files := map[string]string{"/": "index.html", "/app.js": "app.js", "/recommendation.js": "recommendation.js", "/style.css": "style.css", "/g4-logo.png": "g4-logo.png"}
			name, ok := files[r.URL.Path]
			if !ok {
				http.NotFound(w, r)
				return
			}
			http.ServeFile(w, r, a.Static+"/"+name)
			return
		}
		var u store.User
		var e error
		token := ""
		if hasBearer {
			u, e = a.Store.Authenticate(r.Context(), bearer, false)
		} else {
			cookie, err := r.Cookie("leaddesk_session")
			if err != nil {
				write(w, 401, map[string]string{"error": "Entre para acessar a carteira."})
				return
			}
			token = cookie.Value
			u, e = a.Store.Authenticate(r.Context(), token, true)
		}
		if e != nil {
			write(w, 401, map[string]string{"error": "Sessão inválida. Entre novamente."})
			return
		}
		if r.URL.Path == "/api/logout" && r.Method == "POST" {
			if token != "" {
				if e = a.Store.Logout(r.Context(), token); e != nil {
					failure(w, e)
					return
				}
			}
			http.SetCookie(w, &http.Cookie{Name: "leaddesk_session", Value: "", Path: "/", HttpOnly: true, SameSite: http.SameSiteStrictMode, MaxAge: -1})
			write(w, 200, map[string]bool{"ok": true})
			return
		}
		if r.URL.Path == "/api/meta" && r.Method == "GET" {
			filters, e := a.Store.Facets(r.Context(), u)
			if e != nil {
				failure(w, e)
				return
			}
			accounts := []string{}
			q, e := a.Store.DB.Query(r.Context(), "SELECT record_key FROM source_records WHERE table_name='accounts.csv' ORDER BY record_key")
			if e != nil {
				failure(w, e)
				return
			}
			for q.Next() {
				var name string
				if e = q.Scan(&name); e != nil {
					q.Close()
					failure(w, e)
					return
				}
				accounts = append(accounts, name)
			}
			e = q.Err()
			q.Close()
			if e != nil {
				failure(w, e)
				return
			}
			write(w, 200, map[string]any{"user": u, "as_of": "2017-12-31", "key_configured": a.KeyConfigured, "filters": filters, "accounts": accounts, "actions": core.ActionLabels})
			return
		}
		if r.URL.Path == "/api/opportunities" && r.Method == "GET" {
			f := map[string]string{}
			for _, key := range []string{"sales_agent", "manager", "region", "search"} {
				f[key] = r.URL.Query().Get(key)
			}
			f["action"] = r.URL.Query().Get("action")
			requested, _ := strconv.Atoi(r.URL.Query().Get("page"))
			result, e := a.Store.Page(r.Context(), u, f, requested)
			if e != nil {
				failure(w, e)
				return
			}
			write(w, 200, result)
			return
		}
		if strings.HasPrefix(r.URL.Path, "/api/opportunities/") {
			id := strings.TrimPrefix(r.URL.Path, "/api/opportunities/")
			if strings.HasSuffix(id, "/audit") && r.Method == "GET" {
				result, e := a.Store.Audit(r.Context(), u, strings.TrimSuffix(id, "/audit"))
				if e != nil {
					failure(w, e)
					return
				}
				write(w, 200, result)
				return
			}
			if strings.Contains(id, "/") {
				http.NotFound(w, r)
				return
			}
			if r.Method == "GET" {
				v, e := a.Store.Get(r.Context(), u, id)
				if e != nil {
					failure(w, e)
					return
				}
				write(w, 200, v)
				return
			}
			if r.Method == "PATCH" {
				var body struct {
					Version int64  `json:"version"`
					Account string `json:"account"`
				}
				if !decode(w, r, &body) {
					return
				}
				v, e := a.Store.SetAccount(r.Context(), u, id, body.Version, body.Account)
				if e != nil {
					failure(w, e)
					return
				}
				write(w, 200, v)
				return
			}
		}
		if r.URL.Path == "/api/classify" && r.Method == "POST" {
			var body struct {
				ID      string `json:"id"`
				Version int64  `json:"version"`
			}
			if !decode(w, r, &body) {
				return
			}
			j, e := a.Store.Enqueue(r.Context(), u, body.ID, body.Version)
			if e != nil {
				failure(w, e)
				return
			}
			write(w, 202, j)
			return
		}
		write(w, 404, map[string]string{"error": "Rota não encontrada."})
	})
}
func (a API) Server() *http.Server {
	return &http.Server{Addr: a.Host, Handler: a.Handler(), ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 10 * time.Second, WriteTimeout: 30 * time.Second, IdleTimeout: 60 * time.Second, MaxHeaderBytes: 8192}
}
