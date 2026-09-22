# Avaliação técnica e de negócio — Lead Scorer

Data: 22/09/2026. Continuação da proposta inicial de 21/09/2026. Análise exploratória concluída; aplicação e integração com Jev ainda não implementadas.

**Atualização posterior nesta data:** autorizei a execução do ensaio real de classificação. Consulte [Resultado Jev pelo Vercel](RESULTADO-JEV-VERCEL.md). As seções abaixo preservam as conclusões e pendências existentes antes desse ensaio; naquela etapa, a aplicação ainda estava pendente.

## 1. Parecer

**Avançar com um protótipo enxuto de qualificação e priorização assistida. Não apresentar, neste estágio, a solução como preditor validado de vendas ou como prova de economia com Jev.**

O problema de negócio é legítimo: organizar a atenção limitada do vendedor e explicar cada recomendação. Os dados sustentam filtros de carteira, indicadores históricos, detecção de informações ausentes e revisão de negociações antigas. Não sustentam inferir necessidade, intenção, orçamento ou autoridade do comprador.

A preferência por Jev como classificador central foi preservada na proposta de ensaio. Entretanto, sua necessidade técnica ainda não foi demonstrada. Com uma política inteiramente expressa por regras sobre campos estruturados, código determinístico oferece um concorrente forte: custo de inferência zero, consistência e explicação direta. Jev precisa justificar seu uso por aderência a políticas, flexibilidade ou outra melhoria mensurável, sem receber crédito por cálculos já resolvidos pelo código.

## 2. Base examinada e integridade

Fonte: [dataset indicado pelo desafio](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics), versão 1 segundo a API pública consultada. O arquivo baixado foi preservado em `dados/crm-sales-predictive-analytics.zip`; os hashes estão em `resultados/auditoria.json`.

| Tabela | Registros | Achados principais |
|---|---:|---|
| Contas | 85 | Setor, receita anual em milhões de USD, funcionários e localização completos; 70 campos de controladora vazios, sem presumir se isso significa independência ou desconhecimento. |
| Produtos | 7 | Nome, série e preço sugerido; ausência de descrição funcional, quantidade e margem. |
| Equipe | 35 | 6 gestores e 3 regiões; 30 vendedores possuem oportunidades. |
| Pipeline | 8.800 | IDs únicos; 6.711 encerradas e 2.089 abertas. |
| Metadados | 21 | Definições dos campos; não fornece histórico de atualizações ou data de extração operacional. |

O pipeline usa `GTXPro` em 1.480 linhas e o catálogo usa `GTX Pro`. O alias foi aplicado exclusivamente em memória para a análise, com junções `many_to_one` validadas e preservação das 8.800 linhas. O ZIP original não foi modificado. Sem o alias, uma junção interna descartaria 16,8% das oportunidades.

Todos os identificadores de conta preenchidos e todos os vendedores do pipeline encontram cadastro. Os CSVs não têm linhas integralmente duplicadas. Há rótulos com grafia irregular, como `technolgy`; isso não impediu a análise por grupo e não foi corrigido no original.

## 3. O principal problema operacional

| Estágio aberto | Conta identificada | Conta ausente | Total |
|---|---:|---:|---:|
| Prospecting | 163 | 337 | 500 |
| Engaging | 501 | 1.088 | 1.589 |
| Total | 664 | 1.425 | 2.089 |

**68,2% das oportunidades abertas não têm conta identificada; todas as encerradas têm.** Isso não demonstra que identificar a conta causa fechamento. O preenchimento pode ocorrer durante o processo. Usar esse campo atual como preditor de um resultado histórico pode incorporar informação que não existia na data da decisão.

Consequências:

- Não remover as 1.425 oportunidades: isso excluiria a maior parte da carteira aberta.
- Não atribuir baixa qualidade comercial automaticamente a cadastro incompleto.
- Mostrar a lacuna e o encaminhamento de identificação da conta, preservando produto, vendedor e estágio conhecidos.
- Não vender enriquecimento automático: os arquivos não oferecem identificadores alternativos suficientes para descobrir com segurança qual empresa está ausente.

## 4. Tempo e risco de generalização

Adotamos **31/12/2017 como data de referência explícita da demonstração**, por ser a última data de fechamento observada. Isso é uma convenção analítica; não foi confirmada como data de extração.

Nas 6.711 oportunidades encerradas, a duração mediana é 45 dias, o percentil 90 é 104 dias e o máximo é 138 dias. Nas 1.589 negociações abertas com data, a mediana de idade é 165 dias, o máximo é 423 dias e **1.291 (81,2%) ultrapassam a duração máxima de todas as encerradas**.

