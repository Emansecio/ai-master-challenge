# Correções da revisão do Lead Desk

Em 22/09/2026, foram implementadas as correções identificadas na revisão da interface, do fluxo comercial e do servidor. Os critérios de classificação, a ordem da carteira e os dados comerciais foram preservados.

## Mensagens e navegação

As mensagens de salvamento, cópia e erro identificam a oportunidade que originou a operação. Se o usuário abrir outro registro antes da resposta, o novo detalhe não exibe uma confirmação que pertence ao anterior. Respostas de uma sessão encerrada são ignoradas.

As seções expansíveis têm identificação estável. Durante atualizações, a aplicação preserva o foco do teclado, as seções abertas e o conteúdo do histórico. Esse cuidado também alcança os controles internos da auditoria quando uma nova consulta termina.

## Cadastro e resumo de conferência

Na fila Cadastro, o formulário de vínculo aparece no início do detalhe. O texto pede confirmação da empresa no sistema de origem. Continua existindo um único formulário por oportunidade, com controle de versão e preservação de alterações ainda não salvas durante a navegação.

O resumo de conferência reúne ID, versão, data histórica, fatos, alertas simultâneos, perguntas e limites da orientação. O texto pode ser revisado e copiado. Ele é produzido pelas regras de apresentação, sem nova chamada ao modelo, e não comprova contato com o cliente. Se a cópia automática falhar, a interface seleciona o conteúdo para cópia manual.

## Pedidos desatualizados e interrupções

Antes de reservar um pedido para execução, a fila compara sua versão e política com os dados atuais. Uma pendência já desatualizada é encerrada sem outra tentativa. Se a alteração ocorrer depois dessa conferência, a verificação final continua impedindo que uma resposta antiga seja publicada como atual.

Quando uma reserva de processamento vence, o banco registra um evento `interrupted` por tentativa. O evento não se repete na recuperação nem recebe uma duração presumida. O identificador de reserva continua impedindo que um processo antigo publique uma resposta depois de ser substituído. O limite de tentativas também permanece em vigor.

A auditoria apresenta `attempt_count` e até 20 registros em `attempts`. Cada registro informa identificação, versão, política, resultado, momento de gravação e duração medida ou desconhecida. O acesso continua limitado ao perfil do usuário. Credenciais e conteúdo interno da resposta do provedor não são expostos.

## Alteração do banco local

A única mudança na estrutura permite que a duração de uma tentativa seja desconhecida:

```sql
ALTER TABLE job_attempts ALTER COLUMN elapsed_ms DROP NOT NULL;
```

O comando foi incluído na preparação do banco e aplicado como administrador antes de reiniciar o servidor local na porta 8766. Pode ser repetido sem alterar o resultado. Não modifica eventos anteriores nem cria registros de interrupções passadas.

## Verificações executadas

| Verificação | Resultado e alcance |
|---|---|
| `npm run build` | TypeScript compilado sem erros. |
| `go test ./...` e `go vet ./...` | Aprovados. Nessa execução geral, os testes de banco foram ignorados conforme a configuração padrão. |
| `go test ./internal/store -count=1 -v`, com `LEADDESK_INTEGRATION=1` | 16 testes principais e dois subcasos aprovados em PostgreSQL temporário isolado, em 18,084 segundos. O conjunto de testes criou e removeu sua própria base. |
| `node --test scripts/recommendation.test.mjs`, com `LEADDESK_LIVE_TEST=1` | 11 testes aprovados, incluindo conteúdo do resumo e leitura das 2.089 oportunidades nas 105 páginas. |
| Interface | Dez verificações aprovadas, cobrindo mensagens, foco, cópia, auditoria e apresentação em tela de 320 px. |

Os testes de banco incluem descarte por mudança de versão ou política, recuperação de interrupções, limite de tentativas e rejeição de resultados de processos antigos. Também verificam ausência de eventos duplicados, permissões, limite de registros da auditoria, concorrência, importação e paginação.

Salvamento atrasado, atualização periódica e cópia de texto foram exercitados com respostas controladas em uma aba descartável. Todas as solicitações de dados dessa aba eram interceptadas, sem gravação no banco. A aplicação real foi usada para conferir a ordem do formulário, a auditoria, o tamanho da tela e o resumo. Não foram observados erros no console da aba real.

Antes e depois da implementação, a base principal tinha 2.089 oportunidades, 2.089 versões, 122 classificações, dois trabalhos e duas tentativas. Não houve edição comercial nessa base nem nova chamada real ao Jev.

## Evidências e reprodução

| Arquivo | Conteúdo |
|---|---|
| `app/evidence/review-fixes-ui.json` | Resultado das dez verificações da interface. |
| `app/evidence/review-fixes-desktop.png` e `review-fixes-mobile.png` | Capturas da aplicação real. |
| `app/evidence/review-fixes-recommendation-tests.txt` | Saída dos 11 testes de apresentação e leitura. |
| `app/internal/store/queue_regression_test.go` | Testes das correções de fila e auditoria. |
| `app/scripts/ui-regression-fixture.mjs` | Respostas controladas usadas exclusivamente nos testes de navegador. |

O último arquivo recebe dois casos de `business-review.json`, intercepta `/api/` e permite liberar um salvamento atrasado, simular atualizações e negar a cópia automática. Ele foi carregado pelas ferramentas de desenvolvimento numa página local descartável, junto ao HTML e ao módulo reais. A aba foi fechada ao terminar. O servidor não disponibiliza esse arquivo na interface de uso.

Os comandos automatizados devem ser executados dentro de `app`. A integração exige PostgreSQL local, e a leitura completa exige o servidor ativo. O teste de navegador depende da preparação explícita de uma aba isolada; não foi instalado um novo programa para automatizar esses testes.

## Limites desta verificação

Não foram repetidos os testes de carga, nem realizadas avaliação com vendedores ou novas consultas reais ao modelo. As correções verificam o funcionamento técnico e não demonstram aumento de conversão ou qualidade comercial. Uma chamada interrompida no provedor ainda pode exigir repetição; o histórico mantém essa incerteza explícita.
