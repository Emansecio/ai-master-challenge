# Ensaio Jev pelo Vercel AI Gateway

Data: 22/09/2026. Política: `0.2-proposed`. Modelo solicitado e retornado: `typesafe-ai/jev`. Provedor efetivo informado: `typesafe-ai`.

Para entender o modelo, os tipos de resposta e a escolha tecnológica, consulte [Jev: tecnologia, integração e justificativa](TECNOLOGIA-JEV.md).

**O Jev reproduziu corretamente as duas classificações da política nos 120 casos reais testados, incluindo os 60 reservados para avaliação. O Gateway reportou custo efetivo zero nas 120 chamadas bem-sucedidas.**

## Desenho do teste

Foram usados os casos preparados antes da execução, com seis estratos de estágio, conta identificada/ausente e idade acima/abaixo da referência. Cada estrato possui dez casos de desenvolvimento e dez de avaliação.

Sequência: 12 casos iniciais, complementação até 60 de desenvolvimento e 60 de avaliação. Os primeiros 12 fazem parte dos 60 de desenvolvimento e não são contados duas vezes. Não foi necessário alterar nenhuma pergunta, critério ou estado após os primeiros resultados.

Cada requisição contém apenas modelo, estado factual, as duas perguntas e restrição de provedor. A API não recebe as respostas esperadas nem a partição da amostra. Os hashes das 122 requisições foram reconstruídos para verificar esse isolamento.

