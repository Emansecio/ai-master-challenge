package service

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"leaddesk/internal/core"
	"leaddesk/internal/store"
	"log"
	"net/http"
	"time"
)

type Client struct {
	Key      string
	HTTP     *http.Client
	Endpoint string
}
type Failure struct {
	Message string
	Retry   bool
}

func (e *Failure) Error() string { return e.Message }
func (c Client) Evaluate(ctx context.Context, j store.Job) (core.Response, error) {
	var response core.Response
	if c.Key == "" {
		return response, &Failure{"Credencial Jev não configurada no servidor.", false}
	}
	payload := map[string]any{"model": core.Model, "state": j.State, "questions": j.Policy.Questions, "providerOptions": map[string]any{"gateway": map[string]any{"only": []string{"typesafe-ai"}}}}
	b, e := json.Marshal(payload)
	if e != nil {
		return response, e
	}
	endpoint := c.Endpoint
	if endpoint == "" {
		endpoint = "https://ai-gateway.vercel.sh/v1/evaluate"
	}
	req, e := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, bytes.NewReader(b))
	if e != nil {
		return response, e
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+c.Key)
	client := c.HTTP
	if client == nil {
		client = &http.Client{Timeout: 30 * time.Second, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	}
	res, e := client.Do(req)
	if e != nil {
		return response, &Failure{"Não foi possível consultar o Jev dentro do prazo.", true}
	}
	defer res.Body.Close()
	if res.StatusCode != 200 {
		return response, &Failure{fmt.Sprintf("Jev indisponível (HTTP %d).", res.StatusCode), res.StatusCode == 429 || res.StatusCode >= 500}
	}
	if e = json.NewDecoder(io.LimitReader(res.Body, 1048576)).Decode(&response); e != nil {
		return response, &Failure{"Resposta Jev inválida.", false}
	}
	if e = core.Validate(response, j.Policy, j.State); e != nil {
		return response, &Failure{e.Error(), false}
	}
	return response, nil
}
func Work(ctx context.Context, s *store.Store, c Client, interval time.Duration) {
	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			j, e := s.Claim(ctx, interval)
			if e != nil {
				if ctx.Err() == nil {
					log.Print("worker: banco temporariamente indisponível")
				}
				continue
			}
			if j == nil {
				continue
			}
			start := time.Now()
			callCtx, cancel := context.WithTimeout(ctx, 30*time.Second)
			response, e := c.Evaluate(callCtx, *j)
			cancel()
			// On shutdown retain the lease for another process to recover, rather than misreport completion.
			if ctx.Err() != nil {
				return
			}
			if e != nil {
				retry := false
				if f, ok := e.(*Failure); ok {
					retry = f.Retry
				}
				if err := s.Fail(ctx, *j, e.Error(), retry, time.Since(start)); err != nil {
					log.Print("worker: falha ao persistir tentativa")
				}
			} else if e = s.Complete(ctx, *j, response, "consulta_ao_vivo", time.Since(start)); e != nil {
				log.Print("worker: resultado não publicado; lease ou banco indisponível")
			}
		}
	}
}
