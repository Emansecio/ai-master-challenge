package store

import (
	"bufio"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"leaddesk/internal/core"
	"os"
	"path/filepath"
	"time"
)

func (s *Store) ImportReceipts(ctx context.Context, folder, contractPath string, p core.Policy) (int, error) {
	raw, e := os.ReadFile(filepath.Join(folder, "manifesto.json"))
	if os.IsNotExist(e) {
		return 0, nil
	}
	if e != nil {
		return 0, e
	}
	var m struct {
		Hash      string `json:"questions_sha256"`
		StartedAt string `json:"started_at"`
		Model     string `json:"requested_model"`
	}
	if e = json.Unmarshal(raw, &m); e != nil {
		return 0, e
	}
	started, e := time.Parse(time.RFC3339Nano, m.StartedAt)
	if e != nil || p.Epoch != started.Format(time.DateOnly) || m.Model != core.Model {
		// A new validation epoch must never be prefilled with old benchmark answers.
		return 0, nil
	}
	contract, e := os.ReadFile(contractPath)
	if e != nil {
		return 0, e
	}
	h := sha256.Sum256(contract)
	if hex.EncodeToString(h[:]) != m.Hash {
		return 0, nil
	}
	f, e := os.Open(filepath.Join(folder, "chamadas.jsonl"))
	if e != nil {
		return 0, e
	}
	defer f.Close()
	scan := bufio.NewScanner(f)
	scan.Buffer(make([]byte, 65536), 1048576)
	n := 0
	for scan.Scan() {
		var r struct {
			ID       string        `json:"case_id"`
			Status   int           `json:"http_status"`
			Errors   []string      `json:"validation_errors"`
			State    core.State    `json:"state"`
			Response core.Response `json:"response"`
			At       string        `json:"timestamp"`
		}
		if e = json.Unmarshal(scan.Bytes(), &r); e != nil {
			return n, e
		}
		if r.Status != 200 || len(r.Errors) > 0 {
			continue
		}
		v, e := s.Get(ctx, User{Role: "admin"}, r.ID)
		if e != nil {
			return n, e
		}
		if core.Hash(r.State) != core.Hash(v.State) || core.Validate(r.Response, p, v.State) != nil || v.Version != 1 {
			continue
		}
		response, _ := json.Marshal(r.Response)
		tag, e := s.DB.Exec(ctx, `INSERT INTO classifications(opportunity_id,version,policy_hash,response,origin,current_at_commit,created_at)
  VALUES($1,1,$2,$3,'ensaio_validado',true,$4::timestamptz) ON CONFLICT DO NOTHING`, r.ID, p.Hash, response, r.At)
		if e != nil {
			return n, e
		}
		n += int(tag.RowsAffected())
	}
	return n, scan.Err()
}