O teste usa o [endpoint oficial de avaliação do Vercel](https://vercel.com/docs/ai-gateway/modalities/evaluation), via HTTP, sem instalar dependências. A chave fornecida foi armazenada exclusivamente no `.env` local, com regra de exclusão no `.gitignore`. A verificação não encontrou a credencial nos scripts, documentos ou resultados.

## Qualidade das classificações

| Medida | Desenvolvimento | Avaliação | Total |
|---|---:|---:|---:|
| Oportunidades distintas | 60 | 60 | 120 |
| Respostas finais válidas | 60 | 60 | 120 |
| Situação de qualificação correta | 60/60 | 60/60 | 120/120 |
| Próxima ação correta | 60/60 | 60/60 | 120/120 |
| Ambas corretas na mesma oportunidade | 60/60 | 60/60 | 120/120 |
| Erros HTTP temporários | 1 | 1 | 2 |

No conjunto reservado de avaliação, a próxima ação teve 30 acertos em identificação de conta, 10 em qualificação de prospecção, 10 em revisão de negociação antiga e 10 em continuidade da revisão comercial. As três classes de situação de qualificação também tiveram todos os exemplos corretos.

Não houve saída fora dos conjuntos definidos, probabilidades inválidas ou divergência entre a alternativa selecionada e a maior probabilidade retornada.

## Latência observada

| Medida | Desenvolvimento | Avaliação | Total |
|---|---:|---:|---:|
| Mediana da chamada | 392 ms | 405 ms | 396 ms |
| Percentil 95 | 610 ms | 584 ms | 610 ms |
| Maior chamada bem-sucedida | 4.048 ms | 974 ms | 4.048 ms |

A latência mede o tempo no cliente para uma requisição HTTP completa, incluindo conexão e TLS. O percentil usa o método de posição ordenada mais próxima. Os números consideram a resposta final bem-sucedida por caso; não incluem espera entre chamadas, diagnóstico dos erros ou intervalo até repetição. Não representam o tempo total do lote nem garantia de SLA.

O tempo da tentativa no provedor, informado pelo próprio Gateway, teve mediana de 156 ms. Essa métrica tem escopo diferente do tempo observado pelo cliente e não foi tratada como tempo puro de inferência.

## Consumo e custo

- Tokens de entrada reportados: **115.805**.
- Tokens de saída reportados: **15.120**.
- Campo `cost` somado nas 120 respostas bem-sucedidas: **US$ 0,00**.
- Campo `marketCost` somado: **US$ 0,00486381**.

O custo efetivo zero confirma a gratuidade reportada para estas chamadas. O valor de mercado é metadado de referência do Gateway, não uma cobrança adicional observada. A consulta não inclui conferência de fatura ou saldo da conta; as duas respostas de erro não forneceram metadados de custo equivalentes.

Não foi executado um modelo generativo na mesma tarefa, portanto ainda não há comparação empírica de economia ou velocidade contra outro LLM. Código determinístico continua sendo um comparador sem custo de inferência para essa política.

## Falhas operacionais e recuperação

Foram registradas **122 tentativas para concluir 120 oportunidades**. Duas retornaram HTTP 429 com mensagem de alta demanda do provedor. O lote parou em cada ocorrência; depois, somente os casos pendentes/falhos foram retomados. Nenhuma resposta bem-sucedida foi refeita.

Após a primeira ocorrência, foi introduzido intervalo de um segundo entre chamadas. Após a segunda, o restante da avaliação usou dois segundos. Os erros e as invocações foram preservados nos registros. Não houve troca de provedor ou modelo.

Isso demonstra recuperação neste ensaio e indica necessidade de fila, tratamento explícito de indisponibilidade e repetição limitada no produto. Não permite estimar uma taxa estável de disponibilidade a partir de um lote pequeno.

## Confiança e abstenção

No desenvolvimento, as menores confianças foram 0,57 para situação de qualificação e 0,41 para próxima ação. Na avaliação, foram 0,61 e 0,39. Todas essas respostas estavam corretas segundo a política.

Exigir confiança de pelo menos 0,8 nas duas perguntas teria aceitado apenas **40 dos 60 casos de avaliação**, embora todos os 60 estivessem corretos. Isso é uma observação diagnóstica posterior; o limiar não foi usado para escolher ou alterar as respostas.

Sem exemplos de erro neste conjunto, não podemos demonstrar que um limiar separa acertos de erros nem afirmar calibração da confiança. A confiança também não representa chance de venda.

## Interpretação crítica

**O resultado sustenta a viabilidade técnica do Jev como aplicador desta política de classificação.** Ele retornou resultados estruturados corretos e apresentou latência compatível com uma aplicação que pré-calcula classificações ou as executa em segundo plano.

Os limites permanecem:

1. As regras são explícitas, simples e determinísticas. O teste não demonstra vantagem sobre implementá-las diretamente em código.
2. Os rótulos são referências da política, não julgamento independente de especialistas comerciais nem resultados futuros de venda.
3. Os 120 casos são registros válidos de um único dataset. A classe `human_review` não é o resultado esperado em nenhum deles. Falta testar ambiguidades, contradições, dados inválidos e condições não representadas.
4. Duas respostas por oportunidade não constituem 240 amostras independentes de desempenho. O conjunto reservado possui 60 oportunidades, com estratificação equilibrada e regras homogêneas.
5. Não houve ensaio repetido de estabilidade das classificações bem-sucedidas. Os dois reenvios foram de erros sem resposta classificatória, não uma avaliação de repetibilidade.
6. O Gateway expôs o alias `typesafe-ai/jev`, sem revisão interna específica nas respostas. Política e dataset estão fixados por hash, mas reprodução futura pode usar outra revisão por trás do mesmo alias.
7. Priorização final, ganho operacional, aumento de conversão e economia frente a LLM generativo continuam sem validação.

## Decisão recomendada

Prosseguir com a integração do classificador em um protótipo local enxuto, preservando o contrato, explicações por evidência e tratamento explícito de falhas. A integração precisa manter separados: situação de qualificação, próxima ação e regra de ordenação da carteira.

Antes de automatizar aceitação por confiança ou declarar prontidão operacional, avaliar os casos de fronteira e as situações inválidas. O comparador determinístico e a comparação com um modelo generativo continuam pertinentes, mas não foram executados como novas chamadas nesta etapa.

## Evidências e reprodução

Diretório: `resultados/jev-vercel-v02/`.

- `manifesto.json`: endpoint, política, hashes de dados/perguntas e condições iniciais.
- `decisao-pre-avaliacao.json`: decisão de manter as perguntas após desenvolvimento.
- `chamadas.jsonl`: 122 tentativas, incluindo respostas, erros, uso e metadados.
- `invocacoes.jsonl`: registro das invocações instrumentadas após a introdução de retomada de erros; as primeiras chamadas estão no registro de respostas.
- `resumo.json`: métricas por fase e agregadas.
- `diagnostico_confianca.json`: distribuição de confiança e duração reportada pelo Gateway.
- `verificacao.json`: auditoria do ensaio concluída com sucesso.

Para conferir os recibos localmente, sem novas chamadas:

```text
python verificar_ensaio_jev.py
```

O executor `testar_jev_vercel.py` retoma o manifesto existente e não repete casos concluídos. Para um novo experimento, criar um diretório de execução distinto e preservar estes resultados. Nunca incluir o `.env` na entrega pública.
