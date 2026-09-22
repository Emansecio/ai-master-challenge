## REQ-05 — Registro do processo de construção com IA

> "### 3. Process log (obrigatório)"
>
> "Evidências de como você usou IA para construir. Leia o [Guia de Submissão](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/submission-guide.md)."
>
> Fonte: ai-master-challenge/challenges/build-003-lead-scorer/README.md:L75-L77.

> "Evidência de **como** você usou IA para chegar na solução. Sem process log = desclassificado."
>
> Fonte: ai-master-challenge/submission-guide.md:L20.

**Verdict:** partial · confidence: high

Nota da consolidação: esta é a análise inicial da candidata. As contrachecagens [documental](REQ-05-refutation-docs.md) e [das evidências](REQ-05-refutation-evidence.md) encontraram identificação de ferramentas nas referências. A conclusão final é explicitar no registro principal as ferramentas de construção e as rodadas documentadas, não afirmar ausência absoluta dessas informações. O destino do link citado acima foi ajustado à localização deste relatório.

**What this demands of an implementation:** disponibilizar um registro real da construção com IA em um dos formatos aceitos, demonstrando o processo e cobrindo as expectativas do guia. A presença do registro está atendida; a identificação das ferramentas usadas para construir e a quantidade de iterações permanecem incompletas.

---

**Where enforcement lives:**

O requisito é documental. `README.md:L58` encaminha o avaliador ao registro `analise/PROCESSO.md`. Esse arquivo apresenta a sequência de análise, ensaio, decisões de arquitetura, implementação, revisões e correções (`analise/PROCESSO.md:L3-L110`).

O guia aceita expressamente uma narrativa escrita: "Documento explicando passo a passo: \"primeiro fiz X, depois pedi Y ao Claude, ajustei Z porque...\"" (`ai-master-challenge/submission-guide.md:L29`). Portanto, capturas de conversas, exportações e histórico Git são formatos alternativos (`L22-L31`), não anexos obrigatórios cumulativos. Não há fundamento para declarar ausência de process log por falta de prints.

As cinco expectativas de conteúdo constam em `submission-guide.md:L35-L39`:

| Expectativa literal | Evidência e resultado |
|---|---|
| "Quais ferramentas de IA você usou e por quê" | O registro documenta Jev pelo Vercel e suas chamadas (`PROCESSO.md:L39-L49`), mas Jev é o classificador incorporado ao produto. O texto menciona "três agentes" (`L102`) sem identificar a ferramenta de assistência que analisou, programou e revisou o projeto. `PROPOSTA-INICIAL.md:L97-L99` também usa apenas "assistente". Não foram encontrados Codex, ChatGPT, Claude ou Cursor nos documentos de processo consultados. Cobertura parcial. |
| "Como você decompôs o problema antes de promptar" | A proposta preserva a sequência prevista: inspecionar dados, definir critérios e papel do Jev, especificar versão e avaliação, implementar/testar e preparar a entrega (`PROPOSTA-INICIAL.md:L111-L117`). O registro detalha sua execução (`PROCESSO.md:L7-L18`). Coberto por narrativa, sem exigir prompts literais. |
| "Onde a IA errou e como você corrigiu" | A proposta registra a sugestão inicial do assistente de usar Jev para interpretar pedidos e a correção de Thiago para colocá-lo na qualificação (`PROPOSTA-INICIAL.md:L97-L99`). O processo também registra falhas encontradas por testes e respectivas correções (`PROCESSO.md:L45`, `L65`, `L102-L104`). Coberto. |
| "O que você adicionou que a IA sozinha não faria" | A correção de direção feita por Thiago está identificada na proposta (`PROPOSTA-INICIAL.md:L97-L100`). O registro atribui ao candidato decisões e solicitações de concorrência/persistência (`PROCESSO.md:L53-L57`), identidade visual (`L100`) e revisão por agentes (`L102`). Há contribuição humana registrada; não é necessário inventar afirmação contrafactual sobre o que uma IA jamais faria. |
| "Quantas iterações foram necessárias" | O registro descreve sucessivas etapas e revisões (`PROCESSO.md:L39-L110`), demonstrando que houve iteração, mas não quantifica nem define uma unidade de contagem das rodadas de construção. Os 120 casos e 122 pedidos Jev (`L47`) são medidas do ensaio do produto e não devem ser apresentados como número de iterações de desenvolvimento. Cobertura parcial. |

