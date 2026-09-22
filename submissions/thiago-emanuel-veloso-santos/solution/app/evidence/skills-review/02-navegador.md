# Testes de navegador

A skill webapp-testing foi aplicada com Python Playwright. O servidor existente estava ativo na porta 8766. Primeiro foram inspecionados o DOM e a captura da aplicação carregada; depois foram definidos os seletores e executados os fluxos.

O Chromium distribuído pelo Playwright não estava instalado. Foi utilizado o Microsoft Edge Chromium 153.0.4234.48 já disponível, em modo sem janela. Não foi instalado navegador novo.

[browser-results.json](browser-results.json) registra 24 verificações aprovadas. [browser-tests.py](browser-tests.py) reproduz o conjunto a partir do workspace com servidor ativo. O script não imprime códigos de acesso.

Na aplicação real foram exercitados acesso válido e inválido, perfis de administrador, gestor e vendedor, paginação, busca sem resultados, limpeza, filtro regional, cadastro, resumo, histórico, largura de 320 px, foco no diálogo e saída. As únicas escritas permitidas são criação e encerramento das próprias sessões de autenticação.

Rascunhos, salvamento atrasado, conflito de edição e clipboard usam um contexto separado cujas requisições de API são todas respondidas pelo teste. Essas respostas controladas verificam a interface e não comprovam gravação real no banco. A integração de banco será verificada separadamente. Nenhuma classificação real foi solicitada.

Não ocorreram erros JavaScript não tratados nem tentativas de escrita comercial no contexto real. A observação de perda do filtro ao recarregar foi registrada e encaminhada à revisão de interface.

As verificações de mensagem desta etapa confirmam conteúdo e associação à oportunidade. A revisão visual seguinte mede também se a mensagem fica na área visível, uma propriedade diferente.

Fonte: [webapp-testing](https://raw.githubusercontent.com/anthropics/skills/main/skills/webapp-testing/SKILL.md).
