# Deteção de trojans em fluxos de rede

Projeto de Márcio Araújo para o Grupo 10 IAAC. O sistema recebe características de comunicações de rede e calcula scores e alertas para revisão humana.

**Este é o único README do projeto.** A pasta `projeto/` contém os ficheiros de trabalho, organizados por função. Não existe outro projeto dentro dela.

## Começar aqui

1. Abra **Trojan-IAAC.code-workspace** no VS Code.
2. Consulte este README para executar a demonstração.
3. Para estudar o trabalho, consulte o [guia técnico](projeto/docs/guia_tecnico.md), o [roadmap](projeto/docs/roadmap_adaptado.md) e os [diagramas](projeto/docs/diagramas.md).

## Abrir a página local

Abra um terminal na raiz deste repositório e execute:

```powershell
cd projeto
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Mantenha o terminal aberto e visite **http://127.0.0.1:8000/**. Para parar o servidor, use **Ctrl+C**.

A página pontua as estatísticas enviadas; não captura automaticamente o tráfego da rede. Use o conteúdo de [pedido_api.json](projeto/examples/pedido_api.json) para testar. A documentação da API está em http://127.0.0.1:8000/docs.

No VS Code também pode escolher **Terminal > Run Task > 4 Abrir API local**. As tarefas já usam a pasta e o interpretador corretos.

## Onde está cada coisa

```text
projeto-trojan-detection/
├── README.md                      instruções e visão geral
├── Trojan-IAAC.code-workspace      abrir o projeto no VS Code
├── LICENSE                        licença do repositório
├── .github/workflows/             testes automáticos no GitHub
├── .vscode/                       configuração e tarefas do VS Code
└── projeto/
    ├── src/                       preparação, treino, avaliação e agentes
    ├── api.py                     serviço da demonstração
    ├── predict.py                 previsão a partir de um CSV
    ├── static/                    página apresentada no navegador
    ├── models/                    modelos treinados e manifestos
    ├── data/                      dataset local
    ├── examples/                  exemplos para testar
    ├── notebooks/                 notebook do trabalho
    ├── tests/                     testes do código
    ├── reports/                   resultados atuais e evidências
    ├── figs/                      gráficos da análise
    ├── docs/                      explicações, roadmap e gestão
    ├── scripts/                   preparação do LLM e execução do notebook
    ├── requirements*.txt          dependências
    └── Dockerfile                 empacotamento opcional da API
```

**Os resultados atuais estão em `projeto/reports/`; os classificadores atuais estão em `projeto/models/`.** Os ficheiros de experiências antigas foram guardados fora da pasta do projeto. Os ambientes e caches ficam ocultos no Explorer do VS Code para reduzir a confusão.

## Executar as etapas do trabalho

Os comandos seguintes são executados dentro de `projeto/`, depois de `cd projeto`:

```powershell
.\.venv\Scripts\python.exe -m src.eda
.\.venv\Scripts\python.exe -m src.modelacao
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe predict.py examples/fluxos_sem_rotulo.csv --saida reports/scores.csv
```

- `src.eda`: analisar os dados e gerar gráficos.
- `src.modelacao`: treinar candidatos, escolher na validação e avaliar a reserva de teste.
- `pytest`: verificar os comportamentos do código.
- `predict.py`: pontuar um CSV sem voltar a treinar.

O [notebook](projeto/notebooks/01_pipeline.ipynb) usa funções dos mesmos módulos, carrega os classificadores, testa a API e chama os agentes. O retreino é explícito. O teste atual já foi observado e não deve orientar repetidamente novas escolhas apresentadas como independentes.

## Modelos e resultados

Foram treinados sete candidatos scikit-learn: baseline trivial, regressão logística, árvore de decisão, Random Forest, HistGradientBoosting (HGB), HGB mais regularizado e HGB sem portas e indicadores de host.

O HGB foi escolhido na validação por ter o maior recall sob a restrição de falsos positivos de 5%, com desempate por AUC PR/ROC. O limiar escolhido foi 0,927568.

No teste reservado: AUC ROC 0,6425, recall Trojan 4,30%, falsos positivos 4,23%. **A meta de recall de 90% com FPR de no máximo 5% não foi atingida.** A aplicação é uma demonstração para revisão humana, sem bloqueio automático.

O dataset tem 177 482 fluxos e 86 colunas. A separação por IP de origem produziu 60 693 linhas de treino, 111 185 de validação e 5 604 de teste. Não há IPs de origem partilhados entre os conjuntos; as frações de grupos diferem das frações de linhas por existirem IPs dominantes.

Evidências: [comparação na validação](projeto/reports/comparacao_validacao.csv), [avaliação final](projeto/reports/avaliacao_final.json), [qualidade dos dados](projeto/reports/qualidade_dados.json) e [model card](projeto/models/MODEL_CARD.md).

## Instalar numa nova máquina

Com Python 3.12, dentro de `projeto/`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

Coloque `Trojan_Detection.csv` em `projeto/data/`. O dataset fica fora do Git e do ZIP. O seu hash está na avaliação final; a origem pública e licença ainda precisam de confirmação pelo grupo.

## Agentes de relatórios opcionais

Há duas orquestrações: funções Python e LangGraph. O classificador calcula os factos; o Qwen pré-treinado produz um comentário genérico sujeito a filtro e revisão humana. Não houve fine-tuning do Qwen neste projeto, e o seu texto não decide scores, limiares ou aprovação de produção.

Dentro de `projeto/`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-llm-lock.txt
.\.venv\Scripts\python.exe scripts/preparar_llm.py
.\.venv\Scripts\python.exe -m src.agentes --backend python
.\.venv\Scripts\python.exe -m src.agentes --backend langgraph
```

Os pesos Qwen são guardados em `projeto/models/llm/`, têm cerca de 1 GB e não entram no Git ou ZIP. O manifesto fixa a revisão. A geração é local. `--sem-llm` desativa explicitamente a geração neural.

## Documentação e entrega

- [Estado e pendências](projeto/docs/estado_final.md).
- [Roadmap](projeto/docs/roadmap_adaptado.md) e [canvas revisto](projeto/docs/canvas_revisto.md).
- [Explicação do código](projeto/docs/guia_tecnico.md) e [diagramas](projeto/docs/diagramas.md).
- [Backlog](projeto/docs/backlog.md) e [SCRUM](projeto/docs/scrum.md).
- [Operação](projeto/docs/operacao.md) e [guião do relatório académico](projeto/docs/relatorio_academico_guiao.md).

Faltam os restantes datasets do grupo, os templates do professor, as reuniões reais e a autoria/apresentação dos alunos. Docker não foi executado nesta máquina; a API local foi testada.

## Referências

- [scikit-learn e prevenção de fuga de informação](https://scikit-learn.org/stable/common_pitfalls.html).
- [Escolha do limiar](https://scikit-learn.org/stable/modules/classification_threshold.html).
- [Qwen2.5 0.5B Instruct](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct).
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api).
- Machine Learning Canvas de Louis Dorard, OWNML, 2015. O canvas fornecido mantém a atribuição e licença CC BY SA 4.0.
