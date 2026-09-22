# Ensaio do Router publico contra a politica de qualificacao

Data: 22/09/2026. Execucao real local, com os mesmos 120 casos usados no Jev.

**A configuracao testada nao manteve os resultados do Jev. Nas 60 oportunidades reservadas para avaliacao, o Router acertou as duas classificacoes em 23 (38,3%); o Jev havia acertado as duas em 60 (100%).**

## Implementacao executada

- Codigo: [eletroswing/router](https://github.com/eletroswing/router/tree/ca4a967fa3632a2faed8cbd9721fe419cf8b207e), commit `ca4a967fa3632a2faed8cbd9721fe419cf8b207e`.
- Caminho oficial de CPU do repositorio, usando `Lfm2Router.fromFile` e `route`, sem modificar o codigo de inferencia.
- Pesos: `kucukkanat/LFM2.5-Encoder-350M-Prompt-Router-ONNX`, revisao `d5f69da4b475ee0edcba2caf12f5a724aa8cab5a`, arquivo `onnx/model_quantized.onnx`, com 356.839.915 bytes.
- Modelo de 350 milhoes de parametros. Nao e a versao ternaria de 3 milhoes mostrada nas imagens, nem a variante podada/fp16 preparada pelo projeto para CUDA. E o modelo quantizado que o caminho CPU publico utiliza quando a variante local otimizada nao existe.
- Windows x64, Intel Core i7-14700K, seis threads de inferencia, Node 26.9.0, tokenizers 0.23.2, binding nativo ONNX Runtime fornecido pelo repositorio.
- A maquina possui GPU AMD Radeon RX 6900 XT; a execucao foi em CPU. O benchmark NVIDIA/CUDA divulgado pelo autor nao foi reproduzido.

Os artefatos foram baixados de uma revisao fixa e seus hashes foram registrados. A dependencia de tokenizacao foi instalada somente na copia local do Router, com scripts de instalacao desativados. Nao houve treinamento, chamada de inferencia externa, uso de chave de API ou deploy.

## Compatibilidade e adaptacao

O Router aceita no maximo 128 tokens para texto e categorias juntos. Ao converter as instrucoes, os fatos e as descricoes de categorias originais do Jev para essa interface, as 240 entradas exigiram entre 323 e 357 tokens. Todas foram rejeitadas pelo proprio `buildInputs`, antes da inferencia. Isso e uma incompatibilidade de entrada, nao uma medida de acuracia.

Para executar a comparacao, foi usada uma unica adaptacao compacta em ingles, com 73 a 94 tokens. Preservaram-se os fatos relevantes para as regras dos casos validos: conta identificada, estagio, idade, referencia historica e indicador de idade acima da referencia. As categorias descrevem as condicoes e a acao correspondente, incluindo revisao humana. Produto, preco e outros campos que nao alteram essas regras foram omitidos. As frases exatas estao em `manifesto.json` e nos recibos.

Cada oportunidade exigiu duas chamadas locais: uma para qualificacao e outra para proxima acao. As respostas esperadas e a particao da amostra nunca entram em `route`; servem somente a avaliacao posterior. Nao houve correcao deterministica das respostas, limiar de confianca, cache de resultados ou ajuste depois de observar os erros. A configuracao e o script foram congelados antes do desenvolvimento e permaneceram iguais na avaliacao.

Logo, este e um teste da mesma politica nos mesmos registros, com uma representacao adaptada a outra interface. Nao e uma comparacao de prompts literalmente identicos, nem uma busca exaustiva pela melhor configuracao possivel do Router.

## Acertos observados

| Medida | Desenvolvimento: Router | Avaliacao: Router | Avaliacao anterior: Jev |
|---|---:|---:|---:|
| Oportunidades | 60 | 60 | 60 |
| Qualificacao correta | 30/60 (50%) | 30/60 (50%) | 60/60 (100%) |
| Proxima acao correta | 25/60 (41,7%) | 24/60 (40%) | 60/60 (100%) |
| Duas respostas corretas na mesma oportunidade | 25/60 (41,7%) | 23/60 (38,3%) | 60/60 (100%) |

No total dos 120 casos, foram 60 qualificacoes corretas, 49 proximas acoes corretas e 48 oportunidades com ambas corretas (40%). Todas as 240 inferencias de negocio retornaram saidas validas. Cada fase tambem executou um teste simples de sanidade com um comando de timer; ambos passaram. Sao 242 inferencias locais ao todo, das quais 240 compoem a comparacao de negocio.

| Estrato da avaliacao | Ambas corretas |
|---|---:|
| Engaging, sem conta, idade dentro da referencia | 0/10 |
| Engaging, sem conta, idade acima da referencia | 0/10 |
| Engaging, com conta, idade dentro da referencia | 5/10 |
| Engaging, com conta, idade acima da referencia | 8/10 |
| Prospecting, sem conta | 0/10 |
| Prospecting, com conta | 10/10 |

A falha predominante foi desrespeitar a precedencia da conta ausente. Nas 30 oportunidades sem conta da avaliacao, todas as qualificacoes ficaram incorretas: o modelo escolheu a classe correspondente ao estagio. Em 29 dessas 30 oportunidades, a proxima acao tambem nao foi identificar a empresa.

Exemplo real: `SMP2K39G`, Engaging, sem conta, idade de 94 dias e referencia de 102. Esperado: `incomplete_profile` e `identify_account`. Obtido: `negotiation_reviewable` e `continue_negotiation_review`. A primeira decisao incorreta recebeu probabilidade de aproximadamente 0,703. Essa probabilidade nao constitui garantia de acerto.

Nenhuma resposta escolheu `human_review`. Os casos sao validos e essa classe nao era esperada; portanto, a ausencia de escolhas nao valida a capacidade de abster-se diante de entradas contraditorias ou desconhecidas. Esse comportamento exigiria outro conjunto de testes.

## Desempenho e custo

| Medida por oportunidade, para as duas classificacoes | Router: desenvolvimento | Router: avaliacao | Jev: avaliacao anterior |
|---|---:|---:|---:|
| Mediana | 90 ms | 220 ms | 405 ms |
| Percentil 95 | 96 ms | 226 ms | 584 ms |

O Router mede duas inferencias sequenciais locais, incluindo tokenizacao, pooling e selecao de categorias. O Jev mede uma requisicao HTTP que responde as duas perguntas, incluindo rede/TLS. Os ensaios ocorreram em momentos diferentes e nao isolam a velocidade interna dos modelos. A diferenca entre desenvolvimento e avaliacao do Router mostra variacao de tempo mesmo na mesma maquina; sua causa nao foi isolada. Nao cabe atribuir um fator universal de aceleracao a esses numeros.

Inicializar o modelo levou aproximadamente 655 ms no desenvolvimento e 608 ms na avaliacao. Download e inicializacao ficam fora da latencia por oportunidade. O maior RSS observado depois de uma oportunidade foi de aproximadamente 491 MB, incluindo processo e runtime; nao e uma medicao do pico global de memoria.

Nao houve tarifa de API de inferencia no teste local. Energia, hardware e manutencao nao foram contabilizados. O Jev tambem havia reportado custo efetivo zero nos 120 casos; seu `marketCost` somado foi US$ 0,00486381, como referencia do Gateway, nao como cobranca observada.

## Conclusao e limites

Esta configuracao do Router ficou mais rapida no tempo observado pelo cliente, mas perdeu aderencia a regras essenciais. Nao sustenta substituir o Jev mantendo a qualidade obtida no ensaio anterior. Isso nao prova que o Router seja incapaz de melhorar com outra representacao ou treinamento; esses experimentos nao foram realizados.

Os acertos medem aderencia a uma politica proposta, cujo oraculo e deterministico. Nenhum dos resultados demonstra aumento de conversao comercial. Os 120 registros cobrem seis estratos de regras; nao sao 120 condicoes logicas distintas nem uma avaliacao ampla de raciocinio comercial. O ensaio tambem nao mede a versao ternaria das imagens ou a variante otimizada para GPU.

## Evidencias e verificacao

- [Manifesto: modelo, hashes, maquina e categorias](resultados/router-local-v01/manifesto.json).
- [Compatibilidade de tokens](resultados/router-local-v01/preflight.json).
- [Recibos do desenvolvimento](resultados/router-local-v01/development.jsonl) e [recibos da avaliacao](resultados/router-local-v01/evaluation.jsonl).
- [Verificacao independente e matrizes de confusao](resultados/router-local-v01/verificacao.json).
- [Script de download fixado](baixar_router.py), [executor](testar_router_local.mjs) e [verificador](verificar_router.py).
- [Ensaio anterior do Jev](RESULTADO-JEV-VERCEL.md).

O verificador confirmou os 120 IDs sem duplicacao, as particoes 60/60, os hashes dos dados/script/configuracao/pesos, a reconstrucao dos requests a partir dos fatos sem respostas esperadas, o mapeamento das probabilidades para as classes e as contagens publicadas. Ele roda localmente, sem repetir inferencias: `python analise/verificar_router.py`.


## Reprodução do experimento opcional

Os recibos e scripts desse experimento acompanham a entrega. O código externo do Router, suas dependências e os pesos não acompanham o pacote, pois não são usados pela aplicação final. Para repetir a verificação completa do Router, é necessário recuperar esses artefatos conforme as revisões e assinaturas registradas no manifesto e no script de download. Esse passo é independente da instalação do Lead Desk.
