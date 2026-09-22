# Guia da aplicação Lead Desk

O Lead Desk reúne as 2.089 oportunidades abertas do conjunto de dados e apresenta uma orientação para cada uma. O vendedor pode consultar sua carteira, entender os critérios, confirmar a empresa vinculada e acompanhar o histórico do registro.

A aplicação funciona localmente com Go, TypeScript e PostgreSQL. As regras locais oferecem a orientação inicial. A consulta ao Jev é opcional durante o uso e serve para conferir a classificação segundo os mesmos critérios. A prioridade organiza o trabalho; sua capacidade de melhorar vendas ainda não foi demonstrada.

A [visão geral do projeto](../README.md) explica a proposta para quem está conhecendo a solução. Este guia reúne instalação, uso e cuidados de operação.

## Executar no Windows

É necessário ter Go 1.26 ou superior, Node.js 22 ou superior, PowerShell 7 e Docker Desktop com o ambiente Linux em execução. O PostgreSQL roda em um contêiner próprio; não precisa ser instalado diretamente no Windows. O arquivo Compose fixa a versão e a identificação da imagem usada.

A partir da pasta `solution` da submissão, que contém `app` e `analise`:

```powershell
cd app
./scripts/init-local.ps1
npm ci --ignore-scripts
npm run build
go run ./cmd/leaddesk -mode setup
go run ./cmd/leaddesk -port 8766
```

