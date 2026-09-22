# Evolução da interface do Lead Desk

Este documento registra as rodadas de apresentação visual. A paleta da primeira rodada foi ajustada depois à logo G4, conforme a seção Identidade G4. As últimas correções de navegação e cadastro estão no [relatório da revisão](CORRECOES-REVISAO-LEAD-DESK.md).

## Primeira rodada

Aplicação da skill [frontend-design](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md), consultada em 22/09/2026. Público: vendedores e gestores que precisam selecionar uma oportunidade, entender os motivos e conferir o próximo passo.

Problemas observados na interface de 1280 × 900: a carteira começa a 726 px do topo; avisos competem com o trabalho; a navegação lateral ocupa espaço apesar de conter uma única área. No organização visual estreito, o detalhe aparece depois da lista inteira.

## Organização visual da primeira rodada

Tinta 
`#172B40`; superfície `#FFFFFF`; fundo `#F3F6F8`; ação azul `#2456C7`; texto secundário `#526579`; atenção `#86500B`.
Tipografia: Segoe UI, com alternativas locais. Títulos de 28 px; conteúdo de 14 px; apoio de 12 a 13 px. Números tabulares para comparação. Sem downloads de fontes.

Estrutura: barra de identidade horizontal; título e contexto compacto; resumo em uma faixa; filtros e filas; carteira e detalhe lado a lado. Alinhamento à esquerda; valores à direita.

Destaque principal: a lista de trabalho. Cores de estado ajudam a diferenciar ações, sempre acompanhadas por texto. O painel explica a decisão antes de expor os dados complementares.


```text
Identidade / Carteira                         Usuário / Sair
Título + contexto histórico                         Atualizar
Resumo da seleção em quatro colunas
Busca / Vendedor / Gestor / Região / Limpar
Qualidade do cadastro + filas
Lista de oportunidades                 Motivo + roteiro de ação
```

Em telas estreitas: resumo recolhível e filtros de equipe expansíveis, com contagem de filtros ativos; lista em formato de cartões com os mesmos dados e ordem; seleção abre um diálogo nativo com fechamento por botão ou Escape e retorno ao item de origem. Nenhuma consulta ao Jev é disparada pela navegação.

Revisão do plano: removidos os quatro cartões isolados e a navegação lateral sem alternativas. Mantidos os números porque representam filas reais, não decoração. Mantidas limitações do histórico, origem das orientações e auditoria. Sem alterar política, classificação, persistência ou contratos da API.

## Validação

Compilação TypeScript concluída. Verificados no navegador integrado: filtros de equipe, busca vazia e recuperação, paginação com foco no início da lista, detalhes em diálogo, Escape, fechamento pelo botão, retorno ao item original, limite de foco do diálogo, mudança de largura, rascunho de conta ao trocar de oportunidade, acesso ao histórico, persistência das seções abertas após atualização, abertura dos critérios e saída/entrada local.

Larguras 320, 390, 768, 1024 e 1280 px: nenhuma rolagem horizontal na página ou na lista nos estados medidos. A carteira começa a 547 px do topo no desktop de 1280 × 900, ante 726 px anteriormente (179 px acima). No celular de 390 px, começa a 642 px com resumo e filtros de equipe recolhidos. Esse resultado mede organização da tela, não produtividade comercial.

Amostragem de 26 combinações de cor/fundo de texto sem falhas de contraste calculado. Controles desabilitados não entram nessa amostra. Não equivale a uma certificação WCAG nem substitui avaliação com leitor de tela e usuários.

Seis contratos de leitura da API idênticos aos da rodada anterior. Contagens mantidas: 2.089 oportunidades, 2.089 versões, 122 classificações e dois jobs. Os testes desta rodada não salvaram contas nem solicitaram classificações. Nenhuma nova dependência, fonte externa ou mudança de servidor.

Evidências: `app/evidence/design-validation.json`, `app/evidence/design-contracts.json`, `design-before.png`, `design-desktop.png`, `design-mobile.png` e `design-detail-320.png`.


## Identidade G4

Logo fornecida pelo usuário incorporada sem edição, preservando transparência e proporção 560 × 221. Cabeçalho claro e identificação Lead Desk; tela de acesso com fundo azul-marinho. Paleta alinhada à imagem: azul-marinho `#001F35` e dourado `#B9915B`, com dourado escuro `#77582F` em indicadores que exigem maior contraste. Cores das categorias comerciais preservadas. PNG servido por uma rota estática explícita, sem dependências externas. Verificação visual em desktop e celular; capturas em `app/evidence/brand-desktop.png`, `brand-mobile.png` e `brand-login.png`.

## Ajustes posteriores no fluxo de trabalho

Na revisão seguinte, o formulário de vínculo de empresa passou para o início do detalhe na fila Cadastro. A interface também recebeu o resumo copiável para conferência no CRM, mensagens associadas à oportunidade correta e preservação do foco durante atualizações. Os fatos, os alertas simultâneos e o histórico permanecem acessíveis. A verificação em tela de 320 px e as capturas estão no [relatório das correções](CORRECOES-REVISAO-LEAD-DESK.md).
