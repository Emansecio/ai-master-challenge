## REQ-02: lógica de priorização

> "Precisa ter **lógica de scoring/priorização** (não é só ordenar por valor)"
>
> Fonte: ai-master-challenge/challenges/build-003-lead-scorer/README.md:L66

**Verdict:** implemented · confidence: high

**What this demands of an implementation:** a ordem apresentada ao usuário precisa incorporar critérios além do valor da oportunidade. O requisito permite priorização e não exige um escore numérico de propensão de compra.

---

**Where enforcement lives:**

Em `app/internal/core/core.go:L98-L124`, `Decide` verifica validade do estado, identificação da conta, estágio e duração acima da referência histórica. Seus cinco resultados recebem prioridades explícitas em `app/internal/core/core.go:L128-L132`: revisão humana 0, revisão de negociação antiga 1, qualificação de prospecção 2, próximo passo 3 e identificação de conta 4. A precedência de classificação de um registro e a ordem relativa das filas são conceitos diferentes; ambas estão explícitas no código.

```sql
-- app/internal/store/read.go:L11-L13
(doc->>'priority')::int,
CASE WHEN (doc->>'priority')::int=1 THEN (doc->'state'->>'age_days')::float8 / NULLIF((doc->'state'->>'reference_p90_days')::float8,0) ELSE 0 END DESC NULLS LAST,
(doc->'state'->>'catalog_price')::int DESC, id COLLATE "C"
```

Essa ordem é aplicada antes de `LIMIT 20` em `app/internal/store/read.go:L37-L38`. O agrupamento JSON preserva o ordinal em `L46`. Portanto, o preço de catálogo é apenas um desempate após a prioridade da ação e, nas negociações antigas, após a razão entre idade e referência histórica.

O histórico de duração vem das oportunidades encerradas até 2017-12-31, com percentil 90 interpolado e referência por produto quando há pelo menos 30 registros: `app/internal/core/dataset.go:L73-L106`. A idade e o indicador de ultrapassagem são calculados em `L128-L137`; a classificação é incorporada a cada oportunidade em `L139-L141`.

---

**Paths walked:**

1. Importação: `LoadDataset` calcula referências e estado, chama `Decorate` (`dataset.go:L73-L141`), que chama `Decide` e atribui a prioridade (`core.go:L98-L132`). `Store.Seed` grava o documento completo em `store.go:L122-L132`.
2. Leitura paginada: `GET /api/opportunities` chama `Store.Page` (`web/api.go:L159-L172`). Os filtros e escopos antecedem a ordenação, mantendo os mesmos critérios em todas as seleções (`store/read.go:L30-L49`). A interface recebe a página e percorre `data.rows` sem reordená-la (`frontend/app.ts:L123-L125`, `L135`).
3. Leitura completa: `Store.List` aplica a mesma prioridade, razão de duração, preço e identificador em Go (`store/store.go:L231-L246`).
4. Alteração da conta: `Store.SetAccount` atualiza a identificação, recalcula `Decorate` e persiste o documento e sua versão em uma transação (`store/store.go:L279-L292`).
5. Estado inválido recebe revisão humana; conta ausente recebe identificação; prospecção identificada recebe qualificação; negociação identificada acima da referência recebe revisão; negociação válida restante recebe próximo passo (`core.go:L98-L124`). Não há caminho válido de `Decide` sem ação prevista no mapa de prioridades (`L128`).
6. A resposta do Jev não substitui essa lógica: `Validate` exige concordância com `Decide` (`core.go:L146-L169`), e a leitura mantém a ordenação pelo documento da oportunidade mesmo quando existe classificação (`store/read.go:L37-L45`).

---

**Searched:**

1. `lógica de scoring|priori|priority|ORDER BY|sort` em enunciado e `app/internal`: localizou o requisito na linha 66, o mapa de prioridades em `core.go`, a ordenação SQL em `read.go` e a ordenação completa em `store.go`.
2. A primeira busca incluiu `app/web/src`, caminho inexistente. `rg --files app` localizou o frontend real em `app/frontend`, que foi lido nas linhas de carregamento e renderização acima.
3. `Page\(|List\(|Priority|priority|order|sort|Decide` em `app/internal/core` e `app/internal/store`, limitado a `*test.go`: localizou verificações de decisão em `core_test.go:L58-L74`, comparação entre lista e página em `read_test.go:L19-L60` e preservação de ordem em `read_test.go:L74-L82`. Esses testes foram identificados, mas não executados nesta verificação estática.
4. Leitura de `app/policy.json`: a precedência de decisões descrita em `questions.next_action.instructions` corresponde às ramificações lidas em `Decide`. O requisito avaliado não exige que a regra seja editável por configuração.

---

**How the verdict was reached:** existe lógica explícita que antecede o preço e chega à lista efetivamente renderizada. Os caminhos de importação, leitura paginada, leitura completa e atualização cadastral preservam essa priorização. Isso satisfaz o requisito de priorização além de ordenar por valor, sem depender de inferência a partir de nomes de funções.

**Open questions / limits:** esta conclusão é sobre existência e integração da priorização. Não estabelece que a ordem maximize vendas, que o percentil 90 meça urgência ou que a qualidade comercial tenha sido comprovada. Não foram feitas chamadas ao modelo, mutações em dados, consultas ao banco ou execução de testes. Foram alterados somente os arquivos de evidência solicitados. A política e a estratégia comercial não foram ampliadas para outros requisitos.
