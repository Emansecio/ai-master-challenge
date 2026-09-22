package main

import (
	"context"
	"flag"
	"fmt"
	"leaddesk/internal/config"
	"leaddesk/internal/core"
	"leaddesk/internal/service"
	"leaddesk/internal/store"
	"leaddesk/internal/web"
	"log"
	"os"
	"os/signal"
	"time"
)

func main() {
	if e := run(); e != nil {
		log.Fatal(e)
	}
}
func run() error {
	mode := flag.String("mode", "serve", "setup ou serve")
	port := flag.Int("port", 8765, "porta local")
	data := flag.String("data", "../analise/dados/crm-sales-predictive-analytics.zip", "dataset auditado")
	epoch := flag.String("model-epoch", "2026-09-22", "identidade de revalidação do modelo")
	flag.Parse()
	if e := config.Load(".local/dev.env"); e != nil {
		return e
	}
	if e := config.Load(".env"); e != nil {
		return e
	}
	if e := config.Load("../analise/.env"); e != nil {
		return e
	}
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt)
	defer cancel()
	p, e := core.LoadPolicy("policy.json", *epoch)
	if e != nil {
		return e
	}
	url := os.Getenv("DATABASE_URL")
	if *mode == "setup" {
		url = os.Getenv("ADMIN_DATABASE_URL")
	}
	s, e := store.Open(ctx, url)
	if e != nil {
		return e
	}
	defer s.DB.Close()
	if *mode == "setup" {
		if e = s.Migrate(ctx, os.Getenv("APP_DB_PASSWORD")); e != nil {
			return e
		}
		d, e := core.LoadDataset(*data)
		if e != nil {
			return e
		}
		if e = s.Seed(ctx, d, p, ".local/access-codes.json"); e != nil {
			return e
		}
		n, e := s.ImportReceipts(ctx, "../analise/resultados/jev-vercel-v02", "policy.json", p)
		if e != nil {
			return e
		}
		fmt.Printf("Setup concluído: %d oportunidades; %d recibos Jev importados. Códigos em .local/access-codes.json.\n", len(d.Opportunities), n)
		return nil
	}
	if *mode != "serve" {
		return fmt.Errorf("modo desconhecido")
	}
	var active string
	if e = s.DB.QueryRow(ctx, "SELECT policy_hash FROM settings WHERE id=true").Scan(&active); e != nil {
		return fmt.Errorf("execute o setup primeiro")
	}
	if active != p.Hash {
		return fmt.Errorf("política diferente da ativa; execute setup para ativar")
	}
	key := os.Getenv("AI_GATEWAY_API_KEY")
	for i := 0; i < 2; i++ {
		go service.Work(ctx, s, service.Client{Key: key}, 2*time.Second)
	}
	api := web.API{Store: s, KeyConfigured: key != "", Static: "static", Host: fmt.Sprintf("127.0.0.1:%d", *port)}
	server := api.Server()
	go func() {
		<-ctx.Done()
		shutdown, done := context.WithTimeout(context.Background(), 5*time.Second)
		defer done()
		server.Shutdown(shutdown)
	}()
	fmt.Printf("Lead Desk em http://%s — Go + PostgreSQL; acesso local autenticado.\n", api.Host)
	e = server.ListenAndServe()
	if ctx.Err() != nil {
		return nil
	}
	return e
}
