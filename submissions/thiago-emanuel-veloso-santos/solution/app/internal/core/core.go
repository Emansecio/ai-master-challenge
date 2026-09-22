package core

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"time"
)

const Model = "typesafe-ai/jev"
const DatasetSHA = "74d535826330b616758ebb6bb393abf701a5126364a72fbe71003cb6a7a87a9c"

type State struct {
	AsOf              string   `json:"as_of"`
	Stage             string   `json:"stage"`
	AccountIdentified bool     `json:"account_identified"`
	EngageDate        *string  `json:"engage_date"`
	AgeDays           *int     `json:"age_days"`
	Product           string   `json:"product"`
	CatalogPrice      int      `json:"catalog_price"`
	Reference         float64  `json:"reference_p90_days"`
	Old               bool     `json:"age_exceeds_reference_p90"`
	HistoryN          int      `json:"historical_product_closed_n"`
	ReferenceScope    string   `json:"duration_reference_scope"`
	Unavailable       []string `json:"unavailable"`
}
type Decision struct {
	Qualification string `json:"qualification"`
	Action        string `json:"next_action"`
}
type Opportunity struct {
	ID                 string   `json:"id"`
	Version            int64    `json:"version"`
	Account            string   `json:"account"`
	Sector             string   `json:"sector"`
	Agent              string   `json:"sales_agent"`
	Manager            string   `json:"manager"`
	Region             string   `json:"region"`
	State              State    `json:"state"`
	Decision           Decision `json:"decision"`
	Priority           int      `json:"priority"`
	ActionLabel        string   `json:"action_label"`
	QualificationLabel string   `json:"qualification_label"`
	Reasons            []string `json:"reasons"`
}
type Question struct {
	Type         string            `json:"type"`
	Instructions string            `json:"instructions"`
	Criteria     map[string]string `json:"criteria"`
}
type Policy struct {
	Version   string              `json:"policy_version"`
	Questions map[string]Question `json:"questions"`
	Hash      string              `json:"-"`
	Epoch     string              `json:"-"`
}
type Answer struct {
	Type          string             `json:"type"`
	Choice        string             `json:"choice"`
	Probabilities map[string]float64 `json:"probabilities"`
	Confidence    *float64           `json:"confidence"`
}
type Response struct {
	Model    string            `json:"model"`
	Answers  map[string]Answer `json:"answers"`
	Usage    json.RawMessage   `json:"usage,omitempty"`
	Metadata json.RawMessage   `json:"providerMetadata,omitempty"`
}

func Hash(v any) string {
	b, _ := json.Marshal(v)
	h := sha256.Sum256(b)
	return hex.EncodeToString(h[:])
}
func LoadPolicy(path, epoch string) (Policy, error) {
	var p Policy
	b, e := os.ReadFile(path)
	if e != nil {
		return p, e
	}
	if e = json.Unmarshal(b, &p); e != nil {
		return p, e
	}
	if len(p.Questions) != 2 || len(p.Questions["qualification"].Criteria) != 4 || len(p.Questions["next_action"].Criteria) != 5 {
		return p, fmt.Errorf("contrato de política inválido")
	}
	p.Epoch = epoch
	p.Hash = Hash(struct {
		Version      string
		Questions    map[string]Question
		Model, Epoch string
	}{p.Version, p.Questions, Model, epoch})
	return p, nil
}
func Decide(s State) Decision {
	invalid := s.Reference <= 0 || math.IsNaN(s.Reference) || math.IsInf(s.Reference, 0) || (s.Stage != "Engaging" && s.Stage != "Prospecting")
	at, e := time.Parse(time.DateOnly, s.AsOf)
	invalid = invalid || e != nil
	if s.Stage == "Engaging" {
		if s.AgeDays == nil || s.EngageDate == nil {
			invalid = true
		} else {
			engaged, err := time.Parse(time.DateOnly, *s.EngageDate)
			invalid = invalid || err != nil || *s.AgeDays < 0 || int(at.Sub(engaged).Hours()/24) != *s.AgeDays || s.Old != (float64(*s.AgeDays) > s.Reference)
		}
	} else if s.AgeDays != nil || s.EngageDate != nil || s.Old {
		invalid = true
	}
	if invalid {
		return Decision{"human_review", "human_review"}
	}
	if !s.AccountIdentified {
		return Decision{"incomplete_profile", "identify_account"}
	}
	if s.Stage == "Prospecting" {
		return Decision{"discovery_required", "qualify_prospect"}
	}
	if s.Old {
		return Decision{"negotiation_reviewable", "review_old_negotiation"}
	}
	return Decision{"negotiation_reviewable", "continue_negotiation_review"}
}