Isso representa forte diferença de distribuição. Não é prova de que negócios antigos nunca fecham, de que o CRM está abandonado ou de que os dados são sintéticos. Não usar o limite de 138 dias como regra para eliminar oportunidades.

Um alerta por percentil 90 do produto, com referência global para grupos com menos de 30 encerramentos, sinaliza **1.436 das 1.589 negociações abertas (90,4%)**. Um alerta tão frequente tem pouca capacidade de distinguir prioridades; deve ser contexto para revisão, não um alarme urgente nem um multiplicador automático do score.

Não há data de criação para as 500 prospecções, data de último contato, agenda de retorno, histórico de estágio ou histórico de troca de vendedor. Idade da negociação não é inatividade. Não há como reconstruir com precisão toda a carteira em qualquer data passada.

## 5. O histórico não autoriza um ICP forte

Taxas de vitória entre negócios encerrados por setor estão aproximadamente entre 61% e 65%. Isso não fornece, por si, um perfil ideal de cliente discriminante. Receita e número de funcionários são atributos de porte, não disponibilidade orçamentária.

No produto `GTK 500`, 15 de 25 encerradas foram ganhas: 60%, com intervalo de Wilson de aproximadamente **40,7% a 76,6%**. O ponto estimado é muito menos preciso que o de grupos grandes. Esses intervalos são descritivos e pressupõem observações independentes; negociações repetidas por conta podem reduzir a precisão efetiva.

A taxa entre negócios encerrados varia de 82,1% no primeiro trimestre a 60,3% no quarto trimestre de 2017. Com o início das datas de fechamento em março, seleção temporal é uma explicação possível. Não foi estabelecida uma causa nem uma deterioração real da operação.

## 6. Benchmark retrospectivo executado

Foram comparadas cinco referências: preço de catálogo; taxa histórica suavizada por produto; taxa por produto e vendedor; preço multiplicado pela taxa por produto; e expectativa de seleção aleatória dentro da carteira de cada vendedor.

Desenho fixado antes desta execução:

- Cortes em 31/03, 30/06 e 30/09/2017.
- Histórico usa somente encerramentos conhecidos até o corte.
- Carteira elegível: negociação iniciada até o corte e ainda não encerrada nele.
- Seleção de 5 e 10 oportunidades por vendedor: 30 combinações de corte, capacidade e método.
- Resultado: venda ganha observada nos próximos 90 dias e receita histórica dessas vendas.
- Suavização com força 20 em direção à taxa global; produto-vendedor retorna à taxa suavizada do produto. Parâmetro exploratório, não otimizado.
- Empates por hash estável do ID; análise de sensibilidade com 30 desempates alternativos.
- Intervalos exploratórios por reamostragem de vendedores, 2.000 repetições.

Resultados em **30/09/2017**, com 2.409 oportunidades elegíveis e 150 selecionadas (5 por vendedor):

| Método | Ganhas em 90 dias entre selecionadas | Precisão | Parcela da receita elegível capturada |
|---|---:|---:|---:|
| Preço de catálogo | 37 | 24,7% | 18,5% |
| Taxa por produto | 33 | 22,0% | 0,5% |
| Taxa por produto e vendedor | 33 | 22,0% | 6,8% |
| Preço × taxa por produto | 37 | 24,7% | 18,5% |
| Aleatório por vendedor, expectativa | 36,3 | 24,2% | 7,0% |

As quatro primeiras linhas usam um desempate fixo. A última é esperança matemática, não uma execução que produziu fração de venda. A expectativa aleatória por vendedor difere da taxa de 22,5% da carteira inteira porque cada vendedor recebe a mesma capacidade de seleção, embora as carteiras tenham tamanhos diferentes.

**Nos três cortes, preço × taxa por produto produziu exatamente a mesma ordem que preço sozinho.** A separação de preços domina a pequena variação das taxas. Isso é especialmente relevante porque o desafio exige mais que ordenar por valor.

A taxa por produto não apresentou vantagem consistente frente à referência de preço. Em setembro, sua diferença de precisão foi -2,7 pontos percentuais, com intervalo exploratório de aproximadamente -12,0 a +6,7 pontos. Para preço, a precisão de setembro variou de 20,7% a 28,7% apenas trocando os desempates. Diferenças pequenas não justificam alegações de melhoria.

**Limites:** estudo exploratório, não teste prospectivo independente. Negociações podem se repetir entre cortes. Produto e vendedor são assumidos estáveis por falta de histórico. A análise considera cobertura de observação até 31/12/2017, não confirmada na fonte. Ausência de vitória em 90 dias não significa perda definitiva. A completude atual da conta não foi usada para ordenar o passado. Os métodos avaliados não esgotam todos os modelos possíveis.

