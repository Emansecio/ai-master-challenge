## REQ-01 — Uso dos dados reais

> "Precisa usar os **dados reais** do dataset"
> Fonte: ai-master-challenge/challenges/build-003-lead-scorer/README.md:L65. O dataset indicado está em L25.

**Verdict:** implemented · confidence: high

**What this demands of an implementation:** importar os registros do conjunto indicado e utilizá-los na aplicação e na classificação, em vez de apresentar registros inventados como se fossem do conjunto.

---

**Where enforcement lives:**

```go
// app/internal/core/dataset.go:L23-L30
b, e := os.ReadFile(path)
if e != nil {
    return d, e
}
hash := sha256.Sum256(b)
if hex.EncodeToString(hash[:]) != DatasetSHA {
    return d, fmt.Errorf("dataset diferente da versão auditada")
}
```

O ZIP local é lido, sua assinatura é comparada à constante em `app/internal/core/core.go:L14` e os CSV são interpretados em `app/internal/core/dataset.go:L31-L55`. O manifesto associa essa assinatura ao endereço do Kaggle fornecido pelo desafio (`analise/resultados/auditoria.json:L3-L12`). A assinatura do arquivo presente foi recalculada nesta revisão e coincide: `74d535826330b616758ebb6bb393abf701a5126364a72fbe71003cb6a7a87a9c`.

As tabelas de contas, produtos e vendedores são relacionadas em `app/internal/core/dataset.go:L56-L63`. Negócios ganhos e perdidos com encerramento até 31/12/2017 alimentam as durações históricas e o cálculo P90 (`L66-L106`). Registros Engaging e Prospecting originam as oportunidades operacionais (`L107-L142`). Produto ou vendedor sem correspondente, preço inválido, datas inválidas e contagem diferente de 2.089 interrompem a importação (`L112-L144`). A falta de conta é preservada como informação ausente, e não preenchida artificialmente (`L124`, `L139`).

O estado derivado desses dados define a decisão e sua justificativa: `Decorate` chama `Decide` em `app/internal/core/core.go:L130-L140`; `Decide` usa validade dos campos, identificação da conta, etapa e duração em `L98-L124`.

No preparo da aplicação, `core.LoadDataset` é seguido por `Store.Seed` (`app/cmd/leaddesk/main.go:L53-L63`). `Seed` preserva os registros originais em `source_records`, grava oportunidades e registra a primeira versão com autor `dataset` (`app/internal/store/store.go:L104-L133`). Os conflitos usam `ON CONFLICT DO NOTHING`, preservando registros já presentes. A operação termina em transação (`L157`).

A listagem lê `opportunities` do PostgreSQL (`app/internal/store/read.go:L24-L57`), é publicada pela rota GET (`app/internal/web/api.go:L159-L171`) e recebida/renderizada pelo navegador (`app/frontend/app.ts:L123-L128`). O detalhe também consulta o documento persistido, sem substituí-lo por uma amostra embutida (`app/internal/store/store.go:L181-L201`; `app/internal/web/api.go:L189-L195`).

---

**Paths walked:**

1. `main.run`, modo setup → `LoadDataset` → leitura e hash do ZIP → CSV → relacionamento das quatro tabelas → oportunidades e referência histórica → `Decorate`/`Decide` → `Seed` → dados originais, carteira e primeira versão persistidos.
2. Arquivo ausente, assinatura divergente, arquivo ZIP ou CSV inválido, produto/vendedor sem referência, preço/data inválidos ou quantidade inesperada → erro devolvido ao setup, sem carteira alternativa fictícia (`dataset.go:L23-L45`, `L77-L80`, `L112-L144`; `main.go:L57-L62`).
3. `main.run`, modo serve → exigência de configuração persistida e política correspondente (`main.go:L74-L80`) → GET da carteira → consulta real do banco → renderização no navegador. O modo serve não reimporta o ZIP a cada leitura.
4. Carteira existente → repetição do setup preserva as oportunidades já gravadas (`store.go:L124-L132`). O uso posterior pode conter edições humanas; a versão inicial identifica a origem do dataset.

---

**Searched:**

1. `dados reais|dataset` no enunciado: fonte em L25 e requisito em L65.
2. `rg --files` para CSV e arquivos de importação: encontrados o carregador Go e CSV de resultados; as quatro tabelas originais estão dentro do ZIP, encontrado em `analise/dados/crm-sales-predictive-analytics.zip`.
3. `csv|sales_pipeline|accounts|Import` em `app/cmd`, `app/internal` e instruções locais: encontrados o carregador, o seed, leitura de contas, teste de importação e importador separado de recibos. Nenhum importador de recibos foi confundido com importação da base.
4. `DatasetSHA`: constante em `core.go:L14`, comparação em `dataset.go:L28` e exposição do identificador na auditoria em `read.go:L99`.
5. `Store.Page|Store.Get|/api/opportunities` no servidor e frontend: ligações concretas entre banco, API e interface descritas acima.
6. `kaggle|download|sha256|crm-sales-predictive` em arquivos de análise: encontrado manifesto de procedência em `analise/resultados/auditoria.json:L3-L12` e geração dessa procedência em `analise/analisar_dados.py:L193-L195`.

---

**How the verdict was reached:** o requisito está implementado porque existe uma ligação rastreável entre o arquivo do conjunto indicado, sua transformação, a decisão calculada, a persistência e os dados consumidos pela interface. A verificação adicional de assinatura restringe a versão aceita, mas não muda o veredito principal: o uso dos registros exigidos está presente.

Validação executada nesta revisão: `go test ./internal/core -run '^TestAuditedCases$' -count=1 -v`, dentro de `app`, passou. O teste lê o ZIP, verifica 8.800 negócios e 85 contas, compara os estados e decisões de 120 casos preservados e exige exatamente 120 comparações (`app/internal/core/core_test.go:L10-L52`). O comando `Get-FileHash -Algorithm SHA256 analise/dados/crm-sales-predictive-analytics.zip` confirmou a assinatura citada acima.

---

**Open questions:**

1. A procedência externa foi rastreada pelo manifesto preservado; esta verificação não baixou novamente o arquivo do Kaggle. A igualdade com o conteúdo remoto atual não foi estabelecida, nem é necessária para revalidar a versão histórica fixada.
2. O teste executado cobriu a transformação local. Não foi executada nesta checagem uma nova importação no PostgreSQL, nem uma consulta autenticada ao servidor em execução; o caminho banco/API/interface foi verificado por leitura do código. Não se afirma aqui uma nova conferência de todos os registros do banco ativo.
3. O conjunto é histórico e a carteira usa apenas as oportunidades abertas; os encerramentos alimentam a referência de duração. Isso não comprova resultados comerciais atuais, nem transforma esses registros em clientes reais da G4.

Nenhuma chamada a modelo, alteração de código ou alteração de dados da aplicação foi realizada nesta checagem. Somente este relatório foi criado.
