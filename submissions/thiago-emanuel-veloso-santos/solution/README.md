# Lead Desk

O Lead Desk ajuda o vendedor a organizar sua carteira e entender o próximo passo de cada oportunidade. Foi construído para o desafio 003 do G4 AI Master Challenge, com Go, TypeScript, PostgreSQL e integração com o classificador Jev.

A aplicação usa o conjunto público CRM Sales Predictive Analytics. São dados históricos, com referência em 31 de dezembro de 2017. Eles não representam a carteira atual da G4.

## O que o vendedor encontra

Na carteira, o vendedor pode buscar uma oportunidade e filtrar os resultados por vendedor, gestor ou região. As filas separam negociações que precisam de revisão, prospecções que precisam de qualificação, próximos passos a confirmar e cadastros sem empresa vinculada.

Ao abrir uma oportunidade, ele vê os fatos disponíveis, o motivo da orientação e perguntas sugeridas para o atendimento. Quando falta a empresa, o formulário de vínculo aparece no início do detalhe. A empresa deve ser confirmada no sistema de origem antes de ser selecionada.

O resumo de conferência pode ser revisado e copiado para apoiar o trabalho no CRM, o sistema de registro comercial da equipe. Ele reúne informações históricas e perguntas pendentes. Copiar esse texto não registra contato com o cliente nem atualiza outro sistema.

O histórico permite consultar alterações de cadastro, classificações e tentativas de processamento. Assim, o vendedor consegue distinguir uma resposta atual de outra produzida com uma versão anterior dos dados.

## Como a orientação é calculada

A aplicação segue critérios explícitos. Dados contraditórios pedem revisão humana. Uma oportunidade sem empresa pede confirmação do cadastro. Uma prospecção com empresa identificada pede investigação da necessidade. Uma negociação com duração acima da referência histórica pede revisão de sua situação. Nas demais negociações, a orientação é confirmar o próximo passo.

Essa referência de duração é o P90: um valor que abrange aproximadamente 90% das durações dos negócios encerrados considerados no cálculo, incluindo ganhos e perdas. O produto precisa ter pelo menos 30 encerramentos para usar sua própria referência. Abaixo desse número, a aplicação usa o histórico global.

Por exemplo, a oportunidade A7SA2L21 está sem empresa e registra 335 dias em negociação, diante de uma referência global de 104 dias. A interface pede duas verificações: identificar a empresa e confirmar se a negociação continua ativa. A base não informa quando ocorreu o último contato.

A ordem da carteira é uma hipótese de organização do trabalho. Sua capacidade de melhorar resultados de vendas ainda precisa ser avaliada com vendedores.

## Qual é o papel do Jev

Jev é o modelo da TypeSafe usado para responder a duas perguntas: qual é a situação da qualificação e qual próxima ação corresponde aos critérios definidos. O acesso ocorre pelo Vercel AI Gateway, com a credencial mantida no servidor.

As regras locais já fornecem a orientação exibida. Quando uma consulta ao Jev é solicitada, o servidor confere se suas respostas respeitam os mesmos critérios. Uma divergência é registrada como falha de validação. Enquanto o processamento acontece, a carteira continua disponível.

No ensaio com 120 oportunidades, Jev e as regras locais concordaram com a referência em todos os casos. Como essa referência foi construída a partir das próprias regras, o resultado demonstra aplicação consistente dos critérios testados. Ainda não demonstra aumento de vendas ou vantagem do modelo sobre o código local. Os percentuais retornados pelo Jev também não representam chance de fechamento.

## Situação da entrega

| Item | Situação |
|---|---|
| Aplicação local | Implementada e testada. Instruções de execução no guia da aplicação. |
| Dados | 8.927 registros importados de quatro tabelas; 2.089 oportunidades abertas na carteira. |
| Classificações preservadas | 120 do ensaio original e duas consultas reais feitas na aplicação. |
| Persistência | Dados, versões, classificações e fila de processamento no PostgreSQL. |
| Perfis de acesso | Demonstração local com administrador, gestor e vendedor; permissões conferidas no servidor. |
| Validação comercial | Pendente. A revisão técnica dos casos não substitui a avaliação de vendedores. |
| Uso corporativo | Requer definição de carga, autenticação corporativa, disponibilidade e recuperação. |
| Publicação e submissão | Ainda não realizadas. |

## Por onde começar

| Para entender ou fazer | Documento |
|---|---|
| Instalar, executar e usar a aplicação | [Guia da aplicação](app/README.md) |
| Entender os critérios e a ordem da carteira | [Política de qualificação](analise/POLITICA-QUALIFICACAO.md) |
| Entender as escolhas técnicas e a persistência | [Arquitetura](STACK-ARQUITETURA.md) |
| Conhecer a integração com o Jev | [Tecnologia e uso do Jev](analise/TECNOLOGIA-JEV.md) |
| Avaliar o que o Jev acrescenta hoje | [Contribuição do classificador](analise/CONTRIBUICAO-JEV.md) |
| Consultar as últimas correções e seus testes | [Correções após as cinco revisões](app/evidence/post-review-fixes/RELATORIO.md) |
| Acompanhar a construção e o uso de IA | [Registro do processo](analise/PROCESSO.md) |
| Consultar a ideia original | [Proposta inicial, preservada como histórico](PROPOSTA-INICIAL.md) |

## Limites dos dados

Em 1.425 oportunidades abertas, a empresa não está vinculada. Isso corresponde a 68,2% da carteira. A base também não registra necessidade, orçamento, participantes da decisão, intenção de compra, último contato ou data do próximo contato.

Essas informações permanecem desconhecidas até serem confirmadas. O preço de catálogo não informa o valor total da oportunidade, e a duração da negociação não informa seu tempo sem atividade. As explicações e os roteiros respeitam esses limites.
