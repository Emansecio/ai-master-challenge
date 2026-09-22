# Arquitetura do Lead Desk

Atualizado em 22/09/2026. A aplicação local está implementada com Go, TypeScript e PostgreSQL. Este documento explica as escolhas técnicas, os controles existentes e o que ainda precisa ser definido para uso corporativo.

## O problema que orientou as escolhas

O desafio descreve 35 vendedores e aproximadamente 8.800 oportunidades. A solução precisa permitir consultas simultâneas, preservar alterações e explicar os motivos de cada orientação. Consultar o Jev não deve impedir o vendedor de continuar usando a carteira.

O número de pessoas que usarão o sistema ao mesmo tempo, a frequência de atualização e as metas de resposta em produção ainda são desconhecidos. O porte da empresa, por si só, não fornece essa estimativa.

## Tecnologias escolhidas

| Parte da aplicação | Escolha | Motivo |
|---|---|---|
| Servidor | Go | Reúne regras, rotas de acesso e processamento concorrente com limites definidos. |
| Interface | TypeScript sem framework | Apresenta carteira, filtros, explicações, formulários e estados do processamento. |
| Banco | PostgreSQL | Guarda oportunidades, versões, classificações, sessões e fila no mesmo sistema de transações. |
| Classificador | Jev pelo Vercel AI Gateway | Mantém a integração testada para aplicar os critérios de qualificação e próxima ação. |
| Reutilização de respostas | Classificações versionadas no PostgreSQL | Permite reaproveitar somente resultados que ainda correspondem aos dados e critérios atuais. |
| Organização do código | Um serviço dividido por responsabilidade | Mantém as partes do sistema identificáveis, sem exigir serviços independentes nesta etapa. |

Ruby/Rails e Rust foram considerados. A escolha de Go buscou equilibrar concorrência, manutenção e execução do servidor. Não houve comparação de desempenho entre essas linguagens.

Um banco separado para cache, como Redis, ficou adiado. A implementação atual reutiliza classificações no PostgreSQL, evitando outro componente que precisaria acompanhar mudanças nos dados. Novos componentes devem responder a uma necessidade demonstrada por medição.

A alternativa Router local também foi avaliada. Na configuração pública testada em CPU, acertou as duas classificações em 23 dos 60 casos de avaliação, enquanto Jev acertou 60 de 60. O resultado se limita à adaptação e ao modelo usados naquele experimento, descrito no [relatório do Router](analise/RESULTADO-ROUTER-LOCAL.md).

## Caminho de uma consulta

O navegador solicita a carteira ao servidor. O servidor confere o perfil de acesso, consulta o PostgreSQL e retorna uma página com até 20 oportunidades. A seleção segue os filtros e a ordem da política operacional.

As regras locais já fornecem uma orientação. Quando o usuário solicita Jev, o servidor registra um pedido no banco. Uma tarefa em segundo plano retira esse pedido da fila, consulta o modelo e valida a resposta. A interface acompanha o estado enquanto o restante da carteira continua disponível.

O sistema informa a origem da orientação. A indicação de concordância com Jev significa que as respostas coincidiram com a política; não comprova qualidade comercial ou probabilidade de fechamento.

## Quando uma resposta pode ser reutilizada

Cada classificação identifica a oportunidade, a versão dos fatos e a assinatura dos critérios usados. Essa assinatura incorpora as perguntas, o modelo solicitado e uma identificação de revalidação. O registro também preserva origem, resposta validada e momento de gravação. A data de referência dos indicadores permanece nos fatos avaliados.

Uma resposta só aparece como atual se ainda corresponder aos dados e à política vigentes. Um prazo de validade isolado não bastaria: uma alteração no cadastro poderia tornar a resposta incorreta antes desse prazo.

O provedor informa um nome de modelo, sem identificar sua revisão interna exata. A identificação de revalidação permite separar novas avaliações das anteriores, mas possíveis mudanças internas do fornecedor ainda exigem acompanhamento. Os comandos estão no [guia da aplicação](app/README.md).

## Alterações durante o processamento

Considere uma consulta iniciada com a versão 7 de uma oportunidade. Se alguém salvar a versão 8 enquanto Jev responde, o resultado da versão 7 permanece histórico e não substitui uma classificação atual.

A conferência de versão e a publicação acontecem na mesma transação do banco. A chamada externa fica fora dessa transação para evitar bloqueios enquanto o serviço aguarda a rede. As leituras da carteira também conferem a correspondência das versões.

Antes de iniciar um pedido que ainda está na fila, o servidor verifica se ele já ficou desatualizado. Nesse caso, encerra o pedido sem consumir outra tentativa. Uma mudança posterior à reserva continua sendo tratada pela verificação final.

Duas edições baseadas na mesma versão geram conflito explícito. O banco também impede pedidos e resultados duplicados para a mesma combinação de oportunidade, versão e critérios. Isso protege o resultado persistido; uma interrupção entre a resposta externa e a gravação local ainda pode exigir outra chamada ao provedor.

