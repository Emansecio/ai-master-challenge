# Registro do processo em 22/09/2026

## Ferramentas utilizadas e seus papéis

Conduzi as decisões de produto, questionei as hipóteses e autorizei as etapas. Propus o uso do Jev, pedi a comparação com o Router e levantei questões de concorrência, persistência e clareza das explicações. O Codex executou análises, alterações no código e testes, cujos resultados estão registrados nas evidências de cada etapa.

| Ferramenta | Uso no trabalho e motivo |
|---|---|
| ChatGPT | Discussão inicial da candidatura e da proposta. A conversa anterior está referenciada na [proposta inicial](../PROPOSTA-INICIAL.md). Serviu para explorar o problema e organizar a ideia antes da implementação. |
| Codex | Análise dos arquivos, implementação no workspace, execução de comandos e testes e revisão da documentação nesta tarefa. O acesso ao código e ao ambiente permitiu conferir o comportamento durante a construção. |
| Agentes no Codex | Revisões delimitadas de interface, servidor, negócio e requisitos. Na revisão final, outros agentes tentaram refutar a observação documental antes da consolidação. Os [relatórios por requisito](../app/evidence/skills-review/01-requisitos.md) registram o alcance. |
| Jev, da TypeSafe, pelo Vercel AI Gateway | Classificação das oportunidades segundo critérios explícitos, com recibos preservados para conferir respostas e consumo. É um componente avaliado pela aplicação. O [ensaio](RESULTADO-JEV-VERCEL.md) documenta as chamadas e seus limites. |
| Skills de revisão | Instruções específicas para comparar requisitos, testar o navegador, revisar a interface, examinar PostgreSQL e conferir evidências antes de concluir. As cinco aplicações e a adaptação da primeira estão no [relatório da rodada](../app/evidence/skills-review/RELATORIO.md). |

Go, TypeScript, Python, Playwright e PostgreSQL foram usados para implementar e verificar a solução. Os resultados desses comandos constam nas evidências de cada etapa. A identificação do modelo de assistência em cada interação antiga não foi apurada; o registro identifica as ferramentas e os usos comprovados.

## Rodadas documentadas

Para leitura do processo, o histórico foi organizado nas 14 rodadas abaixo. Cada rodada agrupa um objetivo de trabalho e suas decisões ou verificações. Essa contagem não representa o total de mensagens, prompts ou chamadas ao Jev, que são medidas diferentes. O número total de interações de construção não foi apurado.

| Rodada | Objetivo e registro |
|---|---|
| 1 | Formular a ideia e registrar as hipóteses na [proposta inicial](../PROPOSTA-INICIAL.md). |
| 2 | Examinar os dados, comparar critérios e definir limites na [avaliação técnica](AVALIACAO-TECNICA.md). |
| 3 | Executar e conferir o [ensaio do Jev](RESULTADO-JEV-VERCEL.md). |
| 4 | Comparar a alternativa disponível no [Router público](RESULTADO-ROUTER-LOCAL.md). |
| 5 | Alinhar linguagem, persistência e processamento na [arquitetura](../STACK-ARQUITETURA.md). |
| 6 | Construir a aplicação funcional e verificar importação, acesso e persistência, conforme o [guia da aplicação](../app/README.md). |
| 7 | Examinar [dez oportunidades](REVISAO-COMERCIAL-10-CASOS.md) e a [contribuição do Jev](CONTRIBUICAO-JEV.md). |
| 8 | Revisar desempenho, auditoria e uso da interface na [rodada de polimento](RODADA-POLIMENTO.md). |
| 9 | Aprofundar os motivos e roteiros das [recomendações](QUALIDADE-RECOMENDACOES.md). |
| 10 | Incorporar a logo fornecida e ajustar a [identidade visual](DIRECAO-VISUAL.md). |
| 11 | Revisar com agentes e aplicar as [correções de interface, fila e auditoria](CORRECOES-REVISAO-LEAD-DESK.md). |
| 12 | Reorganizar e simplificar a documentação, conforme a seção Revisão da documentação deste registro. |
| 13 | Executar as [cinco revisões antes da entrega](../app/evidence/skills-review/RELATORIO.md). |
| 14 | Corrigir os pontos autorizados após a revisão e preservar a seleção na URL, conforme o [registro de implementação](../app/evidence/post-review-fixes/RELATORIO.md). |

Os relatos seguintes preservam a situação de cada etapa no momento em que ocorreu. Uma funcionalidade descrita como pendente numa etapa inicial pode ter sido implementada nas rodadas posteriores.

## Análise inicial autorizada

Pedi ao Codex que avançasse de forma autônoma na avaliação técnica, crítica e de negócio da proposta. A etapa incluiu análise local, experimentos retrospectivos e preparação de uma política de classificação. Não houve alteração no código do desafio, instalação, commit, publicação ou chamada paga de inferência.

