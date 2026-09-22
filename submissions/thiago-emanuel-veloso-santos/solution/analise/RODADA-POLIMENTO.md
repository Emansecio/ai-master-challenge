# Rodada de polimento e verificação — 22/09/2026

Escopo autorizado: análise, desempenho, auditoria, informações e acessibilidade/UI/UX antes da entrega. Foram corrigidos problemas confirmados na consulta da carteira e nos fluxos de interface. A política comercial, a ordenação, o dataset original e os recibos Jev foram preservados. Não houve instalação de dependências, nova inferência, deploy, commit ou submissão.

## Achados e mudanças

| Achado confirmado | Mudança | Evidência |
|---|---|---|
| A API decodificava toda a carteira filtrada antes de devolver 20 linhas; metadados também carregavam todas as oportunidades | Paginação e ordenação no PostgreSQL; agregação direta dos filtros. Contagens e página compartilham uma única fotografia transacional | Comparação de 600 combinações de perfil/filtro/fila/página e das 105 páginas da carteira com a implementação anterior; contratos HTTP iguais antes/depois |
| O histórico existia no banco, mas não era consultável na tela | Histórico sob demanda, com autor, versão, origem, modelo, data, assinatura da política e identificação do dataset | Teste de autorização, versões antigas, limite de 20 entradas e total explícito; leitura real na interface |
| Rascunhos de conta eram substituídos quando o detalhe era redesenhado | Preservação em memória por oportunidade e versão; indicação de alteração pendente; descarte explícito quando a versão muda; aviso antes de sair com rascunhos | Atualização e troca de oportunidade no navegador; conflito exercitado em banco isolado |
| Era possível acionar Salvar sem mudar a empresa, com mensagem que sugeria uma alteração | Salvar desabilitado enquanto não houver mudança | Navegador; gravação real isolada criou uma versão e desatualizou o resultado anterior |
| Busca concorrente deixava requisições antigas em execução; erros de inicialização podiam deixar a tela sem orientação | Cancelamento da consulta anterior; guarda de sessão; limpeza dos dados visuais ao trocar de perfil; erro de conexão legível; nova tentativa de inicialização | Troca de perfil, falha HTTP de inicialização e interrupção/reinício de servidor de teste |
| Textos secundários tinham pouco contraste e havia fontes de 8–10 px em partes importantes | Cores de texto mais escuras, tipografia maior, áreas de ação maiores e foco visível | Medição de contraste antes/depois e inspeção visual |
| Mudanças de lista e de detalhe não orientavam suficientemente navegação assistida | Atalho para o conteúdo, anúncio de carregamento/resultado, estado selecionado, foco no detalhe, manutenção do foco na fila e respeito à preferência de movimento reduzido | Ativação por Enter e inspeção dos estados de foco; regras de movimento reduzido no CSS e no código |
| Referência temporal e P90 precisavam de contexto | Data identificada como referência de cálculo; explicação do P90, ganhos/perdidos e referência global; preço de catálogo e setor no detalhe | Interface e fonte dos critérios já auditados |

O histórico limita a resposta aos 20 registros mais recentes de cada categoria, apresentando a contagem total. “Atual” compara a versão e a política de agora; “correspondia na gravação” preserva o contexto original. Não se apresentam metadados privados do provedor. O histórico não é uma trilha criptograficamente inviolável: um administrador do banco continua tendo controle sobre o armazenamento.

Rascunhos existem apenas na memória da aba e não são gravados automaticamente. Uma atualização completa do navegador ou saída pode descartá-los; há aviso quando existem alterações pendentes. A preservação de rascunho não substitui a gravação no servidor.

## Desempenho medido

Mesmo computador, banco e dados. Mistura fixa de seis consultas autenticadas: carteira inicial, página 50, cadastro/página 2, busca sem resultado, filtro de vendedor e metadados. Sem chamadas Jev ou escrita. Os resultados completos foram normalizados e comparados por SHA-256, preservando a semântica de linhas, contagens, páginas e metadados.

| Carga | Antes: p95 | Depois: p95 | Erros |
|---|---:|---:|---:|
| 1 cliente, 30 consultas | 38,0 ms | 23,1 ms | 0 / 0 |
| 35 clientes, 175 consultas | 315,9 ms | 58,0 ms | 0 / 0 |
| 100 clientes, 500 consultas | 816,3 ms | 46,1 ms | 0 / 0 |
| 100 clientes por 30 segundos | 853,1 ms | 114,9 ms | 0 / 0 |

Na janela de 30 segundos, foram concluídas 5.156 consultas antes e 41.583 depois. O p95 caiu 86,5%; a vazão observada passou de 168,9 para 1.383,4 consultas/s. A redução decorre de evitar transporte e decodificação de milhares de oportunidades em cada página; não foi introduzido cache que possa servir dados antigos.

