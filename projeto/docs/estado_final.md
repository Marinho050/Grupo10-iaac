# Estado final da componente Trojan

Atualização em 7 de outubro de 2026. Responsável identificado: Márcio Araújo.

## Feito e validado

Roadmap adaptado, revisão do canvas, auditoria e EDA com Pearson/Spearman/PCA, preparação sem fuga de medianas, inferência sem rótulos, sete candidatos treinados e guardados, seleção e limiar na validação, avaliação reservada por IP, intervalos por grupo, explicação por permutação, PSI corrigido, CLI, API e dashboard local. Foram acrescentados backlog, sprints propostos, três diagramas, documentação por classes/funções, model card, notebook e sistemas de agentes em Python e LangGraph com Qwen local pré-treinado.

Validação: 20 testes aprovados sem skips ou falhas; seis células de código do notebook executadas sem erros; CLI pontuou cinco fluxos sem Class; os dois backends dos agentes produziram os mesmos factos; API e interface pontuaram um fluxo real; pip check sem conflitos. Evidências em reports/validacao_execucao.json e reports/testes.xml.

## Desempenho e aprovação

HGB selecionado na validação; limiar 0,9275683468476112. Teste com 5 604 fluxos e 449 IPs de origem novos: AUC ROC 0,6425; recall 4,30%; FPR 4,23%; precisão 48,12%. O critério original recall de 90% e FPR de 5% não foi atingido. A demonstração usa revisão manual e não executa bloqueios.

A latência individual medida tem média 88,6 ms e p95 97,7 ms para transformação de estatísticas já disponíveis, inferência e limiar. Não mede extração PCAP e não garante um limite de pior caso. Os dados são de 2017; o desempenho numa rede atual permanece por validar.

A auditoria encontrou 650 grupos de features idênticas com classes distintas, envolvendo 3 331 linhas, e zero conflitos pela assinatura bruta que mantém identificadores. A afirmação histórica de 61,3% não é reproduzida pelas definições atuais. Contextos diferentes podem justificar a mesma representação com classes distintas; não se declara erro de rótulo sem investigação.

## Ainda falta para o projeto completo do grupo

1. Identificar os restantes elementos e disponibilizar os seus datasets e modelos. Integrar todos no notebook e nos diagramas do grupo.
2. Confirmar validação do dataset pelo professor, origem/licença e os templates do Classroom.
3. Registar reuniões SCRUM realmente realizadas, com participação e decisões do grupo.
4. Redigir o relatório académico de 25 a 30 páginas no template e partilhar com o professor com histórico. O enunciado exige autoria dos alunos; a documentação técnica assistida é uma entrega separada.
5. Preparar e realizar a defesa individual de 5 a 7 minutos, com componentes de código escolhidos e explicados pelo aluno.
6. Construir a imagem Docker numa máquina com Docker, se essa forma de deployment for escolhida. A API local foi efetivamente executada; não houve deployment público.
7. Para uso operacional, recolher dados recentes com ambas as classes, definir uma nova reserva, cumprir as metas e confirmar capacidade/custos do SOC.

A CI do GitHub foi executada e aprovada na versão de código e3d4823, run 37637195526. Instalou as dependências em Ubuntu, executou os testes centrais e validou a CLI. Evidência em reports/ci_github.json. O histórico da branch Márcio contém os commits de implementação, modelos, agentes, documentação e confirmação desta validação.
