package store

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	_ "embed"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/jackc/pgx/v5/pgxpool"
	"leaddesk/internal/core"
	"os"
	"sort"
	"strings"
	"time"
)

//go:embed schema.sql
var schema string
var ErrConflict = errors.New("a oportunidade foi alterada; atualize a tela")
var ErrForbidden = errors.New("oportunidade indisponível para este acesso")

type Store struct{ DB *pgxpool.Pool }
type User struct {
	ID    string `json:"id"`
	Role  string `json:"role"`
	Scope string `json:"scope"`
}
type View struct {
	core.Opportunity
	Classification json.RawMessage `json:"classification"`
	Status         string          `json:"status"`
	Error          string          `json:"error,omitempty"`
}

func Token() string {
	b := make([]byte, 32)
	if _, e := rand.Read(b); e != nil {
		panic(e)
	}
	return hex.EncodeToString(b)
}
func TokenHash(s string) string { h := sha256.Sum256([]byte(s)); return hex.EncodeToString(h[:]) }
func Open(ctx context.Context, url string) (*Store, error) {
	c, e := pgxpool.ParseConfig(url)
	if e != nil {
		return nil, fmt.Errorf("configuração do banco inválida")
	}
	c.MaxConns = 12
	c.ConnConfig.ConnectTimeout = 5 * time.Second
	p, e := pgxpool.NewWithConfig(ctx, c)
	if e != nil {
		return nil, e
	}
	if e = p.Ping(ctx); e != nil {
		p.Close()
		return nil, fmt.Errorf("banco indisponível")
	}
	return &Store{p}, nil
}
func (s *Store) Migrate(ctx context.Context, password string) error {
	tx, e := s.DB.Begin(ctx)
	if e != nil {
		return e
	}
	defer tx.Rollback(ctx)
	if _, e = tx.Exec(ctx, "SELECT pg_advisory_xact_lock(340003)"); e != nil {
		return e
	}
	if _, e = tx.Exec(ctx, schema); e != nil {
		return e
	}
	var exists bool
	e = tx.QueryRow(ctx, "SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='leaddesk')").Scan(&exists)
	if e != nil {
		return e
	}
	if !exists {
		if len(password) != 64 {
			return fmt.Errorf("senha local de runtime ausente")
		}
		for _, c := range password {
			if !strings.ContainsRune("0123456789abcdef", c) {
				return fmt.Errorf("formato de senha inválido")
			}
		}
		if _, e = tx.Exec(ctx, "CREATE ROLE leaddesk LOGIN PASSWORD '"+password+"'"); e != nil {
			return e
		}
	}
	_, e = tx.Exec(ctx, `GRANT CONNECT ON DATABASE leaddesk TO leaddesk; GRANT USAGE ON SCHEMA public TO leaddesk;
	GRANT SELECT ON ALL TABLES IN SCHEMA public TO leaddesk;
	GRANT UPDATE(id) ON settings TO leaddesk;
 GRANT INSERT, UPDATE ON opportunities, jobs, provider_gate TO leaddesk;
 GRANT INSERT ON opportunity_versions, classifications, job_attempts TO leaddesk;
 GRANT INSERT, DELETE ON sessions TO leaddesk;`)
	if e != nil {
		return e
	}
	return tx.Commit(ctx)
}
func (s *Store) Seed(ctx context.Context, d core.Dataset, p core.Policy, codesPath string) error {
	tx, e := s.DB.Begin(ctx)
	if e != nil {
		return e
	}
	defer tx.Rollback(ctx)
	if _, e = tx.Exec(ctx, "SELECT pg_advisory_xact_lock(340003)"); e != nil {
		return e
	}
	keys := map[string]string{"accounts.csv": "account", "products.csv": "product", "sales_teams.csv": "sales_agent", "sales_pipeline.csv": "opportunity_id"}
	for table, records := range d.Tables {
		for _, r := range records {
			b, _ := json.Marshal(r)
			if _, e = tx.Exec(ctx, "INSERT INTO source_records VALUES($1,$2,$3) ON CONFLICT DO NOTHING", table, r[keys[table]], b); e != nil {
				return e
			}
		}
	}
	for _, o := range d.Opportunities {
		b, _ := json.Marshal(o)
		result, e := tx.Exec(ctx, "INSERT INTO opportunities(id,version,doc) VALUES($1,1,$2) ON CONFLICT DO NOTHING", o.ID, b)
		if e != nil {
			return e
		}
		if result.RowsAffected() > 0 {
			if _, e = tx.Exec(ctx, "INSERT INTO opportunity_versions(opportunity_id,version,doc,actor) VALUES($1,1,$2,'dataset')", o.ID, b); e != nil {
				return e
			}
		}
	}
	b, _ := json.Marshal(p)
	if _, e = tx.Exec(ctx, "INSERT INTO settings VALUES(true,$1,$2) ON CONFLICT(id) DO UPDATE SET policy_hash=excluded.policy_hash,policy=excluded.policy", p.Hash, b); e != nil {
		return e
	}
	var count int
	if e = tx.QueryRow(ctx, "SELECT count(*) FROM users").Scan(&count); e != nil {
		return e
	}
	if count == 0 {
		users := []User{{"admin", "admin", ""}, {"gestor", "manager", d.Opportunities[0].Manager}, {"vendedor", "seller", d.Opportunities[0].Agent}}
		codes := map[string]string{}
		for _, u := range users {
			token := Token()
			codes[u.ID] = token
			if _, e = tx.Exec(ctx, "INSERT INTO users VALUES($1,$2,$3,$4)", u.ID, TokenHash(token), u.Role, u.Scope); e != nil {
				return e
			}
		}
		b, _ := json.MarshalIndent(codes, "", "  ")
		if e = os.WriteFile(codesPath, b, 0600); e != nil {
			return e
		}
	}
	return tx.Commit(ctx)
}
func allowed(u User, o core.Opportunity) bool {
	return u.Role == "admin" || (u.Role == "manager" && u.Scope == o.Manager) || (u.Role == "seller" && u.Scope == o.Agent)
}
func (s *Store) Authenticate(ctx context.Context, token string, session bool) (User, error) {
	var u User
	q := "SELECT id,role,scope FROM users WHERE token_hash=$1"
	if session {
		q = "SELECT u.id,u.role,u.scope FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.token_hash=$1 AND s.expires_at>now()"
	}
	e := s.DB.QueryRow(ctx, q, TokenHash(token)).Scan(&u.ID, &u.Role, &u.Scope)
	return u, e
}
func (s *Store) Session(ctx context.Context, u User) (string, error) {
	token := Token()
	_, e := s.DB.Exec(ctx, "INSERT INTO sessions VALUES($1,$2,now()+interval '8 hours')", TokenHash(token), u.ID)
	return token, e
}
func (s *Store) Logout(ctx context.Context, token string) error {
	_, e := s.DB.Exec(ctx, "DELETE FROM sessions WHERE token_hash=$1", TokenHash(token))
	return e
}

