# REQ-05: verificação independente da lacuna de processo

**Resultado:** refutação parcial. Existem referências identificáveis a ferramentas de apoio e evidências claras de iteração. Permanece uma oportunidade de consolidar qual ferramenta participou de cada etapa. Não foi encontrada uma contagem explícita e definida das iterações de construção. Isso representa uma expectativa de apresentação pouco explícita no material atual, e não ausência de process log ou prova de desclassificação.

## Escopo e critério

A candidata afirma que a narrativa existe, mas faltam identificação das ferramentas de construção e quantidade de iterações. Foram examinados `analise/PROCESSO.md`, suas referências, a proposta, o registro visual, os artefatos de evidência pertinentes e o guia/template do desafio. As fontes originais não foram alteradas. Esta verificação não abriu o histórico externo do ChatGPT, não chamou modelos e não executou a aplicação.

O guia declara o process log obrigatório e aceita narrativa escrita (`ai-master-challenge/submission-guide.md:L18-L31`). As cinco perguntas subsequentes aparecem sob “O que queremos ver no process log” (`L33-L39`). Logo, são expectativas explícitas de conteúdo, porém não existe ali exigência de um contador numérico formatado, unidade de iteração ou inventário exaustivo de ferramentas. A sanção por ausência de process log não se estende automaticamente a cada pergunta insuficientemente detalhada.

## Evidências que reduzem a candidata

| Evidência existente | O que comprova | O que não comprova |
|---|---|---|
| `app/evidence/ui.json:L4-L14` identifica `Codex in-app browser`, lista as verificações e declara “Verificacao manual assistida no navegador”. | O artefato nomeia a ferramenta usada em parte da revisão e explica sua finalidade. É alcançável pelo link de interface em `PROCESSO.md:L71`. | Não identifica sozinho o modelo ou a ferramenta que produziu o código. |
| `PROPOSTA-INICIAL.md:L131-L132` contém link para uma conversa anterior em `chatgpt.com`, intitulada “Avaliar chance na vaga”. | Há referência identificável ao ChatGPT como contexto anterior. A afirmação ampla de nenhuma identificação de ChatGPT nas referências precisa ser corrigida. | Não estabelece que o ChatGPT escreveu a aplicação nem assegura que o avaliador consiga abrir uma conversa privada. O conteúdo não foi consultado nesta verificação. |
| `PROPOSTA-INICIAL.md:L136` registra leitura das skills `jev-browser` e `typesafe-ai`. | Há ferramentas/instruções de apoio nomeadas na investigação inicial. | Leitura da skill não significa execução do Jev Browser. A proposta distingue essa possibilidade do escopo em `L105`. |
| `analise/DIRECAO-VISUAL.md:L7` registra aplicação da skill `frontend-design`, autor e link, data e finalidade. | Existe identificação de uma instrução de assistência usada na revisão visual e do objetivo atendido. O registro é ligado por `PROCESSO.md:L100`. | O repositório Anthropic da skill não identifica o modelo que a executou. Não é prova de uso de Claude. |
| `PROCESSO.md:L43-L45`, `L65`, `L89-L104` descreve falhas, correções, revisões e nova validação. | A construção não está apresentada como um único pedido sem revisão. Há iteração documentada. | Números de testes, chamadas ao Jev ou agentes não equivalem a uma contagem de iterações de desenvolvimento. |

## Contagem de iterações

O registro tem onze seções de segundo nível (`PROCESSO.md:L3`, `L7`, `L20`, `L33`, `L39`, `L51`, `L59`, `L73`, `L85`, `L96`, `L106`). Elas misturam fases, execução, julgamentos e limitações; não são onze iterações comprovadas. Uma seção agrupa explicações, identidade visual e revisão por agentes (`L96-L104`), enquanto outras subdividem a mesma análise inicial (`L3-L37`).

A narrativa, portanto, permite observar evolução e revisões, mas contar seus títulos daria uma precisão artificial. O pedido do guia “Quantas iterações foram necessárias” (`submission-guide.md:L39`) pode ser atendido com uma unidade definida e rodadas enumeradas. O material atual não faz isso. Por outro lado, o template de submissão oferece “Workflow” com sequência numerada, sem campo próprio de quantidade (`ai-master-challenge/templates/submission-template.md:L63-L69`); isso reforça que uma sequência clara é importante e que a ausência de um total não deve ser classificada como falha técnica ou descarte automático.

## Buscas e limites

1. `codex|chatgpt|claude|cursor|copilot|assistente|agentes|skill|iteraç|rodadas|rodada|frontend.design|taste` nos documentos principais e Markdown de análise encontrou o link ChatGPT, as skills e os relatos citados. Resultados do diretório do Router são documentação de terceiro, não evidência do desenvolvimento do Lead Desk.
2. `codex|chatgpt|claude|cursor|frontend.design|taste|tool|agent` em JSONs de evidência encontrou `app/evidence/ui.json:L4`. Resultados `sales_agent` se referem ao vendedor do dataset, sem relação com assistentes de construção.
3. Busca ampliada em TXT/JSON retornou o mesmo artefato Codex; nomes presentes no vocabulário do tokenizer do Router foram descartados como irrelevantes.
4. Leitura das seções e dos links mostrou caminhos do registro para proposta, registro visual e evidência de interface. Relatórios da rodada atual não foram usados para preencher retrospectivamente o histórico anterior.

## Disposição recomendada

Manter, se desejado, **partial com ressalva documental restrita**, sem usar “ferramentas não identificadas” como afirmação absoluta. A ferramenta de revisão de navegador e algumas skills estão identificadas; falta tornar explícito no registro principal quem auxiliou análise, implementação e revisão, conforme evidência real disponível.

Para iterações, registrar como **expectativa de conteúdo ainda sem resposta quantitativa explícita**, reconhecendo que a narrativa já comprova múltiplas rodadas. Não inferir ausência de iteração, desclassificação, quantidade de prompts ou modelo de assistência. Nenhuma correção foi aplicada nesta verificação.