Abra [a aplicação local](http://127.0.0.1:8766). As portas 55432, do banco, e 8766, da aplicação, precisam estar disponíveis. Para mudar a porta da aplicação, passe `-port NUMERO` ao iniciar o servidor.

A preparação cria códigos aleatórios para os perfis `admin`, `gestor` e `vendedor`, guardados em `.local/access-codes.json`. Copie o código do perfil desejado para o formulário de acesso. O gestor e o vendedor de demonstração ficam vinculados, respectivamente, à equipe e ao vendedor da primeira oportunidade aberta importada.

Esses códigos são credenciais locais e não devem aparecer em arquivos de entrega ou capturas de tela. O banco guarda apenas suas assinaturas criptográficas. A sessão dura oito horas e usa cookie HttpOnly/SameSite=Strict. O serviço aceita conexões somente da própria máquina; o acesso HTTP local não está preparado para exposição na internet.

O banco mantém seus dados em um volume persistente. O script de preparação preserva as credenciais já geradas em `.local/dev.env`. Para parar o banco sem apagar o conteúdo:

```powershell
docker compose --env-file .local/dev.env stop
```

O comando `down -v` apaga o volume e não deve ser usado para uma parada normal.

## Dados importados

O arquivo `../analise/dados/crm-sales-predictive-analytics.zip` acompanha a entrega, com origem e licença descritas em [dados utilizados](../analise/dados/README.md). Para informar outro caminho:

```powershell
go run ./cmd/leaddesk -mode setup -data "C:/caminho/crm-sales-predictive-analytics.zip"
```

A preparação confere a assinatura SHA-256 do ZIP, importa 8.927 registros de quatro tabelas e deriva as 2.089 oportunidades abertas. Os registros originais são preservados. A diferença de escrita `GTXPro`/`GTX Pro` é tratada ao relacionar os produtos.

O conjunto é histórico. A data de 31/12/2017 é a referência dos cálculos, e os registros não representam clientes atuais da G4. Necessidade, orçamento, intenção de compra e último contato permanecem desconhecidos.

## Configurar o Jev

Defina `AI_GATEWAY_API_KEY` no ambiente ou em `app/.env`, seguindo `.env.example`. Neste projeto, a configuração existente em `analise/.env` também é reconhecida. A credencial fica no servidor e não é enviada ao navegador nem incluída nos recibos. Abrir a carteira não consulta o modelo.

Quando dados, perguntas, política e identificação de revalidação correspondem ao ensaio preservado, a preparação importa suas 120 classificações reais. Repetir essa importação não cria duplicatas nem sobrescreve edições locais. Sem os recibos anteriores, novas classificações dependem do acesso ao Jev.

Duas consultas reais adicionais foram realizadas durante a construção da aplicação e permanecem na base local original. Uma instalação nova importa as 120 classificações do ensaio que acompanham a entrega. As evidências das duas consultas adicionais também foram preservadas, mas não são importadas pelo setup. O Gateway informou custo zero nessas respostas e nas 120 respostas bem-sucedidas do ensaio original. Esse registro não garante gratuidade em consultas futuras.

O comando `setup` usa acesso administrativo ao PostgreSQL. Durante o uso normal, o serviço usa o papel `leaddesk`, sem privilégio de superusuário, criação de banco ou alteração do histórico de versões.

## Usar a carteira

1. Busque uma oportunidade ou filtre por vendedor, gestor e região. As permissões são conferidas no servidor, mesmo quando o usuário altera os filtros.
2. Escolha uma fila e abra o detalhe. O motivo, os fatos e a comparação de duração ajudam a entender a orientação.
3. Na fila Cadastro, confirme a empresa no CRM de origem e selecione o vínculo correto. Salvar cria uma nova versão e invalida a classificação anterior. Duas edições baseadas na mesma versão produzem um aviso de conflito.
4. Consulte o roteiro em Como conduzir o atendimento. As perguntas indicam o que ainda precisa ser confirmado com o cliente. As respostas devem ser registradas no CRM de origem.
5. Abra Resumo para levar ao CRM para revisar e copiar o texto. Ele inclui ID, versão, data histórica, fatos e perguntas pendentes. A cópia não registra contato nem atualiza outro sistema. Se a cópia automática falhar, o texto fica selecionado para cópia manual.
6. Quando desejar conferir a classificação pelo modelo, use Classificar com Jev. A interface acompanha o processamento e informa eventual falha. Um resultado compatível é reutilizado enquanto os dados e os critérios continuarem iguais.

A busca, a fila, os filtros de equipe e a página ficam registrados na URL. Recarregar, abrir o endereço em outra aba e usar voltar ou avançar restaura a seleção. O acesso continua limitado ao perfil autenticado. Filtros de equipe indisponíveis para esse perfil são descartados, parâmetros inválidos são normalizados e uma página além do resultado é ajustada para a última disponível. Alterações de cadastro ainda não salvas permanecem somente na memória da aba.

Ao copiar o resumo, a confirmação aparece junto do botão. Se a cópia automática falhar, a orientação para copiar manualmente aparece no mesmo lugar e o texto fica selecionado. A mensagem acompanha a oportunidade de origem e não é atribuída a outro registro durante a navegação.

O aviso de cadastro informa quantas oportunidades estão sem empresa e sua proporção na seleção atual. Falta de cadastro não significa baixo potencial comercial.

Alterações ainda não salvas ficam na memória da aba enquanto o usuário navega ou atualiza a consulta. Elas não são salvas automaticamente e se perdem ao fechar ou recarregar a aba. A aplicação avisa antes de sair com alterações pendentes. Mensagens de operações identificam a oportunidade de origem, e as atualizações preservam o foco do teclado e as seções abertas do detalhe.

## Entender a prioridade

A carteira é ordenada primeiro por tipo de ação: revisão humana de dados inconsistentes; revisão de negociações identificadas acima da referência de duração; qualificação de prospecções identificadas; próximo passo das demais negociações identificadas; e confirmação de empresas ausentes.

A fila Cadastro pode ser aberta diretamente. Sua posição posterior na lista geral não classifica seus clientes como comercialmente piores. Dentro da revisão de negociação, considera-se o excesso relativo de duração. Preço de catálogo e ID desempatam os registros restantes, conforme a regra de ordenação.

A referência P90 abrange aproximadamente 90% das durações dos negócios encerrados usados no cálculo, incluindo ganhos e perdas até 31/12/2017. A aplicação usa o histórico do produto quando há pelo menos 30 encerramentos; com menos exemplos, usa a referência global. Igualar a referência não significa ultrapassá-la.

A duração não informa quando ocorreu o último contato. O preço de catálogo também não informa o valor total de uma oportunidade. Os detalhes completos estão na [política de qualificação](../analise/POLITICA-QUALIFICACAO.md).

## Ler a classificação e o histórico

A indicação Jev · coerente com a política significa que as duas respostas do modelo coincidiram com os critérios locais. O servidor confere as alternativas, as probabilidades e a compatibilidade das escolhas com os fatos. Uma resposta incompatível não é publicada como orientação válida do Jev.

Os percentuais do modelo não medem chance de venda. As explicações são montadas a partir dos campos e das regras; não usam texto comercial inventado. O [estudo da contribuição do Jev](../analise/CONTRIBUICAO-JEV.md) explica por que concordar com a regra ainda não demonstra benefício comercial adicional.

Histórico e rastreabilidade reúne versões dos dados, classificações e tentativas registradas. Cada grupo mostra até 20 registros recentes e a contagem total. As informações incluem autor, origem, momento do registro e correspondência com a versão e a política atuais.

Uma interrupção indica que a reserva de processamento venceu antes de uma conclusão local válida. Sua data é a da detecção e a duração fica desconhecida quando não houve medição. Um recibo importado ou um pedido ainda aguardando processamento não equivale a uma tentativa local concluída. O endereço `GET /api/opportunities/{id}/audit` aplica o mesmo controle de acesso da carteira.

## Processamento e proteção dos resultados

A fila fica no PostgreSQL. Duas tarefas de processamento podem consultar o Jev ao mesmo tempo, com pelo menos dois segundos entre inícios de chamadas. Esses limites foram escolhidos de forma conservadora para o ensaio; não representam uma capacidade ótima já demonstrada.

Cada pedido identifica oportunidade, versão dos dados e assinatura dos critérios, incluindo modelo e identificação de revalidação. O banco impede duplicatas dessa combinação. Antes de reservar um pedido, o serviço confere se ele ainda corresponde aos dados atuais. Um pedido já desatualizado é encerrado sem uma nova tentativa.

A chamada externa tem limite de 30 segundos, e a reserva do trabalho dura 45 segundos. Outro processo pode recuperar uma reserva vencida. Um identificador de reserva impede que o processo anterior publique uma resposta depois de ser substituído. A recuperação registra uma interrupção por tentativa, sem duplicar o evento nem inventar sua duração.

Falhas temporárias permitem até três tentativas no total, com espera progressiva. Ao esgotar esse limite, ou diante de uma falha que não permite repetição, a interface indica necessidade de revisão técnica. Clicar repetidamente não reinicia o mesmo pedido indefinidamente.

Antes de gravar um resultado, a aplicação confere novamente a versão e a política dentro da mesma transação de banco. As leituras repetem essa conferência. Uma resposta que ficou desatualizada durante a chamada permanece no histórico e não aparece como atual.

Esses controles protegem a publicação do resultado. Uma interrupção depois da resposta externa e antes da gravação local ainda pode exigir outra chamada ao provedor.

Uma correção anterior permitiu duração desconhecida em `job_attempts.elapsed_ms`. A alteração de esquema é aplicada pelo `setup`; instalações existentes precisam aplicá-la antes de iniciar o servidor atualizado. O [relatório da revisão](../analise/CORRECOES-REVISAO-LEAD-DESK.md) registra o comando SQL e a validação.

O provedor disponibiliza um nome de modelo que não identifica sua revisão interna exata. Para iniciar outra identificação de revalidação, use o mesmo valor nas duas operações:

```powershell
go run ./cmd/leaddesk -mode setup -model-epoch "revalidacao-02"
go run ./cmd/leaddesk -port 8766 -model-epoch "revalidacao-02"
```

As respostas antigas do ensaio não são importadas como novas nessa identificação. Possíveis mudanças internas do provedor ainda exigem acompanhamento antes do uso em produção.

## Verificações e evidências

A [conferência da entrega](../../docs/ENTREGA.md) registra a instalação desta cópia em banco vazio, os resultados e os limites do ensaio. Os relatórios abaixo preservam as etapas anteriores da construção.

Os comandos abaixo devem ser executados dentro de `app`:

```powershell
# Política e transporte, sem consultar IA externa
go test ./...

# Inclui banco PostgreSQL real em base temporária isolada
$env:LEADDESK_INTEGRATION = '1'
go test ./... -count=1 -v
go vet ./...

# Com o servidor em execução; Python 3.11+ somente para este verificador HTTP
python scripts/check-live.py --port 8766
# Acrescenta uma consulta REAL ao Jev, com possível cobrança do provedor
python scripts/check-live.py --port 8766 --live

# Backup lógico e restauração em banco separado; executar sem gravações concorrentes
./scripts/backup-verify.ps1
```

Sem `LEADDESK_INTEGRATION=1`, os testes de banco são explicitamente ignorados. Com essa variável, o conjunto de testes cria e remove apenas sua própria base temporária. Respostas controladas aparecem como `test_fixture` e não contam como consultas reais ao modelo. O verificador HTTP com `--live` faz uma consulta real, com possível cobrança.

| Verificação | Evidência e alcance |
|---|---|
| Política, concorrência, permissões e fila | [Testes da implementação inicial](evidence/tests.txt). Incluem comparação com os 120 casos, conflitos de edição, respostas atrasadas e recuperação. |
| Consulta real e reutilização | [Registro HTTP](evidence/http-live.json) e [reinício](evidence/restart.json). Duas novas classificações foram preservadas e reutilizadas. |
| Restauração | [Conferência do backup](evidence/backup-restore.json). A cópia foi restaurada em outra base e comparada por contagens e assinaturas. |
| Revisão dos casos | [Dez oportunidades](../analise/REVISAO-COMERCIAL-10-CASOS.md) e [comparação reproduzível](evidence/business-review.json). Revisão técnica, ainda sem julgamento independente de vendedores. |
| Últimas correções | [Correções após as cinco revisões](evidence/post-review-fixes/RELATORIO.md). Incluem 49 verificações de interface, 17 testes principais de banco e 11 testes de recomendações. |
| Interface | [Verificação inicial](evidence/ui.json), [revisão comercial](evidence/business-ui.json) e [última revisão](evidence/review-fixes-ui.json). Incluem fluxo de navegação, foco, mensagens e tela de 320 px. |

Para repetir a conferência dos dez casos, execute `python app/scripts/review-business.py` na raiz do projeto, com o servidor ativo. A verificação usa os recibos existentes e não chama o Jev.

Os testes locais de desempenho têm condições diferentes e devem ser lidos separadamente. Nas primeiras ondas de 35 e 100 consultas simultâneas, o p95 foi de aproximadamente 741 ms e 1.166 ms. Na rodada posterior, com 100 clientes por 30 segundos, passou de 853,1 ms antes da alteração de paginação para 114,9 ms depois. P95 significa que 95% das respostas medidas terminaram até aquele tempo. Os ensaios terminaram sem erros, mas não estabelecem uma garantia de desempenho em produção. A metodologia está no [relatório de polimento](../analise/RODADA-POLIMENTO.md).

## Limites da instalação atual

A demonstração atende uma organização e oferece três perfis locais. Não há autenticação corporativa, autenticação em duas etapas, provisionamento de usuários ou separação entre organizações independentes. As permissões são aplicadas pelo servidor; políticas por linha do PostgreSQL não foram configuradas, e o serviço compartilha um papel de acesso ao banco.

O banco é único. Alta disponibilidade, conexões protegidas entre máquinas, operação em várias regiões e capacidade necessária para produção dependem de definição e testes. A restauração de backup local foi exercitada; recuperação para um instante específico, agendamento, cópia externa e metas de recuperação continuam pendentes.

O detector de corridas do Go não foi executado neste Windows, que está sem CGO e compilador C. Os testes concorrentes de banco foram executados. As verificações de contraste e foco são parciais e não constituem certificação de acessibilidade.

A submissão do desafio está no [PR 146](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/146). A aplicação continua com execução local e ainda não foi validada com vendedores. A revisão humana continua necessária para medir utilidade comercial, compreensão das orientações e eventuais decisões inadequadas.

## Organização dos arquivos

| Pasta | Conteúdo |
|---|---|
| `cmd/leaddesk` | Preparação e inicialização do servidor. |
| `internal/core` | Leitura dos dados e critérios de qualificação. |
| `internal/store` | PostgreSQL, versões, permissões e fila. |
| `internal/service` | Comunicação com o Jev e processamento em segundo plano. |
| `internal/web` | Rotas da aplicação e sessões de acesso. |
| `frontend` e `static` | Código TypeScript e arquivos usados pelo navegador. |
| `scripts` | Preparação do ambiente e verificações. |
| `.local` | Credenciais, executáveis e cópias privadas, excluídos pelo `.gitignore`. |

O servidor entregue é o de Go. O protótipo Python anterior não faz parte do pacote de submissão. Os scripts Python de análise e verificação foram mantidos.
