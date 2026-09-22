# Refutação independente da candidata REQ-05

Escopo: somente identificação das ferramentas de assistência e quantidade de iterações no registro de processo. Não foram revisados outros requisitos, nem alterados documentos da entrega.

## Resultado

A candidata precisa ser delimitada. Há uma oportunidade confirmada de esclarecer o registro, mas não há evidência de ausência do process log nem fundamento textual para anunciar desclassificação por esses dois detalhes. A afirmação ampla de que nenhuma ferramenta de assistência aparece nas referências é refutada por evidências locais.

## Obrigação e expectativa

`ai-master-challenge/challenges/build-003-lead-scorer/README.md:L75-L77` exige process log e remete ao guia. `ai-master-challenge/submission-guide.md:L18-L20` explicita a obrigação e associa a desclassificação à ausência desse registro.

O guia aceita escolher ou combinar formatos (`L22`), incluindo narrativa escrita (`L29`). Identificação das ferramentas e quantidade de iterações aparecem sob **“O que queremos ver no process log”** (`L33-L39`), como expectativas explícitas de conteúdo. O texto não estabelece penalidade automática individual nem formato numérico obrigatório para cada expectativa. A seção sobre submissão forte enfatiza demonstrar iteração e julgamento (`L63-L68`).

O template pede **“Liste as ferramentas de IA que usou e para quê”** (`ai-master-challenge/templates/submission-template.md:L53-L61`) e um workflow (`L63-L69`). Não contém campo próprio para total numérico de iterações. Isso não elimina a expectativa do guia, mas impede tratar uma contagem de prompts como contrato técnico de entrega.

## Tentativa de refutação 1: ferramentas de assistência

Contraevidências encontradas:

1. `PROPOSTA-INICIAL.md:L131-L132` inclui **“Conversa anterior: Avaliar chance na vaga”** com endereço em `chatgpt.com`. A afirmação da candidata de que não existe referência a ChatGPT nesses documentos é ampla demais. A URL identifica a plataforma da conversa anterior. Não demonstra qual ferramenta escreveu o código, nem foi aberta nesta verificação.
2. `analise/PROCESSO.md:L71` liga diretamente `app/evidence/ui.json`. Este arquivo identifica **“Codex in-app browser”** em `L4` e enumera os fluxos verificados em `L5-L14`. Portanto, uma ferramenta usada na verificação aparece identificada numa evidência alcançável pelo registro de processo.
3. `PROPOSTA-INICIAL.md:L136` registra leitura das skills `jev-browser` e `typesafe-ai`, mas o próprio texto delimita consulta documental. Isso não sustenta que Jev Browser executou testes da interface.
4. Jev e Vercel estão identificados e contextualizados no ensaio (`analise/PROCESSO.md:L39-L49`). Continuam sendo evidência do componente do produto, sem estabelecer o assistente responsável pela programação.

**Veredito da refutação:** parcialmente refutada. Não há ausência absoluta de identificação de ferramenta. Subsiste uma lacuna mais estreita: o texto principal não explicita qual assistente participou de análise, programação e revisão nem por que foi escolhido para essas funções. As referências acima não devem ser promovidas a prova da autoria integral do código.

## Tentativa de refutação 2: quantidade de iterações

O registro discrimina ensaio real, alinhamento de arquitetura, implementação funcional, revisão de oportunidades, polimento, explicações/identidade visual/revisão e revisão documental (`analise/PROCESSO.md:L39`, `L51`, `L59`, `L73`, `L85`, `L96`, `L106`). A correção do direcionamento do assistente também aparece na proposta (`PROPOSTA-INICIAL.md:L97-L99`). Logo, houve iteração documentada; não cabe descrever o processo como uma única resposta entregue sem revisão.

Entretanto, contar títulos do documento não estabelece a quantidade real de iterações: alguns agrupam várias revisões, outros descrevem preparação ou resultados. `PROCESSO.md:L47` conta tentativas do ensaio Jev, não rodadas de desenvolvimento. Não localizei contagem explícita com unidade definida para o desenvolvimento.

**Veredito da refutação:** não refutada a ausência de contagem definida. Refutada qualquer conclusão de ausência de iteração. Trata-se de clareza documental frente à expectativa do guia; não de defeito funcional, ausência de process log ou desclassificação comprovada.

## Buscas e alcance

Foram lidos a candidata, o enunciado, `submission-guide.md`, o bloco de processo do template, `analise/PROCESSO.md` e o bloco de discussão e referências da proposta inicial. Buscas sem distinguir maiúsculas de minúsculas por `codex|chatgpt|claude|cursor|copilot|assistente|agentes|iteraç|rodada|etapa|prompt` nos documentos Markdown e por identificação de ferramenta nos destinos locais do registro encontraram os itens acima. A busca nos destinos JSON foi necessária: limitar a procura aos documentos Markdown teria perdido `app/evidence/ui.json:L4`.

A verificação não reconstrói prompts, não atribui um modelo de programação e não inventa um total. Se a revisão consolidada mantiver a candidata, a redação proporcional é: **“Explicitar no registro principal as ferramentas de construção e o significado/quantidade das rodadas documentadas.”** O requisito de existência do process log já está atendido; as duas observações afetam sua completude e legibilidade para o avaliador.
