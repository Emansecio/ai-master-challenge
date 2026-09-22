# Correções após as cinco revisões

Implementação de 22/09/2026, autorizada por Thiago. Os três ajustes recomendados e a melhoria de navegação foram concluídos. A aplicação local na porta 8766 foi reiniciada com o executável atualizado e passou pelas verificações de interface após o reinício.

## O que mudou

| Ponto | Comportamento entregue |
|---|---|
| Confirmação de cópia | O aviso aparece junto do botão e permanece visível no computador e no celular. A rolagem acomoda o aviso e o botão. Uma resposta atrasada mantém a identificação da oportunidade de origem. Se a cópia automática falhar, o resumo fica selecionado para cópia manual. |
| Conexão com PostgreSQL | Quando a conta enviada já é a atual, `SetAccount` encerra a transação antes de consultar a oportunidade pelo pool. O retorno preserva conta e versão, sem criar outra entrada no histórico. |
| Registro do processo | O documento reúne as ferramentas utilizadas, seus papéis e 14 rodadas organizadas a partir dos registros existentes. Esclarece que essa contagem não equivale ao número de prompts, mensagens ou chamadas ao modelo. |
| Continuidade da navegação | Busca, fila, filtros de equipe e página ficam na URL. Recarregar, abrir outra aba e usar voltar ou avançar restaura a seleção. Valores inválidos são normalizados e os filtros disponíveis continuam respeitando o perfil autenticado. |

O código segue os padrões existentes de Go e TypeScript. As instruções de uso foram atualizadas no [guia da aplicação](../../README.md), e o histórico está no [registro do processo](../../../analise/PROCESSO.md).

## Validação

| Verificação | Resultado e evidência |
|---|---|
| Novos comportamentos no navegador | 25 verificações aprovadas: restauração da URL, histórico, filtros, paginação, perfil de vendedor, cópia e mensagens atrasadas. [Resultados](ui-results.json), [executor](../../scripts/test-post-review-ui.py). |
| Regressão da interface | 24 verificações aprovadas, incluindo login, escopo por perfil, foco no diálogo, rascunhos, resposta de salvamento atrasada e conflito de versão. [Resultados](browser-results.json), [executor](browser-regressions.py). |
| Integração com PostgreSQL | 17 testes principais e dois subcasos aprovados em banco temporário. O teste acrescentado usa um pool de uma conexão e verifica que salvar a mesma conta termina sem alterar a versão. [Saída completa](postgres-tests.txt). |
| Testes Go | `go test ./... -count=1` aprovado. A integração com banco foi executada separadamente, conforme a linha anterior. [Saída](go-tests.txt). |
| Análise estática e compilação | `go vet ./...`, `go build -o .local/leaddesk-final.exe ./cmd/leaddesk` e `npm run build` concluídos com código de saída zero. [Compilação TypeScript](frontend-build.txt). |
| Recomendações | 11 testes aprovados, incluindo conferência das explicações das 2.089 oportunidades locais. [Saída](recommendation-tests.txt). |

Os testes de navegador usaram Chromium pelo Microsoft Edge em modo sem janela. As capturas foram inspecionadas em 1440 × 1000 e 320 × 740: [computador](desktop-copy-feedback.png) e [celular](mobile-copy-feedback.png). Não houve erro JavaScript não tratado nos dois conjuntos de verificações.

As leituras usaram a base local. Nos cenários de alteração de conta e conflito, as respostas da API foram controladas pelo teste, sem enviar essas alterações à base principal. O acesso à área de transferência também foi controlado para conferir sucesso, recusa e atraso. Isso valida o tratamento da interface; não cobre todas as políticas de permissão de navegadores e sistemas operacionais.

## Preservação dos dados e limites

Ao concluir, a base principal mantinha 2.089 oportunidades, 2.089 versões, 122 classificações, dois trabalhos e duas tentativas. Não havia trabalho pendente ou em execução. As contagens são iguais às conferidas antes das alterações. Os testes de acesso criaram e encerraram sessões locais. As contagens e assinaturas dos arquivos alterados estão no [registro final](final-state.json).

Não houve nova chamada ao Jev, commit, publicação ou envio do desafio. Esta rodada verificou as quatro mudanças autorizadas. Não constitui medição de capacidade em produção nem validação comercial das recomendações com vendedores.
