# Explicações e qualidade das sugestões

Este registro descreve a rodada que ampliou as explicações. Correções posteriores de navegação, cadastro e resumo copiável estão no [relatório da revisão](CORRECOES-REVISAO-LEAD-DESK.md). Os resultados de teste abaixo pertencem à rodada descrita aqui.

## Diagnóstico

A classificação atual aplica a política operacional 0.2. O ensaio anterior verificou concordância com essa política; não mediu aumento de vendas nem qual próximo contato seria o melhor segundo vendedores. Sem novos rótulos comerciais independentes, não há evidência para anunciar maior acurácia comercial.

A revisão do código e dos dez casos já auditados confirmou oportunidades de melhoria verificáveis: motivos apresentados em parágrafos genéricos, diferença de duração que exigia cálculo mental, pouco destaque para alertas simultâneos e perguntas sem explicitar o registro esperado ao final do atendimento.

## Implementado

A lista mostra um motivo curto junto à ação. Conta ausente com longa duração explicita os dois sinais.

O detalhe separa o critério aplicado dos fatos disponíveis. A duração é identificada como calculada na data histórica da base.

Duas barras com valores em dias comparam negociação e P90. Não são um indicador de conclusão nem uma probabilidade. A origem da referência e a quantidade de encerramentos do produto aparecem ao lado; amostra de produto pequena usa a referência global existente.

Igualdade ao P90 é mostrada como igualdade, sem sinalizar ultrapassagem. Prospecções sem idade não recebem um gráfico de duração. Estados de revisão humana não recebem comparações que aparentem evidência válida.

Cadastro incompleto e duração acima da referência mantêm duas verificações visíveis, sem alterar a ação principal.

O roteiro muda conforme a ação e oferece pergunta e resultado a registrar. Respostas devem ser confirmadas e registradas no CRM de origem; a aplicação não finge coletar esses dados.

Uma seção enumera o que falta na base, a partir do campo 
`state.unavailable`.
Os percentuais do Jev permanecem no detalhamento da conferência. São apresentados como concentração das respostas, sem tratá-los como chance de venda ou qualidade comercial demonstrada.


O módulo `app/frontend/recommendation.ts` apresenta a decisão recebida do servidor. Não reclassifica, reordena, altera os critérios do Jev ou grava fatos. As explicações são da política e dos campos observáveis, não raciocínio interno do modelo. O servidor recebeu apenas a rota exata do novo arquivo JavaScript, mantendo sua política de conteúdo.

## Validação técnica

Nove testes automatizados passaram, incluindo os dez casos revisados, igualdade e diferença fracionária de referência, estados inválidos, ausência de duração e leitura das 2.089 oportunidades nas 105 páginas. Nenhuma nova inferência foi solicitada. Testes Go de domínio e carregamento do novo módulo também passaram.

Os seis contratos de leitura comparados com a rodada anterior permaneceram iguais. Contagens: 2.089 oportunidades, 2.089 versões, 122 classificações, dois jobs. Isso verifica preservação operacional; não mede a eficácia comercial das sugestões.

Reproduzir na raiz, com servidor local ativo:

```powershell
$env:LEADDESK_LIVE_TEST='1'
npm --prefix app run test:recommendations
```

Sem a variável, os testes de casos e limites rodam sem servidor; a checagem da carteira completa é marcada como ignorada.

Evidências em `app/evidence/recommendation-tests.txt`, `recommendation-contracts.json`, `recommendation-ui.json`, `recommendation-desktop.png` e `recommendation-mobile.png`.

## Próxima medida de assertividade comercial

Usar os mesmos dez casos para uma revisão independente por atendentes: apresentar os fatos antes da sugestão; registrar ação que escolheriam, motivo, informação faltante e próximo passo esperado. Depois apresentar a interface e verificar se conseguem explicar por que ela recomenda aquela ação e qual informação ainda não é conhecida.

Medir concordância por tipo de caso, omissão de alertas, sugestões sem evidência, entendimento correto da duração e utilidade do roteiro. Discordância exige análise do caso; não significa automaticamente erro do vendedor ou do modelo. Essa avaliação ainda não foi realizada e não é requisito para executar a demonstração local.
