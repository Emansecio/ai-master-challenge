# Contribuição do Jev na solução atual

## Resultado observado

Jev continua integrado como classificador de qualificação e próxima ação. O ensaio existente demonstra aplicação correta da política aos 120 casos auditados. Ainda não demonstra vantagem decisória sobre código determinístico, economia frente a um modelo de geração de texto ou aumento de conversão.

A nova revisão confrontou os recibos originais com uma implementação local das regras e verificou dez oportunidades na API atual. Não executou novamente o modelo. Não foram adicionados dados de conversas, enriquecimento externo ou exemplos sintéticos.

| Comparação | Regra local | Jev |
|---|---:|---:|
| Desenvolvimento: duas decisões iguais à referência | 60/60 | 60/60 |
| Avaliação separada: duas decisões iguais à referência | 60/60 | 60/60 |
| Dez casos revisados: concordância entre os métodos | 10/10 | 10/10 |
| Chamadas externas para aplicar a política local | 0 | 122 tentativas no ensaio original, 120 concluídas |
| Latência no ensaio de avaliação | Não medida neste comparativo | Mediana 404,85 ms; p95 583,57 ms |

A referência foi construída da própria política determinística. O resultado mede aderência a essa política, não julgamento comercial independente. A amostra foi estratificada, não sorteada proporcionalmente à carteira. O caminho de revisão humana por dados inconsistentes não está representado nesses 120 casos reais.

## O que o classificador acrescenta hoje

O fluxo exercita classificação por critérios escritos, retorno estruturado, probabilidades/confiança e integração assíncrona com persistência e controle de versões. Isso prova funcionamento da integração. A interpretação comercial dos rótulos e a ordem de trabalho continuam definidas pela política proposta.

A aplicação já calcula as decisões em código e só aceita uma resposta Jev quando ela concorda com esse cálculo. Portanto, o modelo não pode melhorar ou mudar a decisão exibida dentro do contrato atual: uma divergência vira falha de validação. O termo “coerente com a política” descreve essa checagem com maior precisão que “validado”.

As probabilidades do modelo não estão calibradas para fechamento de vendas. Nem mesmo a confiança mede o valor econômico da ação. No ensaio separado, exigir confiança de pelo menos 0,8 nas duas respostas aceitaria 40 dos 60 casos, apesar de os 60 coincidirem com a política. Esse corte não foi transformado em filtro comercial.

O Gateway reportou custo efetivo zero e custo de mercado agregado de US$ 0,00486381 no ensaio original. Isso não é garantia de gratuidade. Código local também consome infraestrutura, mas elimina a requisição externa para essas regras. Sem um ensaio equivalente de modelo de geração de texto, a alegação de economia frente a ele permanece hipótese.

## Onde testar valor adicional depois

Uma hipótese plausível é classificar evidências textuais de necessidade, objeção ou próximo compromisso, usando notas comerciais autorizadas e critérios claros. Esses dados não existem na base atual. Relatos inventados não podem ser apresentados como evidência dos clientes.

Antes desse experimento, seria necessário obter notas com origem, data e vínculo com a oportunidade; definir rótulos com revisão comercial independente; separar treino/desenvolvimento de avaliação por conta e tempo; e comparar Jev com regras simples nas mesmas entradas. Os critérios de sucesso devem incluir erros comercialmente relevantes, abstenção/revisão humana, latência e custo, além de concordância. Os limiares precisam ser definidos antes de examinar o resultado de avaliação.

Se esse novo classificador avaliar texto, a validação atual de igualdade com a regra estruturada precisará de um contrato próprio. Apenas inserir texto nas perguntas atuais e manter essa igualdade não testa contribuição adicional.

## Decisão desta etapa

Manter a integração Jev acordada, com origem e limites explícitos. Melhorar a utilidade da orientação com os fatos já existentes. Não atribuir ganho comercial à IA nem promover “confiança” a score de venda.

Para validação com vendedor, usar os dez casos do [roteiro de revisão](REVISAO-COMERCIAL-10-CASOS.md). Registrar concordância, ação alternativa, motivo e dado ausente, sem preencher essas respostas pelo avaliador técnico. Avaliar tempo até encontrar uma ação e decisões consideradas inadequadas. A validação com vendedor permanece pendente.

Fontes locais: [comparativo reproduzível](../app/evidence/business-review.json), [ensaio original](RESULTADO-JEV-VERCEL.md), [resumo das chamadas](resultados/jev-vercel-v02/resumo.json) e [diagnóstico de confiança](resultados/jev-vercel-v02/diagnostico_confianca.json).
