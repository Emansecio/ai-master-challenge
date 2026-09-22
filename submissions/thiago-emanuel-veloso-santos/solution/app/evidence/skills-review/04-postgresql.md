# Revisão do PostgreSQL

Aplicada supabase-postgres-best-practices à camada Go de persistência, ao esquema, à fila e às consultas reais. A análise incluiu regras de conexões, índices, transações curtas, ordenação de bloqueios, SKIP LOCKED, paginação, privilégios, estatísticas e planos de execução. Nenhuma alteração foi aplicada no esquema ou na configuração da base principal.

## Ajuste recomendado no código

`app/internal/store/store.go:276`: quando a conta recebida já corresponde à gravada, SetAccount retorna por s.Get antes de executar o rollback adiado. A transação iniciada em L250 ainda mantém sua conexão e o bloqueio de L256; s.Get usa o pool novamente em L191. A aquisição de uma segunda conexão enquanto a primeira permanece reservada pode esperar por capacidade sob concorrência. O retorno normal após uma alteração efetiva ocorre depois de Commit e não tem essa mesma propriedade.

Trata-se de um risco de concorrência identificado por leitura do fluxo, não de travamento observado nesta rodada. A menor correção é encerrar a transação antes da leitura externa ou realizar a leitura usando a transação já disponível. O botão da interface evita enviar uma conta sem alteração, o que reduz a ocorrência no fluxo comum. Os testes atuais de edição não demonstram cobertura desse caminho sob falta de conexões. Nenhum teste de saturação ou interrupção de serviço foi realizado.

## Medições

[postgres-results.json](postgres-results.json) reúne metadados e cinco planos obtidos por EXPLAIN ANALYZE da consulta de paginação extraída do código. As consultas ocorreram em transações somente leitura, com o papel leaddesk e limite local de cinco segundos. Foram incluídas primeira e última páginas, vendedor, região e busca.

| Consulta | Execução observada |
|---|---|
| Administrador, primeira página | 79,667 ms |
| Administrador, última página | 34,859 ms |
| Carteira de vendedor | 25,976 ms |
| Região East | 2,468 ms |
| Busca Acme | 27,943 ms |

São amostras individuais instrumentadas, com aquecimento e compilação interna variáveis. Não constituem comparação controlada entre as consultas nem tempo de resposta HTTP. O primeiro plano registra compilação JIT. Nenhum plano precisou ordenar em disco; o filtro de vendedor utilizou opportunity_agent. A leitura completa da pequena carteira do administrador não justifica, por si só, criar outro índice.

[read-performance.json](read-performance.json) registra ondas curtas de GET com até 1, 35 e 100 tarefas concorrentes, usando seis caminhos. Foram 705 solicitações medidas, além de seis leituras de referência, sem erro ou alteração de contrato. P95 observado: 22,2 ms, 60,7 ms e 43,7 ms, respectivamente. A onda posterior teve mais aquecimento; não se pode concluir que mais concorrência melhora a latência. O executor limita o máximo de tarefas, sem garantir que todas atinjam o servidor no mesmo instante. O ensaio é local e breve, sem garantia de capacidade corporativa.

## Propriedades conferidas

| Área | Resultado |
|---|---|
| Conexões | pgxpool limitado a 12 conexões por processo; servidor PostgreSQL configurado para 100. Não há uma conexão nova por vendedor. |
| Privilégios | Papel leaddesk sem superusuário, criação de banco, criação de papéis ou bypass de RLS. |
| Histórico | Chaves compostas vinculam classificação e trabalho à versão; versões e tentativas têm restrições de unicidade. |
| Paginação | Contagem, seleção e agrupamento compartilham uma instrução SQL e a mesma visão dos dados. |
| Fila | Reserva com SKIP LOCKED, limitação compartilhada, token de reserva e revalidação antes de publicar. |
| Chamada externa | O contato com Jev acontece após a transação de reserva ter sido concluída. |
| Estatísticas locais | Autovacuum habilitado, zero deadlocks registrados para a base e nenhuma transação ociosa observada nas amostras. |

Os testes de integração passaram: 16 testes principais e dois subcasos, em 20,068 segundos. Usaram PostgreSQL real em uma base temporária própria, removida pelo conjunto de testes. Cobrem importação, duplicatas, edições concorrentes, resposta tardia, troca de política, recuperação, tentativas, permissões, paginação e auditoria. Ver [saída completa](postgres-tests.txt).

## Recomendações condicionais

`app/internal/store/store.go:46`: os limites de conexão estão explícitos, mas não há prazo próprio para consulta ou espera por bloqueio nessa configuração. Os valores globais de statement_timeout, lock_timeout e idle_in_transaction_session_timeout estão em zero. Definir esses limites por operação ou papel seria uma proteção adicional para operação prolongada. Não houve consulta travada nesta medição. O timeout de escrita HTTP não deve ser tratado como prova de cancelamento da operação no banco.

`app/internal/store/read.go:38`: OFFSET e a ordenação da seleção devem ser reavaliados se a carteira crescer significativamente. Com 2.089 registros e os resultados atuais, não foi demonstrada necessidade de trocar a paginação ou criar índices preventivos.

RLS, alta disponibilidade e divisão entre organizações seguem como limites explicitamente documentados da demonstração. Esta revisão não os transforma em funcionalidades obrigatórias do desafio. As regras da skill foram avaliadas de acordo com o uso local real.

Fonte: [supabase-postgres-best-practices](https://raw.githubusercontent.com/supabase/agent-skills/main/skills/supabase-postgres-best-practices/SKILL.md).
