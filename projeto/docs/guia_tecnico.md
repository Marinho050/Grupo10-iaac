# Guia técnico do código

Este documento explica o código assistido da componente Trojan por módulos, classes e funções, incluindo escolhas, compromissos e casos de fronteira. A documentação é gerada com IA, conforme a entrega técnica pedida, e não constitui o relatório académico do grupo. Os números de linha correspondem à versão de código entregue.

## Decisões de implementação

O modelo é um Pipeline sklearn porque todas as transformações ajustadas nos dados devem ser aprendidas apenas no treino e preservadas para a inferência. A engenharia determinística de FlowFeatures evita depender da composição de um lote novo. O esquema treinado torna a ausência de uma estatística um erro explícito; zero seria uma observação inventada.

A separação usa IP de origem como entidade e seeds definidas antes das experiências. O mesmo IP nunca entra em dois conjuntos, mas IPs de destino e padrões semelhantes podem repetir. Dois hosts dominam grande parte das linhas, pelo que as frações de grupos diferem muito das frações de fluxos. Esta limitação é registada em splits.json. A reserva final é observada só depois da seleção e não orienta alterações de candidatos.

Os candidatos representam complexidade crescente: baseline probabilístico, logística escalada, árvore limitada, Random Forest e boosting por histogramas. Uma segunda parametrização HGB regulariza mais; a ablação retira portas e três indicadores de host. Os valores foram pré-definidos; não foi executada uma pesquisa extensa de hiperparâmetros. early_stopping=False evita que o HGB crie uma validação aleatória interna que misture entidades. Quatro threads limitam consumo e variabilidade de execução.

Escolher modelo e limiar é uma decisão na validação. O critério maximiza recall respeitando FPR de 5% e desempata por AUC PR/ROC. Não se reduz a meta de recall de 90% para declarar sucesso. No teste o recall foi 4,30%, portanto a versão é apenas uma demonstração. AUC e precisão não substituem o requisito de recall. Brier é registado como diagnóstico de scores, mas não foi feita calibração probabilística em dados recentes representativos.

O bootstrap reamostra IPs, em vez de linhas, para reconhecer dependência entre fluxos. O intervalo é descritivo, não uma garantia de generalização. O teste temporal é analisado, mas não permite FPR/ROC AUC em dias contendo só uma classe. Importância por permutação no teste serve apenas para explicar o artefacto fixo, nunca para escolher novamente features nesta reserva.

A inferência, CLI e API usam Predictor. A API não altera o limiar nem aceita modelos externos, limita o número de fluxos e rejeita um esquema incompleto. A interface mostra o estado de deployment e envia apenas pedidos à API local. Os resultados são construídos com textContent no browser, evitando interpretar texto introduzido como HTML.

O gerador Qwen é pré-treinado e permanece local em models/llm. Os dois agentes têm papéis separados: o classificador calcula factos, o relator produz texto auxiliar. Python e LangGraph chamam as mesmas funções, permitindo comparar orquestrações sem mudar a semântica. Os factos são escritos diretamente no relatório e o comentário neural não os substitui. Não foi feito fine-tuning nem medida a qualidade do texto numa avaliação humana ampla.

## Sequência interna do treino

1. Ler e validar rótulos e metadados. Guardar índices dos conjuntos e contagens reais de linhas, classes e IPs.
2. Para cada candidato, criar um novo Pipeline e ajustar só no treino. Pontuar a validação e escolher o respetivo limiar sob o limite de FPR.
3. Guardar os sete candidatos e a comparação da validação. Escolher o vencedor pela regra pré-definida.
4. Pontuar o vencedor no teste reservado com o mesmo limiar. Calcular matriz de confusão, métricas, intervalo por grupos e comparação com o baseline.
5. Executar o diagnóstico aleatório separadamente, sem o usar na seleção. Calcular importância por permutação como explicação descritiva.
6. Guardar scores de teste, métricas por dia, PSI e projeção de volume sob a amostragem do dataset. A projeção não mede a capacidade real do SOC.
7. Serializar o pipeline efetivamente avaliado, com versão sklearn, esquema, limiar e aprovação offline. Não refazer fit em todos os dados depois de medir.
8. Medir cem chamadas individuais com transformação, imputação, inferência e limiar. A medição exclui captura e extração PCAP; p95 não é um limite de pior caso.

## Contratos e fronteiras cobertas

As labels de treino aceitam apenas Benign e Trojan. Protocol é inteiro de 0 a 255; Destination Port é inteiro de 0 a 65535. Estatísticas inválidas em texto geram erro; NaN e infinitos nas estatísticas passam a missing para imputação aprendida no treino. Taxas usam log assinado para preservar o sinal. Os campos de TCP podem conter sentinelas como -1; não são confundidos com portas.

