# Proposta inicial do G4 AI Master Challenge

Data: 21/09/2026  
Candidato: Thiago Emanuel  
Desafio escolhido: 003: Lead Scorer  
Situação em 21/09/2026: proposta documentada, antes da inspeção dos dados e da implementação.

Este arquivo preserva as hipóteses e a conversa daquela etapa. Para conhecer a aplicação atual, consulte a [visão geral](README.md) e o [guia da aplicação](app/README.md). As pendências descritas a seguir devem ser lidas no contexto da proposta original.

Atualização de 22/09/2026: este documento preserva a proposta original. A análise dos dados e dos benchmarks está em [Avaliação técnica e de negócio](analise/AVALIACAO-TECNICA.md), e o contrato está em [Política de qualificação 0.2](analise/POLITICA-QUALIFICACAO.md). O [ensaio real do Jev pelo Vercel](analise/RESULTADO-JEV-VERCEL.md) foi concluído em 120 casos, incluindo 60 reservados para avaliação. A [stack e arquitetura acordadas](STACK-ARQUITETURA.md) definem Go, TypeScript e PostgreSQL, mantendo Jev e adiando Redis. A [base funcional local](app/README.md) já foi implementada com essa stack e verificada com PostgreSQL real, chamadas Jev, testes concorrentes e restauração de backup lógico. Os requisitos de produção permanecem pendentes.

## 1. Objetivo e contexto

Construir uma ferramenta funcional que ajude vendedores a decidir quais oportunidades de venda merecem atenção e explique os motivos da prioridade. A solução deverá utilizar os dados do desafio e registrar como a IA foi usada na sua construção.

O processo exige a escolha de apenas um desafio. Escolhi o 003 pela afinidade com minha experiência relatada em orquestração de IA, aplicações, automações e operação de produtos. Essa afinidade foi uma avaliação inicial baseada no histórico da conversa, sem verificação independente dos meus projetos. Ela não permite prever aprovação no processo seletivo.

O caso descreve 35 vendedores e aproximadamente 8.800 oportunidades. Os arquivos previstos são `accounts.csv`, `products.csv`, `sales_teams.csv` e `sales_pipeline.csv`. Esses números e campos vêm do enunciado; o conteúdo efetivo dos arquivos ainda precisa ser conferido.

## 2. Proposta de valor

> Uma ferramenta de priorização de oportunidades com qualificação assistida por Jev, critérios explícitos, explicações baseadas em evidências e indicação de informações insuficientes.

A unidade principal de avaliação será a oportunidade de venda, considerando os dados disponíveis sobre cliente, produto e momento da negociação. Um cliente com bom perfil pode ter uma oportunidade pouco promissora para determinado produto.

A interface deverá responder: “Quais oportunidades merecem minha atenção e por quê?”

## 3. Arquitetura proposta

Resumo da tecnologia: Jev é o modelo de decisões estruturadas da TypeSafe avaliado para aplicar a política de qualificação. Recebe fatos da oportunidade e critérios explícitos; retorna classificações, probabilidades e confiança. O código prepara os indicadores e valida as respostas. O ensaio pelo Vercel confirmou aderência à política em 120 casos, mas ainda não comprova melhoria de vendas ou vantagem sobre regras determinísticas. Veja [tecnologia, integração e justificativa do Jev](analise/TECNOLOGIA-JEV.md), com fontes oficiais e exemplo real.

| Componente | Responsabilidade |
|---|---|
| Preparação de dados | Relacionar as tabelas, verificar qualidade e identificar quais informações estariam disponíveis no momento da priorização. |
| Código e regras | Calcular indicadores objetivos e combinar resultados em uma prioridade com regras e pesos explícitos. |
| Jev | Ser o classificador central dos critérios de qualificação que exigem interpretação, utilizando apenas evidências fornecidas. |
| modelo de geração de texto de apoio | Quando útil, redigir explicações ou sugestões de abordagem a partir dos dados e classificações, sem acrescentar fatos sobre o cliente. |
| Interface | Apresentar ranking, motivos, informações ausentes e filtros úteis ao vendedor. |

Fluxo proposto:

Dados → preparação e indicadores objetivos → classificação pelo Jev → composição da prioridade → apresentação ao vendedor.

O modelo de geração de texto será complementar. Explicações básicas poderão ser produzidas por textos predefinidos associados aos critérios, evitando uma chamada generativa obrigatória em cada consulta.

Jev deverá ter uma contribuição substantiva na qualificação, cuja utilidade será testada. O código continuará responsável por cálculos, regras e execução do fluxo. A confiança retornada pelo classificador não será apresentada como probabilidade de fechar uma venda.

## 4. Critérios: exemplos e limites

Os critérios finais ainda não foram definidos. Os exemplos abaixo servem para orientar a investigação, e não representam informações já encontradas no dataset.

| Critério candidato | Saídas possíveis | Condição para uso |
|---|---|---|
| Compatibilidade com o perfil de cliente desejado | Alta, média, baixa, informação insuficiente | Perfil explicitamente definido e atributos relevantes disponíveis. |
| Adequação da necessidade ao produto | Compatível, incompatível, desconhecida | Evidências da necessidade e características suficientes do produto. |
| Evidência de intenção de compra | Presente, ausente, inconclusiva | Dados que sustentem a interpretação de intenção. |

Não presumir orçamento, necessidade, urgência ou intenção a partir de campos que não sustentem essas conclusões. Distinguir ausência de evidência de evidência negativa.

