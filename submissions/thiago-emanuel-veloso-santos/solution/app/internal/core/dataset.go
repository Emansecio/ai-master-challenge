package core

import (
	"archive/zip"
	"bytes"
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"fmt"
	"os"
	"sort"
	"strconv"
	"time"
)

type Dataset struct {
	Tables        map[string][]map[string]string
	Opportunities []Opportunity
}

func LoadDataset(path string) (Dataset, error) {
	d := Dataset{Tables: map[string][]map[string]string{}}
	b, e := os.ReadFile(path)
	if e != nil {
		return d, e
	}
	hash := sha256.Sum256(b)
	if hex.EncodeToString(hash[:]) != DatasetSHA {
		return d, fmt.Errorf("dataset diferente da versão auditada")
	}
	archive, e := zip.NewReader(bytes.NewReader(b), int64(len(b)))
	if e != nil {
		return d, e
	}
	for _, f := range archive.File {
		if f.Name == "metadata.csv" {
			continue
		}
		reader, e := f.Open()
		if e != nil {
			return d, e
		}
		records, e := csv.NewReader(reader).ReadAll()
		reader.Close()
		if e != nil {
			return d, e
		}
		for _, record := range records[1:] {
			row := map[string]string{}
			for i, key := range records[0] {
				row[key] = record[i]
			}
			d.Tables[f.Name] = append(d.Tables[f.Name], row)
		}
	}
	index := func(name, key string) map[string]map[string]string {
		m := map[string]map[string]string{}
		for _, r := range d.Tables[name] {
			m[r[key]] = r
		}
		return m
	}
	accounts, products, teams := index("accounts.csv", "account"), index("products.csv", "product"), index("sales_teams.csv", "sales_agent")
	durations := map[string][]float64{}
	all := []float64{}
	at, _ := time.Parse(time.DateOnly, "2017-12-31")
	productName := func(s string) string {
		if s == "GTXPro" {
			return "GTX Pro"
		}
		return s
	}
	for _, r := range d.Tables["sales_pipeline.csv"] {
		if r["deal_stage"] != "Won" && r["deal_stage"] != "Lost" {
			continue
		}
		closed, e1 := time.Parse(time.DateOnly, r["close_date"])
		engaged, e2 := time.Parse(time.DateOnly, r["engage_date"])
		if e1 != nil || e2 != nil {
			return d, fmt.Errorf("datas históricas inválidas")
		}
		if closed.After(at) {
			continue
		}
		age := closed.Sub(engaged).Hours() / 24
		name := productName(r["product"])
		durations[name] = append(durations[name], age)
		all = append(all, age)
	}
	p90 := func(xs []float64) float64 {
		sort.Float64s(xs)
		pos := float64(len(xs)-1) * .9
		i := int(pos)
		if i == len(xs)-1 {
			return xs[i]
		}
		return xs[i] + (xs[i+1]-xs[i])*(pos-float64(i))
	}
	global := p90(all)
	refs := map[string]float64{}
	for name, xs := range durations {
		refs[name] = global
		if len(xs) >= 30 {
			refs[name] = p90(xs)
		}
	}
	for _, r := range d.Tables["sales_pipeline.csv"] {
		if r["deal_stage"] != "Engaging" && r["deal_stage"] != "Prospecting" {
			continue
		}
		name := productName(r["product"])
		product, ok := products[name]
		if !ok {
			return d, fmt.Errorf("produto sem catálogo")
		}
		team, ok := teams[r["sales_agent"]]
		if !ok {
			return d, fmt.Errorf("vendedor sem equipe")
		}
		price, e := strconv.Atoi(product["sales_price"])
		if e != nil {
			return d, e
		}
		s := State{AsOf: "2017-12-31", Stage: r["deal_stage"], AccountIdentified: r["account"] != "", Product: name, CatalogPrice: price, Reference: refs[name], HistoryN: len(durations[name]), ReferenceScope: "product", Unavailable: []string{"need", "budget", "authority", "intent", "last_contact", "next_contact_date"}}
		if s.HistoryN < 30 {
			s.ReferenceScope = "global_fallback"
		}
		if r["engage_date"] != "" {
			dateString := r["engage_date"]
			start, e := time.Parse(time.DateOnly, dateString)
			if e != nil {
				return d, e
			}
			age := int(at.Sub(start).Hours() / 24)
			s.EngageDate = &dateString
			s.AgeDays = &age
			s.Old = float64(age) > s.Reference
		}
		o := Opportunity{ID: r["opportunity_id"], Version: 1, Account: r["account"], Sector: accounts[r["account"]]["sector"], Agent: r["sales_agent"], Manager: team["manager"], Region: team["regional_office"], State: s}
		Decorate(&o)
		d.Opportunities = append(d.Opportunities, o)
	}
	if len(d.Opportunities) != 2089 {
		return d, fmt.Errorf("contagem de oportunidades inesperada")
	}
	return d, nil
}