## Trabalho executado

1. Leitura da proposta inicial, do desafio 003 e das regras de submissão.
2. Download do ZIP do dataset indicado e inspeção dos cinco CSVs. A fonte pública foi consultada também pela API de metadados do Kaggle.
3. Auditoria de campos, nulos, unicidade, datas, relações e unidades. Detectada a divergência `GTXPro`/`GTX Pro`; aplicada somente em memória.
4. Identificadas lacunas que restringem a proposta: contas ausentes em 68,2% das abertas; ausência de necessidades e interações comerciais; distribuição de duração das abertas muito diferente das encerradas.
5. Criados e executados benchmarks retrospectivos com parâmetros explícitos. Os resultados não mostraram vantagem consistente das taxas históricas simples sobre a referência de preço. Preço multiplicado pela taxa preservou a mesma ordenação, o que impede tratá-lo como diferenciação substantiva.
6. Medida a sensibilidade aos desempates e calculados intervalos exploratórios por vendedor. Registradas as limitações do estudo, incluindo ausência de histórico de alterações e dependência entre observações.
7. Consultadas as páginas oficiais TypeSafe sobre Choice, confiança e composição de scores. O acesso pelo leitor web falhou; a leitura HTTP pelo Python funcionou. Nenhuma API de inferência foi acionada.
8. Preparados contrato de política e 120 casos reais, com referências determinísticas e separação desenvolvimento/avaliação. As referências não são saídas do Jev nem rótulos de qualidade comercial.
9. Executadas verificações independentes de contagem e receita, integridade de junções, invariância dos scorers a resultados futuros e equivalência das ordens por preço e preço ponderado.
10. Redigidos parecer técnico e política proposta, com distinção entre conclusões verificadas, hipóteses e trabalho pendente.

## Revisões de julgamento

A hipótese de Jev mais econômico que um modelo de geração de texto continua sem medição. O comparador determinístico passou a ser obrigatório, porque os critérios atualmente disponíveis são estruturados.

“Qualificado” não significa necessidade confirmada nem intenção de compra. As classes propostas descrevem o estado do trabalho de qualificação.

Idade alta passou a ser tratada como motivo para verificar status, sem equipará-la a abandono ou baixa probabilidade de venda.

A classificação e a política de ordenação foram separadas. Não foram inventados pesos para produzir um score aparentemente preciso.

Receita histórica capturada por um ranking foi explicitamente distinguida de aumento de receita causado pela ferramenta.


## Resultados e limitações da análise inicial

Os scripts de análise e verificação executaram com sucesso. O diretório `resultados` contém métricas, metodologia, verificações e casos preparados. Os scripts não constituem a solução funcional exigida pelo desafio: a aplicação, o ensaio real com Jev e a validação com vendedores permanecem pendentes.

Os rótulos ainda não tinham aprovação de avaliadores humanos, e os modelos ainda não haviam sido executados nessa etapa.

## Continuação: ensaio real autorizado com Jev pelo Vercel

Autorizei o teste pelo Vercel e forneci uma chave temporária. A credencial foi armazenada em arquivo local excluído pelo `.gitignore`, sem inclusão nos artefatos do ensaio.

Foi consultada a documentação oficial do endpoint HTTP de avaliação. Implementado executor sem novas dependências, com validação do contrato, registro de latência/consumo e preservação das tentativas. Executados 12 casos iniciais, complementados os 60 de desenvolvimento e executados os 60 de avaliação, sem mudar perguntas ou exemplos.

Duas tentativas receberam HTTP 429. O executor inicialmente parava nesses erros e preservava o recibo. Foi acrescentada retomada explícita e limitada de falhas transitórias, sem repetir casos concluídos; o intervalo entre chamadas foi aumentado. Os rótulos esperados ficaram fora das requisições.

Resultado: 120 casos distintos concluídos, 240 respostas classificatórias corretas segundo a política, 122 tentativas incluindo os dois erros recuperados. Custo efetivo reportado zero nas 120 respostas bem-sucedidas; valor de mercado agregado informado pelo Gateway de US$ 0,00486381. A mediana de latência no cliente foi de 396 ms.

A auditoria dos recibos passou: hashes das fontes/perguntas inalterados, requisições reconstruídas sem os rótulos, contrato das respostas válido e ausência da credencial fora do `.env` local. O relatório [Resultado Jev pelo Vercel](RESULTADO-JEV-VERCEL.md) registra as métricas e limitações. Não houve teste com modelo generativo, implantação da aplicação ou submissão.

## Alinhamento de stack e consistência: 22/09/2026