Nomes duplicados após retirar espaços são rejeitados. As categorias de protocolo e porta têm sempre a mesma ordem, incluindo lotes com um único protocolo. Class, IPs e Timestamp não são exigidos para pontuar; colunas numéricas treinadas não podem desaparecer. A mediana nunca é recalculada no lote de previsão. O PSI tem extremos infinitos para incluir valores novos fora do intervalo da referência e um tratamento próprio para referências constantes.

## Contrato de dados e representação

Ficheiro `src/preparacao.py`. As transformações aqui são determinísticas; imputação e remoção de variância ficam dentro do Pipeline ajustado no treino.

### normalizar

`normalizar` nas linhas 12 a 17. Copia o DataFrame, retira espaços dos nomes e rejeita colisões. A cópia evita alterar o objeto do chamador.

### carregar

`carregar` nas linhas 19 a 20. Lê o CSV e normaliza os nomes uma única vez. O formato esperado continua a ser uma exportação tabular de fluxos.

### rotulos

`rotulos` nas linhas 22 a 28. Converte Trojan para 1 e Benign para 0. Rejeita labels desconhecidas ou em falta, evitando tratá-las silenciosamente como benignas.

### metadados

`metadados` nas linhas 30 a 36. Extrai os campos usados na avaliação e converte a data no formato explícito dia/mês/ano. Estes campos não entram nas features.

### Classe FlowFeatures

Linhas 38 a 90. Aprende apenas o esquema; imputação e seleção são passos posteriores do Pipeline.

### FlowFeatures   init

`FlowFeatures.__init__` nas linhas 40 a 42. Expõe opções sklearn para a ablação de portas e indicadores de host. Não faz trabalho dependente dos dados no construtor.

### FlowFeatures fit

`FlowFeatures.fit` nas linhas 44 a 56. Guarda o conjunto de colunas numéricas e exigidas a partir do treino. Valida o esquema sem aprender medianas ou usar rótulos.

### FlowFeatures transform

`FlowFeatures.transform` nas linhas 58 a 84. Aplica conversões, log assinado e categorias fixas. Rejeita colunas ausentes, strings inválidas e portas/protocolos fora do contrato.

### FlowFeatures get feature names out

`FlowFeatures.get_feature_names_out` nas linhas 86 a 90. Devolve nomes na mesma ordem da transformação, permitindo rastrear a representação e a seleção de variância.

## Separação e avaliação

Ficheiro `src/avaliacao.py`. Centraliza a semântica de grupos, rótulos, limiar e métricas para evitar regras divergentes entre scripts.

### separar

`separar` nas linhas 8 a 19. Separa primeiro grupos de teste e depois validação nos grupos restantes. Verifica duas classes e zero interseção de IPs; não procura seeds pelo desempenho.

### separar aleatorio

`separar_aleatorio` nas linhas 21 a 24. Cria uma experiência estratificada de diagnóstico com indivíduos repetidos entre conjuntos. O resultado é identificado como otimista e fica fora da escolha final.

### metricas

`metricas` nas linhas 26 a 37. Calcula a matriz TN FP FN TP com ordem fixa de labels, métricas de deteção, ranking e Brier. Em conjuntos de uma só classe, métricas não estimáveis ficam como None.

### escolher limiar

`escolher_limiar` nas linhas 39 a 45. Usa todos os pontos ROC da validação e seleciona o maior recall sob FPR máximo. A inclusão do ponto sem alertas permite representar um modelo incapaz de cumprir a meta.

### bootstrap auc grupos

`bootstrap_auc_grupos` nas linhas 47 a 59. Sorteia IPs com reposição e inclui todas as suas linhas. Descarta replicações sem duas classes e regista a unidade de reamostragem e contagem válida.

## Treino e seleção

Ficheiro `src/modelacao.py`. É o único ponto de treino e publicação dos artefactos. Guarda os resultados antes de disponibilizar a demonstração.

### guardar json

`guardar_json` nas linhas 28 a 29. Serializa resultados legíveis em UTF8 e proíbe NaN JSON não padrão. Falhar aqui evita publicar um manifesto inválido.

### candidatos

`candidatos` nas linhas 31 a 40. Define sete alternativas pré-fixadas, incluindo baseline e ablação. Árvores limitadas reduzem complexidade e custo; não há promessa de ótimo global.

### pipeline

`pipeline` nas linhas 42 a 47. Liga engenharia, mediana, variância e modelo. A logística recebe StandardScaler; as árvores dispensam escala. Cada candidato tem uma instância nova.

