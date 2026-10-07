# Deteção de trojans em fluxos de rede

Componente de Márcio Araújo no Grupo 10 IAAC. Pipeline scikit-learn com preparação consistente, vários classificadores, avaliação por IP de origem, CLI, API local, notebook e agentes de relatórios. O modelo atual não atinge o critério de produção do canvas; a demonstração disponibiliza scores para revisão manual.

## Resultados reproduzidos

Dataset: 177 482 fluxos, 86 colunas, 90 683 Trojan e 86 799 Benign. Os dias recentes contêm apenas positivos. Separação fixa por Source IP: 60 693 treino, 111 185 validação e 5 604 teste, com zero sobreposição de IPs de origem. As proporções de linhas não são 56/19/25 porque 25% se refere a grupos e existem IPs dominantes.

Sete candidatos foram treinados: baseline, logística, árvore, RF, HGB, HGB regularizado e HGB sem portas/indicadores de host. O modelo foi selecionado por recall sob FPR máximo de 5% na validação, seguido de AUC PR/ROC. O teste não participa na escolha de modelo nem limiar.

Modelo escolhido: HGB. No teste reservado: AUC ROC 0,6425, recall Trojan 4,30%, FPR 4,23%, limiar 0,927568. O critério de recall de 90% com FPR de 5% falhou. O IC95% de AUC por bootstrap de IPs é aproximadamente 0,532 a 0,768. A experiência aleatória de diagnóstico obteve AUC 0,754 e não serviu para selecionar o modelo. Ver [avaliação completa](reports/avaliacao_final.json).

## Executar passo a passo no VS Code

Abrir esta pasta e selecionar .venv/Scripts/python.exe. O ambiente local já foi instalado. Numa nova máquina com Python 3.12:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

Colocar Trojan_Detection.csv em data/. O dataset não é publicado no Git. A origem pública e licença precisam de confirmação pelo grupo; o manifesto guarda o SHA256 do ficheiro fornecido.

```powershell
.\.venv\Scripts\python.exe -m src.eda
.\.venv\Scripts\python.exe -m src.modelacao
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe predict.py examples/fluxos_sem_rotulo.csv --saida reports/scores.csv
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Abrir http://127.0.0.1:8000 para a interface, /docs para testar a API, /schema para o contrato e /health para estado e decisão de deployment. Enviar examples/pedido_api.json para POST /predict. A inferência aceita estatísticas sem Class, IP ou Timestamp e rejeita colunas obrigatórias em falta. Não preenche silenciosamente features ausentes com zero.

Abrir [notebooks/01_pipeline.ipynb](notebooks/01_pipeline.ipynb) e executar todas as células. Usa funções dos módulos, carrega todos os classificadores, testa a API e chama os agentes. O retreino é explícito; os resultados comprometidos no Git permitem demonstrar o sistema sem repetir experiências.

## Agentes de relatórios

A componente generativa é opcional para a nota, mas tem duas implementações: funções Python e StateGraph LangGraph. Ambas usam o mesmo classificador e o mesmo gerador Transformers local. O Qwen é pré-treinado pelos autores e guardado em models/llm; não houve fine-tuning neste projeto.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-llm-lock.txt
.\.venv\Scripts\python.exe scripts/preparar_llm.py
.\.venv\Scripts\python.exe -m src.agentes --backend python
.\.venv\Scripts\python.exe -m src.agentes --backend langgraph
```

Os pesos generativos têm cerca de 1 GB e ficam fora do Git e do ZIP. O manifesto fixa a revisão obtida. Durante a geração não é necessário serviço externo nem envio dos fluxos. Sem os pesos, usar --sem-llm para executar explicitamente apenas o relatório factual. Comentários neurais requerem revisão; nunca modificam scores, métricas ou decisões.

## Organização e entregas

- [Roadmap adaptado](docs/roadmap_adaptado.md), [estado final](docs/estado_final.md) e [canvas revisto](docs/canvas_revisto.md).
- [Backlog](docs/backlog.md) e [SCRUM](docs/scrum.md), com campos para reuniões reais.
- [Explicação do código](docs/guia_tecnico.md), [diagramas](docs/diagramas.md) e [operação](docs/operacao.md).
- [Model card](models/MODEL_CARD.md), modelos em models/ e evidências em reports/.
- [Guião do relatório académico](docs/relatorio_academico_guiao.md), que precisa de autoria do grupo e do template do professor.

O código FastAPI de exemplo existente no repositório do grupo foi preservado na raiz e não é a API desta componente. A CI desta componente executa apenas projeto/tests.

O Dockerfile desta pasta empacota a API Trojan. Docker não está instalado nesta máquina; a imagem ainda precisa de um build numa máquina com Docker. Não foi feito deployment público.

## Referências técnicas

- [scikit-learn sobre preparação e fuga de informação](https://scikit-learn.org/stable/common_pitfalls.html)
- [Seleção de limiar](https://scikit-learn.org/stable/modules/classification_threshold.html)
- [Qwen2.5 0.5B Instruct e licença Apache 2](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct)
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- Machine Learning Canvas de Louis Dorard, OWNML, 2015. O canvas fornecido mantém a atribuição e licença CC BY SA 4.0.