const viewQuery = `SELECT o.doc, coalesce(c.response - 'providerMetadata' - 'usage','null'::jsonb),
 CASE WHEN c.opportunity_id IS NOT NULL THEN 'classified' WHEN j.id IS NOT NULL THEN j.status
 WHEN EXISTS(SELECT 1 FROM classifications old WHERE old.opportunity_id=o.id) THEN 'stale' ELSE 'unclassified' END,
 coalesce(j.error,'') FROM opportunities o CROSS JOIN settings s
 LEFT JOIN classifications c ON c.opportunity_id=o.id AND c.version=o.version AND c.policy_hash=s.policy_hash
 LEFT JOIN jobs j ON j.opportunity_id=o.id AND j.version=o.version AND j.policy_hash=s.policy_hash `

func (s *Store) Get(ctx context.Context, u User, id string) (View, error) {
	var v View
	var doc []byte
	e := s.DB.QueryRow(ctx, viewQuery+`WHERE o.id=$1`, id).Scan(&doc, &v.Classification, &v.Status, &v.Error)
	if e != nil {
		return v, e
	}
	if e = json.Unmarshal(doc, &v.Opportunity); e != nil {
		return v, e
	}
	if !allowed(u, v.Opportunity) {
		return View{}, ErrForbidden
	}
	return v, nil
}
func (s *Store) List(ctx context.Context, u User, filters map[string]string) ([]View, error) {
	// Scope is applied in SQL before user-supplied filters, never inferred from them.
	rows, e := s.DB.Query(ctx, viewQuery+`WHERE ($1='admin' OR ($1='manager' AND o.doc->>'manager'=$2) OR ($1='seller' AND o.doc->>'sales_agent'=$2))
 AND ($3='' OR o.doc->>'sales_agent'=$3) AND ($4='' OR o.doc->>'manager'=$4) AND ($5='' OR o.doc->>'region'=$5)
 AND ($6='' OR concat_ws(' ',o.id,o.doc->>'account',o.doc->>'sales_agent',o.doc->'state'->>'product') ILIKE '%'||$6||'%')
 AND ($7='' OR o.doc->'decision'->>'next_action'=$7)`, u.Role, u.Scope, filters["sales_agent"], filters["manager"], filters["region"], filters["search"], filters["action"])
	if e != nil {
		return nil, e
	}
	out := []View{}
	for rows.Next() {
		var v View
		var doc []byte
		if e = rows.Scan(&doc, &v.Classification, &v.Status, &v.Error); e != nil {
			rows.Close()
			return nil, e
		}
		if e = json.Unmarshal(doc, &v.Opportunity); e != nil {
			rows.Close()
			return nil, e
		}
		out = append(out, v)
	}
	e = rows.Err()
	rows.Close()
	if e != nil {
		return nil, e
	}
	sort.Slice(out, func(i, j int) bool {
		a, b := out[i], out[j]
		if a.Priority != b.Priority {
			return a.Priority < b.Priority
		}
		if a.Priority == 1 && a.State.AgeDays != nil && b.State.AgeDays != nil {
			x, y := float64(*a.State.AgeDays)/a.State.Reference, float64(*b.State.AgeDays)/b.State.Reference
			if x != y {
				return x > y
			}
		}
		if a.State.CatalogPrice != b.State.CatalogPrice {
			return a.State.CatalogPrice > b.State.CatalogPrice
		}
		return a.ID < b.ID
	})
	return out, nil
}
func (s *Store) SetAccount(ctx context.Context, u User, id string, version int64, account string) (View, error) {
	tx, e := s.DB.Begin(ctx)
	if e != nil {
		return View{}, e
	}
	defer tx.Rollback(ctx)
	var doc []byte
	e = tx.QueryRow(ctx, "SELECT doc FROM opportunities WHERE id=$1 FOR UPDATE", id).Scan(&doc)
	if e != nil {
		return View{}, e
	}
	var o core.Opportunity
	if e = json.Unmarshal(doc, &o); e != nil {
		return View{}, e
	}
	if !allowed(u, o) {
		return View{}, ErrForbidden
	}
	if o.Version != version {
		return View{}, ErrConflict
	}
	sector := ""
	if account != "" {
		if e = tx.QueryRow(ctx, "SELECT doc->>'sector' FROM source_records WHERE table_name='accounts.csv' AND record_key=$1", account).Scan(&sector); e != nil {
			return View{}, fmt.Errorf("conta inexistente")
		}
	}
	if o.Account == account {
		// Release the transaction's connection before reading through the pool.
		if e = tx.Rollback(ctx); e != nil {
			return View{}, e
		}
		return s.Get(ctx, u, id)
	}
	o.Account = account
	o.Sector = sector
	o.Version++
	o.State.AccountIdentified = account != ""
	core.Decorate(&o)
	doc, _ = json.Marshal(o)
	if _, e = tx.Exec(ctx, "UPDATE opportunities SET version=$2,doc=$3,updated_at=now() WHERE id=$1", id, o.Version, doc); e != nil {
		return View{}, e
	}
	if _, e = tx.Exec(ctx, "INSERT INTO opportunity_versions(opportunity_id,version,doc,actor) VALUES($1,$2,$3,$4)", id, o.Version, doc, u.ID); e != nil {
		return View{}, e
	}
	if e = tx.Commit(ctx); e != nil {
		return View{}, e
	}
	return s.Get(ctx, u, id)
}