Após o [ensaio do Router local](RESULTADO-ROUTER-LOCAL.md), decidi manter Jev e avançar com o projeto. Foi iniciado um esqueleto de servidor Python, ainda sem aplicação completa. Durante essa implementação, levantei a necessidade de concorrência e desempenho para vários vendedores e pedi maior rigor sobre persistência e cache.

Foram discutidos Go, Ruby/Rails e Rust. O direcionamento acordado passou a ser Go no servidor, TypeScript na interface e PostgreSQL como fonte oficial dos dados e das classificações versionadas. Redis ficou adiado até existir necessidade medida. Foram explicitados requisitos de processamento em segundo plano, prevenção de resultados desatualizados, detecção de edições concorrentes, autorização no servidor e recuperação testada.

A meu pedido, o alinhamento foi consolidado em [Stack e arquitetura acordadas](../STACK-ARQUITETURA.md), separando escolhas, requisitos e validações pendentes. Esta etapa alterou apenas documentação; não migrou o esqueleto Python, instalou serviços ou executou testes de carga. O porte multinacional não foi convertido em uma estimativa não medida de usuários simultâneos, e nenhuma garantia absoluta de segurança foi prometida.

## Implementação autônoma da base funcional: 22/09/2026

Autorizei a construção da aplicação em Go, TypeScript e PostgreSQL. A implementação usou um container exclusivo, com volume persistente e papel usado pela aplicação sem superusuário. O setup importa os 8.927 registros das quatro tabelas, prepara 2.089 oportunidades abertas e reaproveita 120 classificações reais compatíveis com o ensaio anterior. Naquela etapa, o esqueleto Python e o repositório original do desafio foram preservados.

Implementados API de carteira, filtros, prioridade explicada, edição local da conta com versão, perfis de acesso, sessões, fila persistente, limites globais de chamadas e validação de respostas Jev. Os testes de integração usam um PostgreSQL real em base separada. As respostas controladas desses testes são identificadas como respostas controladas de teste e não são contadas como inferências do modelo.

Na primeira rodada, os testes encontraram falta de permissão para bloquear a linha de política; foi concedido UPDATE somente na coluna identificadora, preservando a restrição sobre o conteúdo da política. A revisão identificou também que a marcação de uma reserva esgotada precisava ser confirmada mesmo quando nenhum novo trabalho fosse encontrado; foi corrigido e adicionado teste específico. Outro teste protege a revalidação do modelo contra reimportação de respostas antigas como se fossem novas.

O fluxo real foi exercitado em UP409DSB pela API e em VDIU10RV pela interface. Ambas as novas respostas foram validadas e persistidas; o Gateway reportou custo zero. A reutilização foi comprovada antes e depois de reiniciar o servidor. Ondas locais de 35 e 100 consultas simultâneas à carteira terminaram sem erros, com p95 de aproximadamente 741 ms e 1.166 ms. Não se trata de teste de capacidade sustentada ou SLA.

O backup lógico foi restaurado em outra base e conferido por contagens e assinaturas dos dados e classificações. No navegador foram verificados login, perfil de vendedor, filtros, busca vazia, paginação, consulta ao Jev e organização visual em desktop/tela estreita. O README registra comandos e limitações, incluindo ausência de SSO, PITR, alta disponibilidade e validação comercial. Não houve deploy, commit ou submissão.

Evidências: [aplicação e instruções](../app/README.md), [testes](../app/evidence/tests.txt), [HTTP e Jev real](../app/evidence/http-live.json), [reinício](../app/evidence/restart.json), [restauração](../app/evidence/backup-restore.json) e [interface](../app/evidence/ui.json).

## Revisão dos três primeiros passos: 22/09/2026

Autorizei a revisão de dez oportunidades, a avaliação da contribuição do Jev e os ajustes de interface decorrentes dos achados. Foram selecionados dez casos do conjunto de avaliação, cobrindo seis estratos e situações de limite/preço. Foram confrontados estados e respostas atuais da API com os recibos originais. A revisão técnica identificou que o caso A7SA2L21 demanda confirmação de atividade além do vínculo de empresa, e usa referência global por ter apenas 25 negócios encerrados do produto.

Uma implementação independente das regras para os estados válidos do ensaio foi comparada às respostas preservadas: ambos os métodos coincidem com a referência em 60/60 casos de desenvolvimento e 60/60 de avaliação. Essa referência é determinística; não há demonstração de melhor decisão comercial ou economia frente a modelo generativo. Não houve nova chamada ao Jev, enriquecimento externo ou criação de dados comerciais.

Na interface, acrescentados roteiro de conferência por ação, indicação da origem/tamanho do histórico do produto e proporção sem conta com acesso à fila. O rótulo do Jev passou a explicitar concordância com a política. No detalhe de produtos com pouco histórico, a explicação apresenta a referência global corretamente. Os critérios, contratos, ordenação e dados persistidos não foram alterados.

