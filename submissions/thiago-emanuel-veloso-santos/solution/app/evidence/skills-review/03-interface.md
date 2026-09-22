# Revisão de interface

Aplicadas web-design-guidelines e as diretrizes atuais da Vercel aos arquivos `app/frontend/app.ts`, `app/frontend/recommendation.ts`, `app/static/index.html` e `app/static/style.css`. A leitura foi complementada por capturas e medições reproduzíveis em [design-probes.py](design-probes.py). Os resultados estão em [design-probes.json](design-probes.json).

## Observações que merecem ação

`app/static/style.css:44`: prioridade média. A mensagem no detalhe é ocultada no computador. Depois de avançar para a página 2, selecionar a primeira oportunidade e copiar seu resumo, a mensagem global fica acima da área visível. A medição encontrou topo em −44,33 px e borda inferior em 2,47 px, sem texto legível. A operação retorna ao estado normal sem confirmação visual junto ao botão. Ver [captura](desktop-feedback-viewport.png). Preservar uma confirmação visível perto da ação, mantendo identificação da oportunidade e evitando anúncios duplicados. O transporte do clipboard foi controlado; o posicionamento usa o HTML, CSS e JavaScript reais.

`app/frontend/app.ts:119`: melhoria de navegação. Busca, fila, filtros e página são enviados à API, mas não sincronizados com a URL. O filtro East deixa a URL em `/`; recarregar retorna ao filtro vazio. Não é possível compartilhar a mesma seleção ou recuperá-la pelo histórico do navegador. Ver as observações em browser-results.json. A implementação deve preservar o controle de acesso no servidor caso essa melhoria seja autorizada.

## Ajustes menores de aderência às diretrizes

`app/static/index.html:5` e `app/static/index.html:14`: campos sem atributo `name`; busca e filtros não definem `autocomplete`. Os controles têm nomes acessíveis por label ou aria-label, portanto esta observação não equivale a falta de rótulo acessível.

`app/frontend/app.ts:53`: seletor de empresa sem `name` e sem intenção de autocomplete explícita. O nome acessível Empresa vinculada está presente.

`app/static/style.css:33`: diálogo sem `overscroll-behavior: contain`. O bloqueio de rolagem no body já existe e não foi observado deslocamento indevido no teste; tratar como aderência adicional, sem alegar falha funcional confirmada.

## Cobertura e limites

| Área | Verificado |
|---|---|
| Semântica e acessibilidade | Botões nativos, labels, nomes dos botões, imagens com alt, regiões de status, títulos e link para pular ao conteúdo. |
| Teclado e foco | Abertura, 25 passos de Tab dentro do diálogo, ausência de foco totalmente coberto pelo cabeçalho nessa sequência, Escape e retorno à lista. |
| Formulários | Aviso de alterações pendentes, conflito, estado de salvamento e rascunho. Há ressalvas de metadados acima. |
| Movimento | Preferência de movimento reduzido respeitada; transição calculada de 0 s. |
| Conteúdo e layout | Lista vazia, IDs e nomes reais, medidas e limites da recomendação, imagens com dimensões, ausência de rolagem horizontal global em 320 px. |
| Desempenho da apresentação | Paginação de 20 registros; não há lista de milhares de elementos no DOM. Nenhum gargalo de renderização foi medido. |
| Navegação | Ressalva sobre URL e recarregamento registrada acima. |
| Localização | Público em português, moeda e números formatados em pt-BR. A data da base é uma data civil histórica, não um horário de evento. |
| Recursos não aplicáveis | Sem vídeo, áudio, arraste obrigatório, fontes externas ou hidratação por framework. O produto tem tema claro. |

Não foi feita certificação de acessibilidade, teste com leitor de tela, Safari/iOS ou medição exaustiva de contraste. As convenções editoriais inglesas de Title Case e uso de ampersand não foram impostas ao texto em português. Ausência de pequenos atributos opcionais não foi promovida a defeito bloqueante.

Fontes: [skill](https://raw.githubusercontent.com/vercel-labs/agent-skills/main/skills/web-design-guidelines/SKILL.md), [diretrizes](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md).