Limites: uma execução por fase, teste local de circuito fechado (cada cliente aguarda sua resposta), mistura com buscas vazias, duração curta e 2.089 oportunidades. Aquecimento, agendamento e processos da máquina afetam as medidas. Não é SLA, previsão para uma multinacional, ensaio de saturação com chegada independente, teste de muitas horas ou dimensionamento de infraestrutura. Não mede capacidade de inferência do Jev.

Recibos: [antes](../app/evidence/performance-before.json), [depois](../app/evidence/performance-after.json). Executor: [benchmark-read.py](../app/scripts/benchmark-read.py). Para repetir o comparativo, capture `before` na versão anterior e `after` na versão atual, em cópias equivalentes. Executar as duas fases na versão atual mede apenas duas execuções dessa versão.

## Verificação funcional e auditoria

- Compilação TypeScript estrita e `go vet ./...` concluíram sem erro.
- `LEADDESK_INTEGRATION=1 go test ./... -count=1 -v` passou em PostgreSQL real separado: 14 testes principais, além dos subcasos de falhas HTTP. Inclui a política comparada aos 120 casos, deduplicação, leases, concorrência, permissões, mudança de política e os novos testes de paginação e auditoria.
- A nova paginação foi comparada à anterior em 600 combinações e em todas as 105 páginas; os filtros de metadados também respeitaram o perfil de vendedor.
- A auditoria foi verificada com uma resposta controlada de teste, mudança de versão, classificação histórica e mais de 20 versões. Essas respostas não são evidência de nova inferência do Jev.
- Na aplicação principal foram verificadas origem importada/ao vivo, foco de teclado, rascunho após atualizar e navegar, e bloqueio de gravação sem alteração.
- Uma cópia restaurada em banco temporário, servida em 8767 e sem credencial Jev, permitiu testar gravação pela interface, conflito com outro cliente, falha de conexão, recuperação, falha inicial da consulta, botão de nova tentativa, login inválido e troca para vendedor. O servidor e o banco temporários foram encerrados após a verificação.
- A aplicação principal foi reiniciada ao final e sua disponibilidade conferida. Não se atribui aos testes de interface qualquer nova classificação de IA.

Evidências: [testes Go](../app/evidence/polish-tests.txt), [gravação isolada](../app/evidence/polish-qa-save.json), [conflito](../app/evidence/polish-qa-conflict.json), [indisponibilidade](../app/evidence/polish-qa-unavailable.json), [recuperação inicial](../app/evidence/polish-qa-startup.json), [sessão de vendedor](../app/evidence/polish-qa-session.json).

## Acessibilidade e interface

O diagnóstico inicial do caso A7SA2L21 encontrou 47 amostras de texto abaixo do contraste adotado, entre 103 avaliadas. Depois, no mesmo caso com histórico aberto, 120 amostras passaram. Os conjuntos não são idênticos porque a interface ganhou conteúdo. Também foi inspecionada a carteira completa após os ajustes.

O cálculo usa cor do texto e fundo opaco ancestral, com mínimo de 4,5:1 para texto comum e 3:1 para texto grande. É uma verificação parcial: não cobre corretamente todas as composições de transparência, gradientes, imagens ou estados de interação. Não constitui auditoria completa ou certificação WCAG.

Foram inspecionadas larguras de 320, 390 e 1280 pixels. Não houve transbordamento horizontal da página; a tabela tem rolagem própria e pode receber foco. No teste estreito, seletor e botão de salvar tinham 44 px de altura. A configuração temporária de viewport foi restaurada. Não foi realizado teste com leitor de tela real, usuários com deficiência, Safari/Firefox ou certificação de zoom.

Evidências: [contraste anterior](../app/evidence/contrast-before.json), [contraste posterior](../app/evidence/contrast-after.json), [dimensões](../app/evidence/polish-responsive.json), [carteira](../app/evidence/polish-portfolio.png), [tela de 320 px](../app/evidence/polish-mobile-320.png) e [histórico em desktop](../app/evidence/polish-desktop.png).

## Limites que permanecem para a entrega

Não há comprovação de aumento de conversão ou contribuição decisória adicional do Jev frente às regras. A validação comercial depende de acesso futuro a vendedores e não bloqueia a submissão. SSO, alta disponibilidade, PITR, distribuição geográfica e detector de corridas Go com CGO continuam fora da validação local realizada.

Esta rodada oferece melhorias e evidências concretas dentro do escopo do desafio; não significa ausência absoluta de defeitos ou que o produto atingiu um teto universal de qualidade.

A [conferência final](../app/evidence/polish-final-check.json) confirmou os mesmos dados e classificações do backup verificado, escopo de acesso HTTP da auditoria, arquivos servidos iguais aos compilados e ausência das credenciais conhecidas em 60 arquivos de entrega examinados. O manifesto registra assinaturas SHA-256 das fontes e evidências principais.