Receita capturada retrospectivamente não é receita incremental: as vendas já ocorreram com outra política de atendimento, e o efeito de contatar cada cliente não foi observado. Esses números não medem ROI.

## 7. Papel defensável do Jev

A documentação oficial descreve `Choice` para alternativas definidas, `Score` para dimensões ordenadas e confiança derivada da distribuição das respostas. Confiança de classificação não é probabilidade de venda. Referências: [Choice](https://docs.typesafe.ai/primitives/choice), [Confidence](https://docs.typesafe.ai/confidence), [Composite scoring](https://docs.typesafe.ai/patterns/composite-scoring).

Para este dataset, recomendo iniciar com **Choice para situação de qualificação e próxima ação**. Não incluir um score de intenção nem de adequação produto-necessidade sem evidência. Suficiência de cadastro deve continuar sendo calculada pelo código, e não cobrada como descoberta da IA.

Preparação concluída: **120 casos reais**, estratificados em seis combinações de estágio, conta presente/ausente e idade acima/abaixo da referência, com 60 para desenvolvimento e 60 para avaliação. Foram produzidas perguntas e referências da política. Nenhum dado comercial inventado foi acrescentado.

As respostas esperadas foram geradas por regras e verificam **aderência à política proposta**, não verdade comercial, aprovação humana ou poder preditivo. Os resultados esperados e o nome da partição não podem ser enviados ao modelo. A partição de avaliação já está disponível localmente; deve permanecer fora do ajuste de prompts. Se for usada para ajustes, deixa de ser teste independente.

O ensaio pode revelar que Jev não agrega valor suficiente a essa política simples. Nesse caso, a conclusão honesta é uma limitação do uso escolhido. Não tornar artificialmente difícil uma regra simples nem criar notas fictícias para justificar o modelo. A arquitetura original só deve ser alterada de forma explícita após apresentar essa evidência.

## 8. Decisões de produto recomendadas

1. **Unidade de trabalho:** oportunidade na carteira de um vendedor. Filtros por gestor/região complementam essa visão; não criar competição entre vendedores por taxas históricas.
2. **Tela principal:** lista acionável com situação de qualificação, prioridade relativa, motivo verificável, lacunas e próxima ação. Data de referência visível.
3. **Separar classificação e ordem:** Jev fornece classes e ações; código aplica restrições e desempates explícitos. Uma classe não vira porcentagem de fechamento.
4. **Informação ausente não é veto:** manter oportunidades visíveis; expor encaminhamento para completar cadastro. O alerta de idade permanece visível mesmo quando outra ação tem precedência.
5. **Evitar falsa precisão:** não exibir 87/100 antes de uma definição operacional auditável. Preferir classes e posição na fila na primeira versão.
6. **LLM generativo fora do caminho obrigatório:** explicações por evidências e textos parametrizados; integrar geração apenas se resolver uma necessidade demonstrada.
7. **Sem execução externa automática:** a aplicação recomenda. Não manda mensagens, concede descontos, exclui negócios ou atualiza CRM nesta versão.
8. **Falha de API:** manter dados e regras disponíveis, identificar explicitamente o modo determinístico e não atribuir saídas desse modo ao Jev.

O benchmark por preço é uma referência de comparação, não a solução final. A composição de prioridade ainda precisa de teste: uma regra que encaminhe toda lacuna cadastral antes de qualquer ação comercial pode ocupar a agenda apenas com cadastro. Não impor uma proporção fixa entre filas sem evidência de capacidade e valor dessa operação.

## 9. Critérios de aceitação do ensaio e da primeira versão

| Área | Critério proposto |
|---|---|
| Dados | Preservar 8.800 registros na preparação; manter 2.089 abertas; zero junções multiplicativas ou descartes silenciosos. |
| Política | Saídas dentro do conjunto permitido; nenhum fato ausente convertido em fato conhecido; ausência de conta não equivale a oportunidade ruim. |
| Jev | Relatar acurácia por classe, matriz de confusão, cobertura de abstenção e inconsistências entre perguntas; meta inicial de 95% de aderência global, sem ocultar falhas de estratos. |
| Falhas críticas | Zero recomendação baseada em orçamento, intenção ou necessidade inventados no conjunto de avaliação; qualquer ocorrência bloqueia a adoção da política atual. |
| Incerteza | Limiar de confiança escolhido no desenvolvimento e congelado na avaliação; medir erro versus cobertura. Não adotar 0,8 ou 0,9 como verdade universal. |
| Repetibilidade | Repetir uma amostra e medir troca de classe/ação; resultado estável não garante correção. |
| Experiência | Motivos acessíveis no próprio item; filtro por vendedor/gestor/região; não depender de o usuário interpretar estatística. |
| Operação | Testar timeout, limite de API, resposta inválida e cache vencido; registrar origem e versão das classificações. |
| Desempenho | Meta de produto a medir: lista local disponível em até 2 segundos no ambiente de demonstração; inferência em segundo plano não bloqueia navegação. |
| Economia | Comparar custo por classificação válida na mesma amostra e contrato contra código e um modelo generativo; contabilizar tokens, falhas, repetições e cache. |

Os limiares acima são critérios de engenharia propostos, não resultados obtidos ou requisitos do G4. Com 60 casos de avaliação, mesmo zero erros não prova segurança universal; a regra aproximada de três ainda permite cerca de 5% de erro com 95% de confiança sob hipóteses binomiais. A amostragem equilibrada por estratos também não representa diretamente a distribuição de produção.

## 10. Economia e arquitetura mínima

O custo por oportunidade deve incluir entrada, saída, perguntas, repetições e chamadas auxiliares. O custo efetivo por classificação aceita é o gasto total dividido pela quantidade de saídas válidas aceitas. Comparar também latência mediana/p95, taxa de erro e necessidade de revisão humana. Não afirmar que saída curta garante menor custo total.

Cache deve considerar oportunidade, hash dos atributos relevantes, data de referência quando alterar indicadores, versão da política, perguntas e versão do modelo. Trocar critérios sem invalidar cache gera recomendações inconsistentes. Chaves de API ficam no servidor; nenhum segredo no navegador ou nos artefatos da candidatura.

Arquitetura candidata: uma aplicação Python simples, preparação tabular separada, adaptador Jev isolado e armazenamento local das classificações. Streamlit é uma opção compatível com o escopo, a confirmar quando implementarmos. Não há justificativa atual para microserviços, banco vetorial, RAG, agentes autônomos, treinamento complexo ou múltiplos provedores obrigatórios.

O objetivo comercial é uma fila útil sob capacidade limitada. Sem dados de margem, esforço, contatos, conversão causada pelo contato e receita incremental, não otimizar nem anunciar “lucro esperado por hora”. No piloto, medir tempo para escolher o próximo negócio, compreensão dos motivos e aceitação das recomendações, além da qualidade técnica.

## 11. Resultado desta etapa e sequência

Concluído: auditoria dos cinco CSVs; normalização em memória; 30 combinações de benchmark; análise de empates e incerteza; verificações de integridade e invariância a resultados futuros; contrato inicial de classificação; 120 casos reais para ensaio.

Não executado: inferência Jev, comparação com LLM generativo, medição de custo de API, aplicação para vendedores, experimento operacional ou submissão. Nenhuma credencial foi acessada e nenhum serviço de inferência foi contratado nesta etapa. Portanto, não existe evidência de qualidade ou economia do Jev neste caso ainda.

Próxima sequência recomendada: escolher e configurar um provedor/versão do Jev e limite de custo do ensaio; testar a política preparada; revisar erros; decidir a contribuição real do classificador; implementar a interface mínima e validar o fluxo completo. Caso o acesso já esteja autorizado e configurado no projeto, o ensaio pode seguir sem nova decisão de produto.

## 12. Reprodução e evidências

Com Python, pandas e numpy disponíveis, a partir desta pasta:

```text
python analisar_dados.py
python verificar_analise.py
python preparar_avaliacao_jev.py
```

As versões efetivamente usadas constam em `resultados/auditoria.json`. Os scripts não baixam arquivos, não instalam dependências, não chamam modelos e não modificam o repositório do desafio. O ZIP precisa ser a versão cujo hash está fixado no script.

Arquivos principais:

- `resultados/auditoria.json`: proveniência, auditoria, intervalos e metodologia.
- `resultados/benchmark.csv`: métricas de todas as combinações.
- `resultados/benchmark_por_vendedor.csv`: base para reamostragem por vendedor.
- `resultados/verificacao.json`: verificações executadas e limites.
- `resultados/exemplos_reais.csv`: exemplos inspecionáveis e ações do comparador.
- `resultados/casos_jev.jsonl` e `resultados/perguntas_jev.json`: preparação do ensaio, sem saídas de modelo.

As verificações passaram. Elas comprovam os cálculos e algumas propriedades de isolamento temporal; não eliminam as limitações do desenho observacional.
