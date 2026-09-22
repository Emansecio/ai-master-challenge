## REQ-06 — Documentar limites e condições para escalar

> "**Limitações:** O que a solução não faz e o que precisaria pra escalar"
> Fonte: ai-master-challenge/challenges/build-003-lead-scorer/README.md:L73, Documentação mínima.

**Verdict:** implemented · confidence: high.

---

**What this demands of an implementation:** disponibilizar documentação acessível que identifique capacidades ausentes e condições ainda necessárias para uma operação maior. O requisito pede explicação dos limites; não obriga a implementar autenticação corporativa, alta disponibilidade ou outra proposta de evolução nesta entrega.

---

**Where enforcement lives:**

Para este requisito, a entrega é a documentação. O README principal apresenta o caráter histórico dos dados (README.md:L5), diferencia uma cópia de resumo de um registro real de atendimento (L13), informa que a prioridade ainda não demonstrou benefício comercial (L25, L33) e separa estado atual de uso corporativo e submissão (L39-L46). Os caminhos para o guia e a arquitetura estão em L52-L54. Campos comerciais ausentes e limites de interpretação estão em L61-L65.

O guia da aplicação descreve concretamente o que falta:

1. Acesso limitado à própria máquina, HTTP local e três perfis de demonstração, sem autenticação corporativa, autenticação em duas etapas, provisionamento ou separação entre organizações (app/README.md:L28, L155-L157).
2. Banco único e ausência de capacidade demonstrada para produção, alta disponibilidade ou operação entre regiões. Recuperação para um instante específico, cópia externa, agendamento e metas de recuperação permanecem pendentes (app/README.md:L159).
3. Carga do Jev conservadora, eventual repetição de chamada após interrupção e ausência de garantia de gratuidade futura (app/README.md:L56, L95-L105).
4. Versão interna do modelo não identificada pelo nome público e necessidade de revalidação (app/README.md:L109-L116).
5. Alterações não salvas limitadas à memória da aba, ausência de escrita automática no CRM de origem e auditoria exibindo até 20 registros por grupo (app/README.md:L66, L71, L89).
6. Limites de validação: desempenho local não representa garantia de produção, revisão de casos não substitui julgamento independente de vendedores e acessibilidade foi verificada parcialmente (app/README.md:L147, L153, L161).

A arquitetura complementa o que precisa ser definido para escalar: carga simultânea e metas de resposta desconhecidas (STACK-ARQUITETURA.md:L9), decisões de hospedagem, banco, autenticação e isolamento (L85-L87), tolerância a perda de dados e indisponibilidade (L89), além da necessidade de testar controles no ambiente efetivo (L91). A tabela de L66-L73 separa implementação atual de limite. Nenhuma dessas condições é apresentada como já resolvida.

Conferência de fatos pertinentes no código:

```go
// app/cmd/leaddesk/main.go:L82-L85
for i := 0; i < 2; i++ {
    go service.Work(ctx, s, service.Client{Key: key}, 2*time.Second)
}
api := web.API{Store: s, KeyConfigured: key != "", Static: "static", Host: fmt.Sprintf("127.0.0.1:%d", *port)}
```

O serviço inicia dois trabalhadores e usa endereço local, conforme os limites documentados. O limite global no banco rejeita nova reserva quando já há duas em execução (app/internal/store/jobs.go:L107-L112); cada reserva dura 45 segundos (L121), e o cliente usa 30 segundos por chamada (app/internal/service/worker.go:L49, L86). A consulta externa antecede a gravação local (worker.go:L85-L102), sustentando a ressalva de que uma interrupção nessa janela pode exigir repetição.

A instalação Compose contém um serviço de banco, uma porta local e um volume persistente (app/compose.yaml:L1-L20). A preparação cria três usuários locais (app/internal/store/store.go:L142-L155), e a autenticação consulta suas assinaturas e sessões locais (L162-L173). O esquema contém usuários, escopos e sessões, sem entidade de organização independente (app/internal/store/schema.sql:L1-L26). O script de backup executa cópia lógica e restauração em banco separado, comparando registros; seu próprio relatório explicita que não comprova recuperação para um instante específico nem alta disponibilidade (app/scripts/backup-verify.ps1:L14-L33).

---

**Paths walked:**

1. Entrada do avaliador: README principal apresenta limites e liga diretamente ao guia da aplicação e à arquitetura (README.md:L25-L54, L61-L65).
2. Leitor operacional: guia identifica funcionamento local, interpretação da recomendação e restrições de instalação (app/README.md:L28, L79-L87, L155-L161).
3. Leitor responsável por escala: arquitetura identifica perguntas ainda abertas de carga, autenticação, isolamento, disponibilidade e recuperação (STACK-ARQUITETURA.md:L9, L62-L73, L85-L91).
4. Correspondência com implementação: ponto de entrada, autenticação local, configuração do banco, limites da fila e script de cópia lógica foram lidos nos trechos citados; não se encontrou promessa documental incompatível nesses aspectos.

---

**Searched:**

1. `Limita|limita|escala|produç|não |ainda|Postgre|cache|concorr|autent|backup|Vercel|tenant|SSO|redis` nos três documentos: encontrados limites de dados, de avaliação, da integração, da operação local e decisões de produção; os trechos relevantes estão citados acima.
2. `127.0.0.1|ListenAndServe|worker|MaxConns|SameSite|HttpOnly|45` em `app/cmd`, `app/internal` e Compose: encontrados o endereço local, limites dos trabalhadores, sessões e reserva do processamento.
3. `create policy|row level security|oidc|saml|oauth|tenant|wal_level|archive_command|cron` em `app/internal`, `app/cmd`, Compose e script de backup: zero ocorrências. Isso foi usado apenas como conferência limitada das ausências explicitamente documentadas, juntamente com leitura do esquema, autenticação e script; não constitui auditoria de segurança ou inventário de infraestrutura externa.
4. Leitura integral do README principal, da arquitetura, do esquema de banco e do script de backup, além das seções de limites e respectivas referências no guia da aplicação.

---

**How the verdict was reached:** as duas partes da exigência estão cobertas: o que a solução não faz e o que precisa ser definido e validado para escalar. A documentação não promete capacidade corporativa a partir de um teste local, nem confunde concordância com regras com resultado comercial. As limitações examinadas correspondem à implementação. Não há lacuna confirmada para corrigir neste requisito documental.

Validação desta rodada em 22/09/2026: leitura e confronto estático das fontes citadas. Não foram executados comandos de backup, testes de carga, chamadas ao Jev ou alterações de configuração. Nenhum código, documento do produto ou dado comercial foi alterado.

---

**Open questions:**

1. Carga real, metas de disponibilidade e de recuperação e condições de autenticação dependem de definições externas. Estão explicitamente documentadas como pendentes e não são falhas de implementação deste requisito.
2. Esta análise não reexecuta as evidências históricas citadas pela documentação. Sua existência não autoriza concluir que todo resultado anterior foi reproduzido nesta rodada.
3. A avaliação de qualidade comercial e de compreensão por vendedores permanece necessária para demonstrar benefício, conforme a própria documentação; isso não invalida a presença da seção de limitações.