Compilação TypeScript concluída. Testes Go e vet passaram; a integração PostgreSQL não foi repetida nesta revisão de interface. Verificados no navegador os dez casos, fila de cadastro, ausência de aviso residual na busca vazia, explicação global e tela estreita. A revisão comercial por vendedor não foi simulada: continua pendente, com perguntas documentadas caso a caso.

Entregas: [revisão dos casos](REVISAO-COMERCIAL-10-CASOS.md), [contribuição do Jev](CONTRIBUICAO-JEV.md), [comparativo reproduzível](../app/evidence/business-review.json) e [verificação da interface](../app/evidence/business-ui.json).

## Polimento antes da submissão: 22/09/2026

Esclareci que a validação com vendedores depende de acesso posterior ao envio. Em seguida, autorizei uma rodada de revisão da análise, do desempenho, da auditoria e da interface, incluindo informações apresentadas e acessibilidade.

A medição confirmou desperdício de leitura/decodificação de toda a carteira em cada página. A paginação foi movida para SQL, preservando resultados, contagens e ordenação; os filtros de metadados passaram a ser agregados diretamente. Foram acrescentados histórico consultável com escopo de acesso, preservação de rascunhos, tratamento de falhas de inicialização/conexão, limpeza de estado entre sessões e melhorias de contraste, tipografia, foco e anúncios de carregamento.

Os testes PostgreSQL foram ampliados e passaram, incluindo comparação de 600 combinações e todas as 105 páginas, além de autorização, versões e limitação explícita do histórico. A carga local de leitura por 30 segundos com 100 clientes teve p95 de 853,1 ms antes e 114,9 ms depois, sem erros; os contratos HTTP coincidiram. Não houve nova inferência Jev.

Na cópia isolada do banco foram exercitados gravação pela interface, conflito concorrente, falha de conexão/reinício, falha da consulta inicial/nova tentativa e troca de perfil. A cópia foi encerrada e removida ao concluir. As verificações visuais cobriram 320, 390 e 1280 pixels; medições parciais de contraste foram registradas, sem alegar certificação WCAG. A aplicação principal foi reiniciada ao final e ficou disponível para revisão.

O [relatório completo](RODADA-POLIMENTO.md) contém as evidências e limitações. Nenhum deploy, commit, submissão, instalação ou validação comercial foi realizado nesta rodada.
## Explicações, identidade visual e revisão da aplicação

As explicações passaram a separar o critério aplicado, os fatos disponíveis e as perguntas sugeridas. A comparação de duração informa valores em dias, origem da referência e tamanho do histórico do produto. O caso sem empresa e com duração elevada mantém os dois sinais visíveis. O módulo de apresentação foi testado sem mudar as decisões do servidor. O trabalho está descrito em [Qualidade das recomendações](QUALIDADE-RECOMENDACOES.md).

A logo que enviei foi incorporada à interface com sua proporção e transparência preservadas. Cabeçalho, tela de acesso e cores foram ajustados e conferidos em computador e celular. O [registro visual](DIRECAO-VISUAL.md) preserva as decisões e capturas.

A meu pedido, três agentes revisaram experiência do atendente, qualidade das orientações e funcionamento do servidor. A revisão foi somente leitura. Depois que autorizei a implementação, foram corrigidos contexto das mensagens, preservação do foco, processamento de pedidos já desatualizados e registro das interrupções. O formulário de cadastro passou para o início do detalhe, e foi acrescentado o resumo de conferência copiável.

A implementação passou por testes de banco isolado, 11 testes de recomendações e dez verificações de interface. A base principal manteve suas contagens e não houve nova consulta real ao Jev. O [relatório das correções](CORRECOES-REVISAO-LEAD-DESK.md) registra o alcance, a migração e as evidências.

## Revisão da documentação

Pedi uma redação clara, explicativa e com menos termos desnecessários. A revisão criou uma [visão geral](../README.md), reorganizou o [guia de execução e uso](../app/README.md) e atualizou a arquitetura, os critérios e a explicação do Jev para corresponderem à implementação. Comandos e evidências de testes foram preservados. A proposta inicial continua identificada como registro histórico.

Esta etapa altera documentação. Não acrescenta resultado de teste, validação comercial, publicação ou submissão.


## Organização da entrega

Após as 14 rodadas de construção, a entrega foi organizada na minha pasta de submissão, com README no template e índice do processo. Os cinco documentos oficiais foram conferidos novamente e correspondiam às cópias locais. A cópia foi compilada e testada com banco novo, credenciais novas e sem chave do Jev. O [registro da entrega](../../docs/ENTREGA.md) contém os resultados, a ocorrência de timeout no primeiro teste de navegador e os arquivos excluídos do pacote. Nenhum commit ou envio foi realizado.
