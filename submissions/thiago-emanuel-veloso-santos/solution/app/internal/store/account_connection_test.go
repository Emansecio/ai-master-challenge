package store

import (
	"context"
	"github.com/jackc/pgx/v5/pgxpool"
	"testing"
	"time"
)

func TestUnchangedAccountReleasesConnection(t *testing.T) {
	reset(t)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	config := testStore.DB.Config()
	config.MaxConns = 1
	pool, err := pgxpool.NewWithConfig(ctx, config)
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	limited := &Store{DB: pool}
	o := testDataset.Opportunities[0]
	view, err := limited.SetAccount(ctx, User{Role: "admin"}, o.ID, o.Version, o.Account)
	if err != nil {
		t.Fatalf("unchanged account must complete using one available connection: %v", err)
	}
	if view.Version != o.Version || view.Account != o.Account {
		t.Fatal("an unchanged account must preserve its version and value")
	}
	var versions int
	if err = pool.QueryRow(ctx, "SELECT count(*) FROM opportunity_versions WHERE opportunity_id=$1", o.ID).Scan(&versions); err != nil {
		t.Fatal(err)
	}
	if versions != 1 {
		t.Fatalf("unchanged account created a version: %d", versions)
	}
}
