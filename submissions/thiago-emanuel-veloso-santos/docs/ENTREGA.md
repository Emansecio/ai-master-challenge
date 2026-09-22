# Conferência da entrega

Preparação realizada em 22/09/2026. A entrega está em `submissions/thiago-emanuel-veloso-santos/`. O README segue as seções do template oficial, inclui meu nome e LinkedIn e aponta para solução, processo e evidências.

## Instruções conferidas

Foram lidos novamente o README principal, o desafio 003, o guia de submissão, o template e o CONTRIBUTING do repositório oficial. O conteúdo remoto dos cinco documentos corresponde às cópias locais. As URLs e assinaturas estão em [instruções conferidas](instrucoes-conferidas.json).

O desafio exige software funcional, dados reais, priorização além do valor, explicação da prioridade, instruções de execução, limitações e registro do uso de IA. As revisões anteriores conferiram esses requisitos. A organização desta etapa atende à exigência de manter todos os arquivos de entrega dentro da pasta do candidato, preservando os arquivos originais do desafio.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `README.md` | Apresentação no formato de submissão. |
| `solution/app` | Aplicação, testes e evidências das revisões. |
| `solution/analise` | Análises, dataset, scripts e recibos dos experimentos. |
| `process-log/README.md` | Índice do processo e das minhas intervenções. |
| `docs` | Conferência das instruções, da instalação e dos arquivos de entrega. |

A estrutura interna de `solution` preserva os caminhos relativos esperados pelo código. Os resultados antigos permanecem datados para permitir a conferência do processo. O protótipo Python substituído pelo servidor Go não acompanha a entrega.

O arquivo `.gitattributes` mantém os bytes dos arquivos ao copiar a entrega pelo Git. Isso evita que a conversão automática de quebras de linha altere as assinaturas usadas para validar a política e os recibos do ensaio.

## Instalação em base vazia

A cópia da submissão foi testada com configuração e credenciais novas, sem chave do Jev e com um volume PostgreSQL novo. Foram executados o script `init-local.ps1`, `npm ci --ignore-scripts`, `npm run build`, o setup da aplicação, os testes Go com integração, `go vet` e a compilação do servidor.

Para preservar a instalação original, somente no ensaio foram usados o projeto Compose `g4-leaddesk-submission-check`, a porta 55433 para o banco e a porta 8767 para a aplicação. A configuração de teste antecipou as credenciais novas e aplicou uma sobreposição de portas ao Compose. O guia entregue mantém as portas padrão 55432 e 8766. Go, Node, PowerShell, Docker, navegador e a imagem PostgreSQL já estavam disponíveis no computador; a verificação não representa a instalação dessas ferramentas em outro Windows.

O setup importou 2.089 oportunidades abertas e 120 classificações do ensaio, sem criar trabalhos de inferência. As regras locais ficaram disponíveis sem credencial externa. Passaram os testes Go com PostgreSQL, 25 verificações de interface e 11 testes de recomendações, incluindo a leitura das 2.089 oportunidades.

A primeira execução do navegador parou por timeout ao abrir o resumo, depois de 12 verificações aprovadas. A inspeção isolada encontrou o resumo disponível e nenhum erro JavaScript. Uma repetição integral com diagnóstico passou as 25 verificações. A causa do timeout não foi determinada; a ocorrência permanece registrada nos resultados.

Evidências: [resultado da instalação](instalacao/resultado.json), [testes Go](testes-instalacao-go.txt), [interface](instalacao/ui-results.json), [recomendações](instalacao/recommendation-tests.txt), [computador](instalacao/desktop-copy-feedback.png) e [celular](instalacao/mobile-copy-feedback.png).

## Arquivos privados e limpeza

O pacote contém código, documentação, dados públicos e evidências. Ficaram fora dele `.env`, códigos de acesso, bancos locais, cópias de segurança privadas, executáveis, dependências instaladas, caches Python, código externo e pesos do Router. Cerca de 674 MiB de arquivos da área de desenvolvimento não foram copiados. Os scripts e recibos do experimento Router foram mantidos; a repetição desse experimento opcional exige recuperar suas dependências.

Os arquivos privados criados no teste de instalação foram transferidos para a área privada do ambiente de desenvolvimento, fora do repositório. O servidor de teste e seu contêiner foram parados. O volume de teste foi preservado. A aplicação original e sua base continuam disponíveis.

Removi manualmente os caches Python, os pesos e as dependências instaladas do Router, o protótipo Python substituído e cinco executáveis antigos. A conferência posterior confirmou a remoção desses itens e a preservação do executável em uso e da pasta de entrega.

## Preparação do Git

O `.gitignore` original do desafio ignora `submissions/`. Esse arquivo foi preservado, pois as regras permitem alterações somente na pasta do candidato. A [lista de arquivos](arquivos-entrega.txt) relaciona os caminhos aprovados para inclusão explícita no Git. Ela não inclui arquivos privados gerados ao executar a aplicação.

Depois de configurar o fork e criar a branch `submission/thiago-emanuel-veloso-santos`, a inclusão pode ser feita a partir da raiz do repositório:

```powershell
git --literal-pathspecs add --force --pathspec-from-file=submissions/thiago-emanuel-veloso-santos/docs/arquivos-entrega.txt
git diff --cached --stat
git diff --cached --name-only
```

Todos os caminhos exibidos devem começar com `submissions/thiago-emanuel-veloso-santos/`. Se o pacote for alterado depois desta preparação, a lista e a conferência dos arquivos precisam ser atualizadas antes da inclusão. Não use inclusão forçada recursiva de toda a pasta após executar a aplicação, pois isso também pode incluir arquivos privados ignorados.

Fork, criação de branch de submissão, commit, push e Pull Request ainda não foram realizados. O título previsto é `[Submission] Thiago Emanuel Veloso Santos — Challenge 003`.

### Texto previsto para o Pull Request

Submissão de Thiago Emanuel Veloso Santos para o Challenge 003, Lead Scorer.

O Lead Desk organiza as 2.089 oportunidades abertas do dataset em filas de trabalho, explica os critérios de prioridade e apresenta perguntas para orientar o atendimento. A entrega inclui código, dados, instruções de execução, registro do processo e evidências dos testes.

A instalação foi conferida com banco vazio e sem chave de inferência. A documentação registra as limitações dos dados históricos e a necessidade de validar a utilidade comercial com vendedores.