### treinar

`treinar` nas linhas 49 a 139. Coordena as oito etapas descritas acima. Os modelos guardados são os mesmos medidos; limiar e seleção são decididos na validação. O retorno é o manifesto final.

### main

`main` nas linhas 141 a 143. Ponto de entrada da ferramenta. Reúne argumentos e chama as funções do módulo; executar com os comandos do README mantém o mesmo comportamento do notebook e da demonstração.

## Compreensão dos dados

Ficheiro `src/eda.py`. Estatística descritiva, correlações e PCA apoiam a análise; não são usadas para selecionar transformações pelo teste.

### analisar

`analisar` nas linhas 17 a 65. Calcula qualidade, assinaturas, estatísticas, classes por dia/protocolo, Pearson/Spearman, boxplots e PCA. Distingue assinaturas brutas de representações sem contexto.

### main

`main` nas linhas 67 a 68. Ponto de entrada da ferramenta. Reúne argumentos e chama as funções do módulo; executar com os comandos do README mantém o mesmo comportamento do notebook e da demonstração.

## Inferência partilhada

Ficheiro `src/inferencia.py`. Uma classe central serve CLI, API e agentes. O modelo vem apenas do caminho local escolhido pelo operador.

### Classe Predictor

Linhas 11 a 30. Define o contrato de estado ou de dados usado pelas funções deste módulo.

### Predictor   init

`Predictor.__init__` nas linhas 12 a 18. Carrega o pacote local, verifica a versão de esquema e sklearn e mantém o modelo em memória. Não carrega artefactos recebidos de utilizadores da API.

### Predictor predict

`Predictor.predict` nas linhas 20 a 30. Valida lote e limiar, executa o pipeline e devolve score, alerta e ação de revisão. A ordem de Flow ID é preservada quando o campo existe.

## Monitorização de distribuições

Ficheiro `src/psi.py`. O PSI demonstra mudança entre amostras e não infere causalidade, erro de rótulo ou necessidade automática de retreino.

### psi

`psi` nas linhas 5 a 20. Cria bins da referência com extremos abertos, inclui missing e usa suavização positiva. Referências constantes continuam a permitir detetar valores novos.

### psi counts

`psi.counts` nas linhas 7 a 9. Conta observações finitas em bins e observações não finitas numa categoria separada, conservando a massa de probabilidade.

### tabela psi

`tabela_psi` nas linhas 22 a 23. Aplica a mesma definição de PSI a todas as features e ordena sinais para inspeção do analista.

## Agentes de classificação e relato

Ficheiro `src/agentes.py`. A orquestração direta e LangGraph partilham o mesmo estado e factos. A geração é neural apenas quando usar_llm=True.

### Classe Estado

Linhas 12 a 17. Define o contrato de estado ou de dados usado pelas funções deste módulo.

### carregar gerador

`carregar_gerador` nas linhas 20 a 28. Mantém tokenizer e Qwen local em cache de processo, limita threads e desativa código remoto. Exige pesos previamente obtidos e não faz download durante a geração.

### agente classificador

`agente_classificador` nas linhas 30 a 36. Pontua o CSV com Predictor e produz um dicionário factual agregado. O recall/FPR são os do teste histórico, não inferidos do lote sem rótulo.

### validar comentario

`validar_comentario` nas linhas 38 a 43. Aceita apenas explicação genérica de revisão humana, sem métricas ou alegações operacionais.

### agente relator

`agente_relator` nas linhas 45 a 62. Gera uma explicação genérica sem sampling, sujeita a um filtro lexical conservador que rejeita métricas e afirmações operacionais. A política de aprovação é escrita por código a partir dos factos. O filtro não garante veracidade geral; o comentário continua sujeito a revisão humana. Com geração desativada, declara isso explicitamente.

### executar

`executar` nas linhas 64 a 82. Encadeia agentes em Python ou StateGraph, preserva a tabela factual e, se guardar=True, escreve o relatório. Os testes usam guardar=False para não modificar entregas.

### main

`main` nas linhas 84 a 87. Ponto de entrada da ferramenta. Reúne argumentos e chama as funções do módulo; executar com os comandos do README mantém o mesmo comportamento do notebook e da demonstração.

## Deployment local

Ficheiro `api.py`. Endpoints pequenos reutilizam Predictor. A carga do modelo no lifespan falha cedo se o artefacto não estiver disponível.

### Classe Pedido

Linhas 10 a 11. Define o contrato de estado ou de dados usado pelas funções deste módulo.

### lifespan

