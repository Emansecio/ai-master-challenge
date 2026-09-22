## REQ-03 — Explicação da prioridade ao vendedor

> "O vendedor precisa entender **por que** um deal tem score alto ou baixo"
> Fonte: ai-master-challenge/challenges/build-003-lead-scorer/README.md:L67, Requisitos mínimos.

**Verdict:** implemented · confidence: high para presença e correspondência das explicações; compreensão por vendedores reais permanece não demonstrada nesta revisão.

---

**What this demands of an implementation:** apresentar os fatos e os critérios que explicam a prioridade de uma oportunidade, em linguagem utilizável pelo vendedor. O requisito imediatamente anterior admite "lógica de scoring/priorização" (README do desafio:L66); portanto, uma prioridade operacional explicada satisfaz esta propriedade sem inventar um score numérico ou uma probabilidade de venda. Este registro avalia explicabilidade, sem julgar o benefício comercial da política.

---

**Where enforcement lives:**

```go
// app/internal/core/core.go:L115-L124
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
```

A validação precedente envia dados inconsistentes para revisão humana (core.go:L94-L113). `Decorate` calcula a decisão, a prioridade e seus rótulos; acrescenta motivo, comparação de duração e ressalva sobre informações comerciais ausentes (core.go:L130-L140). A ordem usa classe de prioridade, excesso relativo de duração na revisão, preço de catálogo e ID (app/internal/store/read.go:L11-L13).

A interface explica cada decisão com regra, resumo, fatos, perguntas e limites. Há ramos específicos para conta ausente, prospecção, negociação acima da referência e negociação dentro da referência; revisão humana e ação desconhecida retornam explicação de conferência dos dados sem gráfico numérico (app/frontend/recommendation.ts:L17-L57). Quando conta ausente e duração elevada coexistem, ambos os sinais são preservados (L30-L36). O gráfico informa data, duração, referência e origem global ou por produto (L24-L28).

`recommendationView` publica essas informações em “Por que esta ação?”, “Como conduzir o atendimento” e “O que ainda não sabemos”; também explica o P90 e sua limitação (app/frontend/app.ts:L38-L40). A lista já apresenta um motivo abreviado (L135), enquanto o detalhe sempre inclui a explicação, independentemente de existir classificação do Jev (L138). Os estados do provedor são separados da orientação local (L114, L138).

O critério global de ordenação está disponível no próprio produto em “Como esta prioridade é definida?”, incluindo desempates e ausência de comprovação de aumento da conversão (app/static/index.html:L20). Um link próximo ao título leva a essa explicação; a mesma região esclarece que prioridade não representa chance de fechamento (L10-L11).

---

**Paths walked:**

1. Importação: `dataset.go:L124-L140` monta fatos e chama `Decorate`; `core.go:L94-L140` decide e descreve. Os cinco resultados possuem representação em `recommendation.ts:L17-L57`.
2. Lista: `web/api.go:L159-L171` chama `Store.Page`; `store/read.go:L30-L48` preserva os fatos e a decisão no JSON; `frontend/app.ts:L135` mostra o motivo curto de `recommendation.ts:L60-L68`.
3. Detalhe: `web/api.go:L189-L195` chama `Store.Get`; `store/store.go:L181-L201` retorna oportunidade e estado de classificação; `frontend/app.ts:L138` chama a explicação sem condicioná-la ao provedor.
4. Atualização de conta: `store/store.go:L279-L285` altera o fato, incrementa a versão e recalcula decisão e motivos. Conta inalterada retorna o registro existente (L276-L277).
5. Revisão humana ou decisão desconhecida: `recommendation.ts:L21-L23` oferece instrução de conferir dados e omite a visualização de duração. Não transmite certeza numérica diante de dados inválidos.
6. Resumo copiável: `recommendation.ts:L70-L87` inclui fatos, orientação, limites e perguntas, explicitando que o texto não comprova atendimento realizado.

---

**Searched:**

1. `O vendedor precisa` no README do desafio: requisito encontrado na linha 67; contexto “scoring/priorização” encontrado na linha 66.
2. `reason|explain|motivo|Por que|P90|evidence` em `app/internal` e fontes de interface: motivos no domínio, explicações em `frontend/recommendation.ts` e apresentação em `frontend/app.ts`. As tentativas iniciais em `app/web` e em glob de caminho Windows foram corrigidas após localizar os arquivos com `rg --files app`.
3. `Decorate|json.NewEncoder|opportunities|priority` em `app/internal` e `app/cmd`: encontrados os caminhos de importação, edição, leitura, ordenação e serialização citados acima.
4. `ordem|prioridade|critério|Prior|fila|P90|chance` em `app/static/index.html`, `app/frontend/app.ts` e `app/README.md`: localizada explicação dos critérios e desempates no próprio HTML, além da documentação.
5. Inspeção integral de `app/scripts/recommendation.test.mjs`: cobre igualdade ao P90, dois sinais simultâneos, falta de duração em prospecção, dados inválidos, referência fracionária, limites e resumo para conferência.

---

**How the verdict was reached:** o código não se limita a emitir um rótulo ou número. As mesmas decisões do domínio conduzem a explicações por registro, fatos verificáveis e limites explícitos; a regra de posição relativa também é exposta na interface. Não foi encontrado um ramo de decisão sem explicação. A alternativa `partial` exigiria um caminho funcional sem apresentação ou com justificativa incompatível, o que não foi observado neste requisito.

Validação executada em 22/09/2026: `node --test app/scripts/recommendation.test.mjs`, código de saída 0, 10 testes aprovados, zero falhas, um teste ignorado. O teste ignorado depende de `LEADDESK_LIVE_TEST=1` e lê as 2.089 oportunidades da aplicação; ele não foi habilitado nesta execução. Os testes executados usam o módulo JavaScript servido em `app/static/recommendation.js` e os casos locais existentes. Nenhuma consulta ao modelo, edição de código ou alteração de dados comerciais foi feita.

---

**Open questions:**

1. Esta inspeção estática e os testes de apresentação não demonstram que um vendedor real compreenda corretamente as explicações. Uma avaliação com vendedores precisa verificar interpretação da prioridade, P90 e ausência de dados, sem confundir esses sinais com chance de venda.
2. Não houve inspeção visual no navegador neste requisito. A legibilidade efetiva, a descoberta do painel de critérios e a interação por teclado dependem da revisão de interface específica.
3. O valor comercial da política e a concordância do Jev são propriedades diferentes de explicabilidade; não foram avaliados nem inferidos como aprovados neste registro.