---

**Paths walked:**

1. Enunciado do desafio → guia de submissão → formatos permitidos e conteúdo esperado → link principal do README → `analise/PROCESSO.md`.
2. Processo → proposta inicial: preservação de discussão e decomposição antes da implementação (`PROPOSTA-INICIAL.md:L91-L121`). A proposta se identifica como síntese, não transcrição literal (`L93`).
3. Processo → ensaio real: `analise/RESULTADO-JEV-VERCEL.md:L9-L16` descreve amostragem, sequência, perguntas e isolamento dos rótulos. `analise/resultados/jev-vercel-v02/manifesto.json:L2-L6` identifica endpoint, modelo e assinaturas. São evidências do uso do classificador, não da ferramenta que escreveu o código.
4. Processo → correções da revisão: `analise/CORRECOES-REVISAO-LEAD-DESK.md:L35-L49` delimita testes, respostas controladas e contagens preservadas. `app/evidence/review-fixes-ui.json:L2-L13` registra método, momento e observação concreta. `app/evidence/tests.txt:L3-L8` contém saída preservada de testes. Foram lidos como evidências históricas, sem alegar reexecução nesta checagem.
5. Conferência dos links Markdown em `analise/PROCESSO.md`: todos os 19 destinos locais encontrados existem. A checagem confirma disponibilidade local, não publicação ou inclusão futura no pacote de entrega.

---

**Searched:**

1. `Process|log|Evid|IA|prompt|screenshot|print` no enunciado, guia e registro: localizados requisito, formatos alternativos e cinco expectativas, citados acima.
2. `Codex|ChatGPT|Claude|Cursor|prompt|conversa|export|transcri|process` em README principal, processo, proposta inicial, resultado Jev e relatório de correções: localizadas referências genéricas a conversa e assistente, mas nenhuma identificação da ferramenta de assistência de construção.
3. `Codex|ChatGPT|Claude|Cursor|ferramentas de IA|iteraç|decompo|agentes` nos documentos Markdown de análise: retornaram referência arquitetural genérica e os três agentes do processo; nenhuma identificação ou quantificação adicional do processo de construção.
4. Extração dos destinos Markdown do registro e `Test-Path`: 19 links locais existentes.

---

**How the verdict was reached:** a obrigação de existir process log está atendida por narrativa escrita, formato explicitamente permitido. O veredito agregado é parcial porque o pedido inclui também as expectativas de conteúdo do guia: faltam identificação e justificativa das ferramentas que participaram da construção e uma contagem definida das iterações. Isso é uma lacuna documental confirmada, não prova de que as etapas não aconteceram, nem motivo para afirmar desclassificação automática. A sanção textual do guia se refere à ausência do process log, que não é o caso.

A menor complementação proposta é identificar as ferramentas de construção realmente utilizadas e seu papel, além de enumerar as rodadas documentadas, informando a unidade escolhida e o limite do registro. Não se deve reconstruir prompts literais, atribuir modelos não confirmados ou inventar quantidade total de interações. Não foram feitas essas edições porque esta etapa autoriza verificação.

---

**Open questions:**

1. A lista exata de ferramentas/modelos usada nas etapas antigas não pode ser deduzida do nome genérico "assistente". Deve ser confirmada pelo histórico disponível antes de completar a documentação.
2. É possível enumerar as rodadas já descritas, mas o total de mensagens ou prompts do desenvolvimento não foi estabelecido por estes arquivos. Esse total não deve ser estimado como fato.
3. Não foi verificado nesta checagem o pacote final de submissão. Os links e evidências conferidos estão presentes no workspace.

Nenhuma captura nova, instalação, chamada a modelo, mudança da documentação original ou submissão foi realizada. Somente este relatório foi criado.