`lifespan` nas linhas 14 a 16. Carrega uma única instância do preditor no arranque da API. Um artefacto inválido impede o serviço de anunciar disponibilidade.

### health

`health` nas linhas 21 a 23. Devolve disponibilidade, nome do modelo, aprovação offline e modo de demonstração. Um status ok não significa aprovação de produção.

### schema

`schema` nas linhas 26 a 28. Publica as colunas exigidas e o limiar fixo do artefacto, permitindo construir pedidos corretos sem tentar adivinhar features.

### predict

`predict` nas linhas 31 a 37. Converte o pedido em DataFrame, chama Predictor e transforma erros de contrato em HTTP 422. Não autoriza bloqueios nem modifica o limiar.

### dashboard

`dashboard` nas linhas 40 a 40. Serve o HTML local; os resultados são obtidos por chamadas à mesma API.

## Previsão de CSV

Ficheiro `predict.py`. Argumentos explícitos permitem novos ficheiros e diretórios de saída; o limiar por defeito vem da validação.

### main

`main` nas linhas 7 a 14. Ponto de entrada da ferramenta. Reúne argumentos e chama as funções do módulo; executar com os comandos do README mantém o mesmo comportamento do notebook e da demonstração.

## Inspeção do pacote

Ficheiro `src/empacotar.py`. Evita um segundo script de treino com critérios diferentes; o empacotamento é feito pelo treino principal.

### main

`main` nas linhas 4 a 5. Ponto de entrada da ferramenta. Reúne argumentos e chama as funções do módulo; executar com os comandos do README mantém o mesmo comportamento do notebook e da demonstração.

## Consulta de evidências

Ficheiro `src/limiares_interpretabilidade.py`. Apresenta ficheiros já calculados em vez de refazer treino ou selecionar limiar no teste.

### main

`main` nas linhas 5 a 7. Ponto de entrada da ferramenta. Reúne argumentos e chama as funções do módulo; executar com os comandos do README mantém o mesmo comportamento do notebook e da demonstração.

## Preparação do gerador

Ficheiro `scripts/preparar_llm.py`. Resolve uma revisão fixa e descarrega apenas pesos e configuração do modelo público. Usa o manifesto existente em execuções posteriores.

### main

`main` nas linhas 7 a 15. Ponto de entrada da ferramenta. Reúne argumentos e chama as funções do módulo; executar com os comandos do README mantém o mesmo comportamento do notebook e da demonstração.

## Execução do notebook

Ficheiro `scripts/executar_notebook.py`. Usa o interpretador corrente no kernel para impedir que o notebook corra silenciosamente noutro ambiente.

### main

`main` nas linhas 9 a 16. Ponto de entrada da ferramenta. Reúne argumentos e chama as funções do módulo; executar com os comandos do README mantém o mesmo comportamento do notebook e da demonstração.

## Testes e limites de validação

`tests/test_pipeline.py` cobre inferência sem rótulo, categorias fixas, valores inválidos, colunas ausentes, medianas aprendidas no treino, invariância ao lote, nomes duplicados, labels desconhecidas, separação por IP, confusão, limiares, métricas de uma classe, extremos/constantes no PSI, pacote serializado e API com o modelo real. Os casos parametrizados de porta, protocolo e strings geram execuções distintas.

`tests/test_agents.py` verifica contagens factuais, política de revisão e equivalência dos backends sem substituir relatórios existentes. A geração neural foi também executada separadamente com os pesos locais. Não há teste automatizado que garanta veracidade total do texto gerado.

`static/index.html` valida JSON no browser, apresenta erros de contrato e constrói uma tabela com número de fluxo, score e decisão. A API é a autoridade para validação; a interface não redefine métricas ou limiares.

O notebook executa funções partilhadas e carrega todos os classificadores em models, testa a API e chama os dois agentes. RETREINAR=False evita refazer uma experiência apenas para consultar resultados. A CI do GitHub valida os testes centrais e a CLI; a componente neural exige a instalação opcional e download explícito dos pesos.

O Dockerfile foi escrito, mas não construído porque Docker não está instalado. Não houve teste em sensor real, deployment público, avaliação clínica ou operacional, auditoria de segurança nem integração dos outros datasets do grupo.

## Fontes técnicas

scikit-learn Common pitfalls and recommended practices https://scikit-learn.org/stable/common_pitfalls.html

scikit-learn Tuning the decision threshold https://scikit-learn.org/stable/modules/classification_threshold.html

Qwen2.5 0.5B Instruct https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct

LangGraph Graph API https://docs.langchain.com/oss/python/langgraph/graph-api
