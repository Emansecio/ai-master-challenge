## REQ-04: instruções para executar a solução

> "**Setup:** Como rodar a solução (dependências, comandos, URL)"
>
> Fonte: ai-master-challenge/challenges/build-003-lead-scorer/README.md:L71

**Verdict:** implemented · confidence: high for documented setup and static agreement; clean installation not executed

**What this demands of an implementation:** disponibilizar dependências, sequência de preparação, comando de execução e endereço de acesso coerentes com a aplicação entregue. A verificação distingue a presença de instruções executáveis da comprovação de instalação em máquina limpa.

---

**Where enforcement lives:**

`app/README.md:L9-L26` especifica Windows, Go 1.26 ou superior, Node.js 22 ou superior, PowerShell 7, Docker Desktop com Linux, comandos de preparação e compilação, execução do servidor e URL `http://127.0.0.1:8766`. O README principal aponta para esse guia em `README.md:L52`.

```powershell
# app/README.md:L16-L21
cd app
./scripts/init-local.ps1
npm ci --ignore-scripts
npm run build
go run ./cmd/leaddesk -mode setup
go run ./cmd/leaddesk -port 8766
```

1. O script gera `.local/dev.env` somente se estiver ausente, com credenciais aleatórias de banco, e chama Compose com `up -d --wait` e verificação do código de saída (`app/scripts/init-local.ps1:L2-L16`).
2. Compose fixa a imagem PostgreSQL por versão e digest, publica somente `127.0.0.1:55432`, configura verificação de saúde e volume persistente (`app/compose.yaml:L4-L20`).
3. A versão mínima de Go está em `app/go.mod:L3`. `npm run build` chama `tsc -p tsconfig.json`, e TypeScript está fixado em 7.0.2 (`app/package.json:L5-L10`). `app/tsconfig.json:L3-L6` direciona `frontend/**/*.ts` para `static`. O lockfile também fixa TypeScript e o executável opcional Windows x64 (`app/package-lock.json:L335-L384`).
4. `main.run` carrega `.local/dev.env`, `.env` e `../analise/.env`; escolhe conexão administrativa para `setup`; lê política; aplica migração, dados e recibos; e inicia o servidor na porta pedida (`app/cmd/leaddesk/main.go:L24-L85`). Arquivos opcionais de ambiente ausentes não interrompem a execução, e variáveis já definidas têm precedência (`app/internal/config/config.go:L10-L29`).
5. O servidor usa `Static: "static"` e vínculo local `127.0.0.1` (`app/cmd/leaddesk/main.go:L85`); os arquivos são servidos conforme o mapa de rotas (`app/internal/web/api.go:L90-L98`).

---

**Paths walked:**

1. Novo ambiente Windows: dependências documentadas, `cd app`, criação de configuração local, Compose, instalação de dependência npm, compilação TypeScript, `setup` e `serve`, seguindo o bloco acima. A criação dos perfis e dos códigos locais está em `app/internal/store/store.go:L138-L154`; seu uso está explicado em `app/README.md:L26`.
2. Dados: o caminho padrão e a opção `-data` são documentados em `app/README.md:L40-L45` e coincidem com `app/cmd/leaddesk/main.go:L26`. O ZIP é obrigatório e tem sua assinatura conferida em `app/internal/core/dataset.go:L23-L29`. O arquivo foi localizado no caminho esperado; a assinatura lida nesta verificação coincide com `DatasetSHA` em `app/internal/core/core.go:L14`.
3. Recibos: `setup` tenta importar `../analise/resultados/jev-vercel-v02` (`app/cmd/leaddesk/main.go:L64`). A ausência do manifesto permite continuar sem recibos (`app/internal/store/receipts.go:L16-L19`). Quando existe, o importador confere data de revalidação, modelo, assinatura da política, estado, validação da resposta e versão antes de inserir (`L31-L76`). Os dois arquivos necessários estão presentes; modelo, data e assinatura do manifesto correspondem aos valores usados pelo programa. O guia descreve a importação condicionada em `app/README.md:L54`.
4. Uso sem chave Jev: a configuração é opcional e documentada em `app/README.md:L5`, `L52-L54`. O programa define `KeyConfigured` conforme a presença da chave (`app/cmd/leaddesk/main.go:L81-L85`), e a interface desabilita o botão da chamada quando ausente (`app/frontend/app.ts:L138`). Não é necessária chave externa para abrir a carteira e consultar a política local.
5. Reexecução: o bootstrap preserva o arquivo de credenciais existente (`app/scripts/init-local.ps1:L6-L11`), a carga usa conflitos sem sobrescrita dos dados importados (`app/internal/store/store.go:L117-L135`) e o servidor exige política já configurada e compatível (`app/cmd/leaddesk/main.go:L74-L79`). Não executei esse caminho contra a instalação principal.

---

**Searched:**

1. `Setup|Como rodar` no enunciado localizou o requisito em `README.md:L71`.
2. `bootstrap|\.zip|receipts|policy|LEAD|DATABASE|8766|node|npm|go ` em scripts, entrypoint e guia localizou os comandos, caminhos, variáveis e porta; seus destinos foram lidos.
3. `rg --files app/scripts app/cmd` e `rg --files app/internal` localizaram bootstrap, main, config e importador de recibos. Os arquivos foram lidos com numeração de linhas.
4. `Get-Item` confirmou ZIP (145.926 bytes), chamadas preservadas (287.229 bytes), manifesto (791 bytes), HTML, CSS, logo e `go.sum`. Não li credenciais reais.
5. `Get-FileHash` confirmou SHA-256 do ZIP: `74d535826330b616758ebb6bb393abf701a5126364a72fbe71003cb6a7a87a9c`. A assinatura da política e a do manifesto coincidem: `01c8ce8e99b4f57cf6b2bc4c859a94756dd726e17dfbd32f21e51c77d38e05bd`.
6. `Get-Command` localizou Go, Node, npm, PowerShell e Docker neste computador. Comandos de versão retornaram Go 1.27.0, Node v26.9.0 e Docker Compose v5.5.1. Isso apenas confirma disponibilidade local, não substitui execução do procedimento completo.

---

**How the verdict was reached:** o guia cobre dependências, comandos, preparação de dados, códigos de acesso, configuração opcional do modelo e URL. Os caminhos e opções correspondem aos arquivos e à implementação. Não foi confirmado um impedimento de setup dentro do procedimento Windows documentado.

**Open questions / limits:** instalação limpa, download de dependências e inicialização de banco novo não foram executados neste requisito. O agente principal fará build e testes locais separadamente. O procedimento depende de ferramentas instaladas, acesso aos registros de pacotes/imagem e porta de banco disponível; não foi inspecionado o ambiente de outro avaliador. A entrega final ainda precisa incluir o ZIP, fontes, lockfile, política e arquivos estáticos que estão presentes neste workspace; a inclusão num pacote ou repositório submetido não foi verificada, pois não houve submissão. Não houve mudança no código, instalação de ferramenta, chamada ao Jev ou execução de setup na base principal.