var ActionLabels = map[string]string{"human_review": "Revisão humana", "review_old_negotiation": "Revisar negociação", "qualify_prospect": "Qualificar prospecção", "continue_negotiation_review": "Definir próximo passo", "identify_account": "Completar cadastro"}
var priorities = map[string]int{"human_review": 0, "review_old_negotiation": 1, "qualify_prospect": 2, "continue_negotiation_review": 3, "identify_account": 4}

func Decorate(o *Opportunity) {
	o.Decision = Decide(o.State)
	o.Priority = priorities[o.Decision.Action]
	o.ActionLabel = ActionLabels[o.Decision.Action]
	o.QualificationLabel = map[string]string{"human_review": "Revisão humana", "incomplete_profile": "Perfil incompleto", "discovery_required": "Qualificação pendente", "negotiation_reviewable": "Negociação para revisar"}[o.Decision.Qualification]
	reason := map[string]string{"human_review": "Revise os dados inconsistentes antes de seguir.", "identify_account": "Identifique a empresa antes de avaliar o perfil da oportunidade.", "qualify_prospect": "Levante a necessidade, o interlocutor e o próximo passo desta prospecção.", "review_old_negotiation": "Confirme o status: a duração ultrapassa a referência histórica do produto.", "continue_negotiation_review": "Confirme o próximo passo comercial desta negociação."}[o.Decision.Action]
	o.Reasons = []string{reason}
	if o.State.AgeDays != nil {
		o.Reasons = append(o.Reasons, fmt.Sprintf("%d dias em negociação; referência histórica de %.0f dias. Idade não significa inatividade.", *o.State.AgeDays, o.State.Reference))
	}
	o.Reasons = append(o.Reasons, "Necessidade, orçamento, intenção e último contato não estão disponíveis nesta base.")
}
func Validate(r Response, p Policy, s State) error {
	if r.Model != Model || len(r.Answers) != len(p.Questions) {
		return fmt.Errorf("modelo ou perguntas fora do contrato")
	}
	expected := Decide(s)
	want := map[string]string{"qualification": expected.Qualification, "next_action": expected.Action}
	for name, q := range p.Questions {
		a, ok := r.Answers[name]
		if !ok || a.Type != "choice" || len(a.Probabilities) != len(q.Criteria) || a.Confidence == nil {
			return fmt.Errorf("resposta incompleta")
		}
		sum, max := 0.0, 0.0
		for choice := range q.Criteria {
			v, ok := a.Probabilities[choice]
			if !ok || !prob(v) {
				return fmt.Errorf("probabilidades inválidas")
			}
			sum += v
			if v > max {
				max = v
			}
		}
		_, known := q.Criteria[a.Choice]
		if !known || !prob(*a.Confidence) || math.Abs(sum-1) > .0200001 || a.Probabilities[a.Choice] != max {
			return fmt.Errorf("escolha ou confiança inválida")
		}
		if a.Choice != want[name] {
			return fmt.Errorf("resposta diverge da política; manter regra local")
		}
	}
	return nil
}
func prob(v float64) bool { return !math.IsNaN(v) && !math.IsInf(v, 0) && v >= 0 && v <= 1 }
