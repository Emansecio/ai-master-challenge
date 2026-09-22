# Verificação final

Aplicada verification-before-completion. As conclusões abaixo se apoiam em comandos executados nesta rodada, não apenas em resultados anteriores ou no retorno de agentes.

| Verificação | Resultado | Evidência |
|---|---|---|
| TypeScript | Compilação concluída com saída 0, em diretório separado. Os dois módulos gerados são idênticos aos servidos. | [Saída](typescript-build.txt), [comparação](source-integrity.json) |
| Executável Go | Compilado com saída 0 em app/.local/skills-review/leaddesk-check.exe. | [Saída](go-build.txt); vazia, sem erro de compilação |
| Testes Go gerais | Saída 0. Core, serviço e módulo web aprovados. Os casos de banco dependentes da variável de integração foram ignorados nesta execução geral. | [Saída](go-tests.txt) |
| Testes PostgreSQL reais | Executados separadamente com LEADDESK_INTEGRATION=1: 16 testes principais e dois subcasos aprovados. | [Saída](postgres-tests.txt) |
| Análise go vet | Saída 0, sem diagnósticos. | [Saída](go-vet.txt); vazia, sem diagnóstico |
| Recomendações | 11 testes aprovados, nenhum ignorado, incluindo leitura das 2.089 oportunidades. | [Saída](recommendation-tests.txt) |
| Fluxos de navegador | 24 verificações aprovadas na etapa funcional. A etapa visual adicional identificou confirmação fora da área visível no computador. | [Resultados](browser-results.json), [medições visuais](design-probes.json) |
| Leitura concorrente | 705 solicitações medidas, nenhum erro ou mudança de contrato. | [Medições](read-performance.json) |
| Fontes da aplicação | 27 arquivos comparados com SHA-256 antes/depois, nenhum alterado. | [Comparação](source-integrity.json) |

A base principal manteve 2.089 oportunidades, 2.089 versões, 122 classificações, dois trabalhos e duas tentativas. Ao final, não havia banco com o prefixo temporário leaddesk_test_. Não houve consulta nova ao Jev. Os testes de navegador criaram e encerraram somente suas próprias sessões de autenticação.

Os arquivos gerados são relatórios, scripts de revisão, capturas, saídas de testes e recursos privados de apoio. Não houve correção na aplicação, alteração de documentação do produto, instalação global de skills, mudança de configuração persistente do banco, commit, publicação ou submissão.

## Limites

O workflow completo da primeira skill não foi executado. Foi usado o modo individual previsto por ela, em seis requisitos, com contrachecagem independente do achado documental. A rodada não certifica todas as afirmações de todos os documentos.

Não foram realizados instalação em máquina limpa, novo ensaio do modelo, avaliação com vendedores, auditoria exaustiva de acessibilidade ou teste de capacidade prolongado. Os testes de concorrência não cobrem todo entrelaçamento possível. O risco de aquisição adicional de conexão foi identificado no código, sem reproduzir saturação. O detector de corridas do Go não foi executado nesta rodada.

Fonte: [verification-before-completion](https://raw.githubusercontent.com/obra/superpowers/main/skills/verification-before-completion/SKILL.md).
