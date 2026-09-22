# Política de qualificação 0.2

Esta política é usada na aplicação local e foi testada em 22/09/2026. Ela organiza o trabalho de qualificação a partir dos dados disponíveis. Sua utilidade comercial ainda precisa ser avaliada com vendedores; não houve validação pela G4.

## O que a política decide

Cada oportunidade recebe uma classificação de qualificação e uma próxima ação. A classificação descreve o contexto disponível para o atendimento. A ação indica o que conferir ou fazer em seguida.

O código local calcula essas decisões. Quando Jev é consultado, recebe os fatos e as perguntas correspondentes. A aplicação só publica sua resposta como válida quando ela respeita os mesmos critérios. A ordem de apresentação da carteira é definida separadamente.

## Informações disponíveis

A política considera existência de empresa vinculada, estágio, produto, preço de catálogo, início da negociação, duração calculada e histórico de encerramentos. A data de referência dos cálculos é 31/12/2017.

Necessidade, orçamento, participantes da decisão, intenção de compra, último contato e próximo compromisso não estão registrados nessa base. Receita da empresa, nome do produto ou estágio não permitem preencher essas lacunas.

## Classificação de qualificação

| Condição | Classe usada no código | Significado |
|---|---|---|
| Estado inválido ou contraditório | `human_review` | Os dados precisam ser conferidos antes de aplicar a política. |
| Empresa ausente | `incomplete_profile` | É necessário identificar a empresa para avaliar seu perfil. |
| Empresa presente e estágio Prospecting | `discovery_required` | Há cadastro suficiente para iniciar a qualificação da prospecção. |
| Empresa presente e estágio Engaging | `negotiation_reviewable` | Há contexto cadastral para revisar a negociação. Adequação comercial ainda precisa ser confirmada. |

Oportunidades encerradas não são classificadas na carteira de trabalho. Seus dados fornecem apenas a referência histórica de duração.

## Escolha da próxima ação

As condições são verificadas nesta sequência. A primeira aplicável define a ação principal.

1. Dados inválidos ou contraditórios pedem revisão humana.
2. Empresa ausente pede confirmação e vínculo ao registro.
3. Prospecção com empresa identificada pede investigação da necessidade, dos participantes e do próximo passo.
4. Negociação identificada com duração acima da referência pede conferência de sua situação atual.
5. As demais negociações válidas pedem revisão do próximo passo comercial.

Uma ação principal não elimina outros sinais. Uma negociação sem empresa também pode ter duração elevada. Nesse caso, a interface mantém as duas verificações visíveis.

## Referência de duração

A comparação usa o percentil 90, chamado P90. Esse valor abrange aproximadamente 90% das durações dos negócios encerrados usados no cálculo, incluindo ganhos e perdas. Usa-se a referência do produto quando há pelo menos 30 encerramentos; abaixo disso, usa-se a referência global.

O limite de 30 é uma escolha operacional simples para reduzir a dependência de grupos pequenos. Ele não foi demonstrado como o melhor limite para o negócio. Na base atual, só entram encerramentos até 31/12/2017. Em outra data histórica, a referência precisaria ser recalculada com o que já era conhecido naquele momento.

Estar exatamente no P90 não é ultrapassá-lo. Estar acima dele pede conferência, mas não demonstra urgência, inatividade ou chance de perda. A base não informa o último contato nem um prazo combinado com o cliente.

## Ordem da carteira

A ordem de trabalho agrupa primeiro os registros que exigem revisão humana. Depois aparecem negociações identificadas acima da referência, prospecções identificadas, demais negociações identificadas e registros sem empresa.

Dentro da revisão de negociação, a aplicação considera quanto a duração excede a referência em termos relativos. Preço de catálogo e ID são critérios de desempate. A fila Cadastro tem acesso direto, e a visão Todas mantém a carteira reunida.

Essa organização evita que a maioria sem cadastro esconda todos os negócios com contexto disponível. Ela não atribui menor potencial comercial às empresas ainda desconhecidas. Não existe evidência para definir a melhor divisão do tempo do vendedor entre as filas ou afirmar que essa ordem maximiza vendas.

## Como os motivos são apresentados

As explicações são produzidas a partir dos fatos e da condição aplicada. Um cadastro ausente leva à orientação de confirmar a empresa. Uma negociação com 161 dias, diante de uma referência de 104 dias, leva à conferência de sua situação atual. Uma prospecção sem data de início não recebe uma duração presumida.

Essas explicações descrevem a política. Não representam acesso ao raciocínio interno do Jev. Respostas incompatíveis com os fatos ou com as regras são rejeitadas, sem uma justificativa inventada para sustentá-las.

O roteiro oferece perguntas e indica o que registrar depois de obter confirmação. O resumo copiável reúne fatos históricos e perguntas pendentes. As respostas do cliente devem ser documentadas no CRM de origem.

## Avaliação realizada e seus limites

O ensaio usou duas perguntas de `resultados/perguntas_jev.json` e estados de `resultados/casos_jev.jsonl`. As referências de resposta, guardadas em `expected_by_policy`, ficaram fora das requisições enviadas ao modelo.

Foram separados 60 casos para desenvolvimento e 60 para avaliação, com dez exemplos de cada uma das seis combinações de cadastro, estágio e duração em cada grupo. Essa seleção procura cobrir situações distintas; não representa uma amostra proporcional de toda a carteira. As referências vieram das regras propostas, sem julgamento comercial independente.

Jev coincidiu com a referência nas duas perguntas dos 120 casos. As regras locais também reproduzem essa referência. O resultado verifica aplicação dos critérios, sem demonstrar aumento de conversão ou vantagem decisória do modelo. O [relatório do ensaio](RESULTADO-JEV-VERCEL.md) preserva método, métricas e limitações.

Esses 120 casos não incluem estados contraditórios nem a necessidade de revisão humana. A aplicação trata dados inválidos e falhas do serviço, com testes controlados; esses testes não substituem um ensaio do modelo nessas situações.

Novas avaliações devem comparar respostas por pergunta, classe e combinação de fatos, registrar falhas e verificar consistência entre repetições. Qualquer limite de confiança deve ser escolhido no conjunto de desenvolvimento e avaliado depois nos casos reservados. A prioridade comercial exige avaliação própria com vendedores.

## Comportamento em falhas e alterações

| Situação | Comportamento |
|---|---|
| Jev indisponível | A orientação local continua acessível, com sua origem indicada. |
| Resposta inválida ou incompatível | O resultado não é publicado como recomendação válida do Jev. |
| Informação ausente | O campo permanece desconhecido; ausência não é substituída por zero ou suposição. |
| Dados ou critérios alterados | A classificação anterior deixa de ser reutilizável como atual. |
| Pedido já desatualizado na fila | O serviço encerra a pendência antes de iniciar outra tentativa. |
| Resposta desatualizada durante o processamento | A conferência final preserva o resultado como histórico. |

A política não contata clientes nem executa ações em um CRM externo. Alterações locais de empresa dependem da ação explícita do usuário.