Critérios objetivos, como comparação de receita com um limite definido, serão calculados diretamente em código. O uso de Jev será direcionado às decisões que necessitem de interpretação.

O esquema descrito no enunciado é principalmente tabular. Ainda é necessário verificar se existem informações suficientes para justificar classificação semântica. Se os dados não sustentarem a função proposta para Jev, essa limitação deverá ser registrada e discutida antes de alterar a arquitetura; não serão inventados dados para acomodar a tecnologia.

## 5. Hipóteses a validar

Jev consegue produzir classificações úteis e consistentes para os critérios escolhidos.

Essas classificações contribuem para uma priorização defensável frente a uma regra simples de referência.

Usar Jev para decisões estruturadas pode custar menos que usar um modelo de geração de texto para a mesma tarefa. Isso ainda não foi medido.

Indicar informação insuficiente ajuda o vendedor a interpretar a prioridade sem falsa precisão.

O modelo de geração de texto agrega valor suficiente nas funções de apoio para justificar custo e complexidade adicionais.


Armazenar classificações e reutilizá-las enquanto dados e critérios permanecerem iguais foi discutido como forma de evitar chamadas repetidas. A implementação e sua necessidade ainda serão definidas.

## 6. Validação planejada

1. Conferir estrutura, campos ausentes, relações entre tabelas e limites do dataset.
2. Definir critérios, exemplos de referência e regras de combinação antes de avaliar resultados.
3. Evitar vazamento de informação: resultados futuros da negociação não poderão ser usados como atributos disponíveis em uma decisão anterior. Seu eventual uso como resultado histórico de avaliação exige separação apropriada.
4. Comparar a priorização com uma referência simples, usando uma metodologia compatível com os dados disponíveis.
5. Avaliar classificações do Jev em casos representativos, incluindo casos ambíguos e com informações insuficientes.
6. Comparar Jev e uma alternativa generativa na mesma tarefa, medindo qualidade, custo e latência. Nenhuma vantagem será anunciada antes da medição.
7. Verificar explicações, comportamento diante de falhas do serviço e clareza da interface para o vendedor.

Métricas, amostras, modelos, limites de confiança e custos aceitáveis ainda não foram definidos.

## 7. Registro da discussão e das decisões

Este registro é uma síntese da conversa, não uma transcrição literal.

1. Pedi uma avaliação da próxima fase à luz do meu histórico. Foram consultados a conversa anterior, os quatro desafios e o guia de submissão.
2. O assistente esclareceu que basta escolher um desafio e recomendou o 003 pela proximidade com a experiência em construção de software e automações que relatei.
3. Sugeri o uso de Jev. A primeira sugestão do assistente concentrou seu uso na interpretação de pedidos na interface.
4. Corrigi esse direcionamento: Jev deveria atuar na própria qualificação dos clientes, como classificador baseado em critérios estabelecidos, com potencial de economia frente a modelos generativos.
5. A proposta foi ajustada para colocar Jev no centro da classificação, com código responsável por critérios objetivos e composição da prioridade.
6. Considerei o uso de outro modelo de linguagem em conjunto, mantendo Jev como classificador essencial. O modelo generativo ficou previsto como apoio.
7. Foi refinada a unidade de análise: avaliar oportunidades, considerando cliente, produto e momento da negociação, e explicitar informações insuficientes.
8. Foi acordado avançar com essa ideia inicial, condicionando os critérios e a utilidade da classificação à inspeção dos dados.
9. Pedi que a proposta e a discussão fossem documentadas antes de prosseguir.

A interpretação de comandos em linguagem natural e o uso de Jev Browser para testar a interface foram possibilidades mencionadas, mas não integram o escopo inicial acordado.

## 8. Escopo e próximos passos

Esta etapa abrange apenas a documentação. Não foram realizados análise dos datasets, implementação, chamadas de classificação, testes de qualidade, comparação de custos ou envio da candidatura.

Sequência proposta para a próxima etapa:

1. Inspecionar os dados reais.
2. Definir critérios viáveis e a função concreta do Jev.
3. Especificar uma primeira versão enxuta e a forma de avaliá-la.
4. Implementar, testar e registrar decisões, erros, correções e resultados reais.
5. Preparar documentação de execução, limitações e entrega conforme as regras do repositório.

A stack, o provedor de acesso ao Jev, o modelo de apoio, a necessidade de credenciais e o orçamento permanecem em aberto. Não há autorização implícita neste documento para instalações, commits, publicação ou submissão.

Este arquivo inicia o registro do processo. Ele deverá ser complementado por evidências da execução; não comprova resultados técnicos ainda inexistentes.

## 9. Referências consultadas

[Repositório e regras gerais
](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge)
[Desafio 003: Lead Scorer
](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/tree/main/challenges/build-003-lead-scorer)
[Guia de submissão e process log
](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/blob/main/submission-guide.md)
[Conversa anterior: Avaliar chance na vaga
](https://chatgpt.com/c/6aa4fbe2-1e54-83e9-8fd8-201f8c8e3fd9)
[Índice oficial da documentação TypeSafe
](https://docs.typesafe.ai/llms.txt)

Também foram lidas as skills locais `jev-browser` e `typesafe-ai`. A consulta da documentação oficial confirmou acesso ao índice; páginas específicas tentadas não foram recuperadas. Contratos de API e detalhes de integração deverão ser consultados e confirmados antes da implementação.