## Limites de processamento e recuperação

A fila é persistida no PostgreSQL. O serviço usa bloqueios de linha e `SKIP LOCKED`, que permite a uma tarefa ignorar um registro já reservado por outra. Um controle compartilhado no banco limita a duas chamadas em execução, com pelo menos dois segundos entre seus inícios. Essa regra vale também quando há mais de um processo do servidor.

Cada chamada tem limite de 30 segundos. A reserva do pedido dura 45 segundos. Quando ela vence, outro processo pode recuperar o trabalho. O identificador dessa reserva impede que um processo antigo publique depois de ser substituído.

Falhas temporárias permitem até três tentativas totais, com espera progressiva. Uma interrupção gera um evento próprio, registrado uma única vez por tentativa. Quando o tempo não foi medido, a duração permanece desconhecida. Esgotamento de tentativas e falhas sem possibilidade de repetição exigem revisão técnica.

Esses parâmetros são conservadores para o provedor usado no ensaio. Ainda não demonstram a capacidade necessária para operação corporativa.

## Acesso, histórico e recuperação dos dados

| Controle | Implementação atual | Limite |
|---|---|---|
| Permissões | Servidor confere acesso de administrador, gestor e vendedor em cada operação. | Organização única e perfis locais de demonstração. |
| Credencial do Jev | Mantida no servidor, fora do navegador e dos recibos. | A gestão corporativa de segredos ainda precisa ser definida. |
| Acesso ao banco | Papel de execução com permissões limitadas; preparação usa acesso administrativo separado. | Políticas de acesso por linha do PostgreSQL não foram configuradas. |
| Histórico | Versões dos dados, classificações e tentativas registradas. A consulta mostra totais e até 20 registros por grupo. | Não representa histórico de contatos comerciais ausentes da base. |
| Cópia de segurança | Backup lógico restaurado e conferido em outra base. | Agendamento, armazenamento externo e recuperação para um instante específico estão pendentes. |
| Disponibilidade | Banco único com volume persistente local. | Não há alta disponibilidade nem operação entre regiões. |

A última revisão permitiu `null` na duração de uma tentativa interrompida. A migração é idempotente, ou seja, pode ser aplicada novamente sem mudar o resultado. Seu comando e os testes estão no [relatório das correções](analise/CORRECOES-REVISAO-LEAD-DESK.md).

## O que os testes mostraram

Os testes verificaram pedidos simultâneos, conflitos de edição, respostas atrasadas, mudanças de política, recuperação de interrupções e controle de acesso. As últimas correções foram verificadas em PostgreSQL temporário isolado. A interface foi exercitada com respostas controladas para testar situações como salvamento atrasado e falha na cópia de texto.

Na rodada de leitura por 30 segundos com 100 clientes, a alteração de paginação reduziu o p95 local de 853,1 ms para 114,9 ms, sem erros e preservando os resultados das consultas. P95 é o tempo até o qual terminaram 95% das respostas medidas. Esse ensaio não estabelece um compromisso de desempenho para outros ambientes.

O [guia da aplicação](app/README.md) reúne os comandos e as evidências. A avaliação com vendedores ainda precisa medir se as orientações ajudam a decidir e executar o trabalho.

## Decisões necessárias para uso corporativo

Antes de planejar uma instalação corporativa, é preciso conhecer a carga esperada, os perfis de acesso e a separação necessária entre equipes ou organizações. Também faltam escolhas de hospedagem, banco gerenciado e autenticação corporativa.

Metas de recuperação devem indicar quanto dado pode ser perdido e quanto tempo de indisponibilidade é aceitável. Replicação, quando adotada, não substitui backup. Réplicas usadas para leitura também exigem definir quando um atraso nos dados é aceitável.

Nenhuma escolha de linguagem ou banco oferece segurança absoluta. As garantias dependem da configuração, dos controles e dos testes no ambiente de operação. Não houve publicação nem validação de capacidade em produção.

## Referências

| Assunto | Fonte |
|---|---|
| Ideia original | [Proposta inicial](PROPOSTA-INICIAL.md) |
| Critérios de classificação | [Política de qualificação](analise/POLITICA-QUALIFICACAO.md) |
| Ensaio real | [Resultados do Jev](analise/RESULTADO-JEV-VERCEL.md) |
| Concorrência em Go | [Documentação do Go](https://go.dev/doc/effective_go#concurrency) |
| Isolamento de transações | [Documentação do PostgreSQL](https://www.postgresql.org/docs/current/transaction-iso.html) |
| Restrições de integridade | [Documentação do PostgreSQL](https://www.postgresql.org/docs/current/ddl-constraints.html) |
| Acesso por linha | [Documentação do PostgreSQL](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) |
| Recuperação para um instante específico | [Documentação do PostgreSQL](https://www.postgresql.org/docs/current/continuous-archiving.html) |
