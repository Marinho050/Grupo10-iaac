# Grupo 10 — IAAC: Deteção de Conexões Maliciosas

Projeto da unidade curricular IAAC (Introdução à Aprendizagem Automática e Ciência de Dados). Objetivo: construir um classificador que identifica, a partir de registos de rede (NetFlow-like), conexões maliciosas vs. benignas, para apoiar a triagem de alertas de um SOC (Security Operations Center).

## Estado do projeto

| Área | Estado |
|---|---|
| ML Canvas / Business Understanding | Feito (decisões documentadas abaixo e em `src/business_understanding.py`) |
| EDA (univariada, bivariada, multivariada, avançada) | Feito |
| Data Preparation (split, pipeline, desbalanceamento) | Feito |
| Modelação (comparação de modelos, afinação de threshold) | Feito |
| Avaliação final no conjunto de teste | Feito — critérios de sucesso cumpridos |
| Documentação do Data Understanding (dicionário de dados) | Feito — [`docs/Data_Understanding.md`](./docs/Data_Understanding.md) |
| Relatório final do projeto | Feito — [`docs/Relatorio_Final.md`](./docs/Relatorio_Final.md) |
| API de inferência (FastAPI) + testes automatizados | Feito — ver secção [API](#api-de-inferência) |
| Scripts reutilizáveis por etapa CRISP-ML(Q) | Feito — ver [`src/`](./src) |
| Branches individuais / Pull Requests da equipa | Em curso — depende de cada elemento |

Backlog completo com user stories, sprint board e templates Scrum: [`management/Backlog_Scrum_IAAC.xlsx`](./management/Backlog_Scrum_IAAC.xlsx).

## Estrutura do repositório

```
.
├── docs/                                        # documentação e referências do projeto
│   ├── IAAC_Roadmap_adaptado.docx                # roadmap da disciplina, adaptado ao projeto
│   ├── Machine_Learning_Canvas_v1.2.pdf          # ML Canvas preenchido
│   ├── Data_Understanding.md                     # dicionário de dados e limitações
│   └── Relatorio_Final.md                        # relatório final consolidado
├── management/
│   └── Backlog_Scrum_IAAC.xlsx                   # product backlog, sprint board, templates Scrum
├── notebooks/
│   ├── EDA_cybersecurity.ipynb                   # análise exploratória completa
│   ├── Data_Preparation_cybersecurity.ipynb      # split, pipeline, baseline
│   └── Modelling_cybersecurity.ipynb             # comparação de modelos, threshold, avaliação final
├── src/                                          # versão em módulo Python de cada etapa CRISP-ML(Q)
│   ├── business_understanding.py                 # custos de erro, critérios de sucesso
│   ├── data_understanding.py                     # perfil de qualidade de dados, correlações
│   ├── data_preparation.py                       # split estratificado, feature engineering, pipeline
│   ├── data_modeling.py                          # comparação de modelos, afinação de threshold
│   └── evaluation.py                             # avaliação final no conjunto de teste
├── datasets/
│   ├── Raw/                                      # dados originais (cybersecurity_network_logs.csv)
│   └── Process/                                  # dados tratados/transformados (gerados pelo pipeline)
├── models/
│   └── model_final.joblib                        # pipeline + threshold final, treinados
├── app/                                          # serviço de inferência (deployment)
│   ├── main.py                                   # API FastAPI (/predict, /health)
│   ├── config_prod.yml                           # configuração (host, porta, caminho do modelo)
│   └── tests/
│       └── test_main.py                          # testes automatizados da API
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Dataset

`datasets/Raw/cybersecurity_network_logs.csv` — 25.000 conexões de rede, 6 colunas:

| Coluna | Descrição |
|---|---|
| `Protocol` | Protocolo de rede (TCP / UDP / ICMP) |
| `Packet_Size_Bytes` | Tamanho do pacote (bytes) |
| `Connection_Duration_ms` | Duração da conexão (ms) |
| `Failed_Logins` | Número de tentativas de login falhadas |
| `Geo_Distance_km` | Distância geográfica estimada da origem (km) |
| `Is_Malicious` | Alvo — 1 = maliciosa, 0 = benigna (prevalência ≈ 4,99%) |

Sem valores nulos nem duplicados. Dataset aparenta ser sintético e limpo — os resultados de um baseline devem ser interpretados com cautela por causa disso (ver limitações em [`docs/Data_Understanding.md`](./docs/Data_Understanding.md)).

## Principais decisões (Business Understanding)

- **Momento da predição:** fim da conexão (flow-based, compatível com NetFlow) — `Connection_Duration_ms`, `Packet_Size_Bytes` e `Failed_Logins` só estão completos nesse momento.
- **Custo de erro:** falso negativo ≈ 500€ (incidente não detetado) vs. falso positivo ≈ 8€ (tempo de análise) — proporção ~60:1 a favor do recall.
- **Critérios de sucesso:** recall ≥ 90% com taxa de falsos positivos ≤ 1%.
- **Holdout:** modo alerta (sem bloqueio automático) durante a validação inicial, para não contaminar os dados com o efeito do próprio modelo.

Estas decisões estão implementadas em código (não só documentadas) em [`src/business_understanding.py`](./src/business_understanding.py):

```bash
python src/business_understanding.py
```

## Principais achados da EDA

- `Failed_Logins ≥ 3` é o sinal isolado mais forte (93–100% das conexões maliciosas).
- `Packet_Size_Bytes` e `Geo_Distance_km` discriminam bem mas de forma bimodal/não-linear (dois perfis de ataque: pacotes grandes vs. pequenos) — Pearson e Spearman divergem por isso.
- `Connection_Duration_ms` e `Protocol` têm pouco poder discriminativo isolado.
- Não remover outliers de `Packet_Size_Bytes`/`Geo_Distance_km` — são, em larga medida, as próprias conexões maliciosas.

Detalhe completo: [`notebooks/EDA_cybersecurity.ipynb`](./notebooks/EDA_cybersecurity.ipynb) ou, em script, [`src/data_understanding.py`](./src/data_understanding.py).

## Pipeline de preparação de dados

Split estratificado 70/15/15 → feature `High_Failed_Logins` (`Failed_Logins >= 3`) → `ColumnTransformer` (log1p + escalonamento nas variáveis assimétricas, escalonamento simples nas restantes, one-hot em `Protocol`) → `class_weight="balanced"` para o desbalanceamento.

Baseline (Random Forest, sem tuning) em validação: recall 89,3%, precisão 97,7%, taxa de falsos positivos 0,11%. Muito perto do critério de recall ≥ 90%; como a margem de falsos positivos é grande, o próximo passo é afinar o threshold de decisão.

Detalhe completo: [`notebooks/Data_Preparation_cybersecurity.ipynb`](./notebooks/Data_Preparation_cybersecurity.ipynb) ou, em script, [`src/data_preparation.py`](./src/data_preparation.py).

## Modelação e resultado final

Comparação por validação cruzada (5-fold, só no treino) entre Regressão Logística e Random Forest — o Random Forest venceu claramente (PR-AUC 0,926 vs. 0,866), confirmando a relação não-linear encontrada na EDA.

Threshold de decisão afinado na validação (0,5 → **0,465**) para recuperar recall sem violar o limite de falsos positivos.

**Avaliação final no conjunto de teste (usado uma única vez):**

| Métrica | Alvo | Resultado |
|---|---|---|
| Recall | ≥ 90% | **93,6%** |
| Taxa de falsos positivos | ≤ 1% | **0,08%** |
| PR-AUC | — | 0,957 |

De 187 conexões maliciosas no teste, o modelo deteta 175 (12 falsos negativos) e gera apenas 3 falsos positivos em 3.563 benignas. **Os dois critérios de sucesso do Business Understanding foram cumpridos.**

⚠️ O dataset parece sintético e muito limpo (sinal quase perfeito em `Failed_Logins`) — estes resultados são provavelmente otimistas face a tráfego real. Recomenda-se validar com dados de produção antes de qualquer bloqueio automático, mantendo entretanto o modo "alerta apenas".

Modelo final treinado e pronto a usar: [`models/model_final.joblib`](./models/model_final.joblib) (pipeline completo + threshold = 0,465). Carregar com:

```python
import joblib
bundle = joblib.load("models/model_final.joblib")
pipeline, threshold = bundle["pipeline"], bundle["threshold"]

proba = pipeline.predict_proba(X_novo)[:, 1]
pred = (proba >= threshold).astype(int)
```

Para reproduzir a comparação de modelos e re-treinar: `python src/data_modeling.py`. Para a avaliação final no teste: `python src/evaluation.py`.

Detalhe completo: [`notebooks/Modelling_cybersecurity.ipynb`](./notebooks/Modelling_cybersecurity.ipynb).

## API de inferência

O modelo é servido por uma API FastAPI em [`app/main.py`](./app/main.py).

### Correr com Docker

```bash
docker-compose up
```

### Correr localmente

```bash
pip install -r requirements.txt
cd app
python main.py
```

*Nota: o endereço e a porta podem ser alterados em [`app/config_prod.yml`](./app/config_prod.yml).*

Documentação interativa (Swagger): http://0.0.0.0:8003/docs

### Exemplo de pedido

```python
import requests

input_data = {
    "Protocol": "TCP",
    "Packet_Size_Bytes": 805,
    "Connection_Duration_ms": 120,
    "Failed_Logins": 0,
    "Geo_Distance_km": 1169,
}

response = requests.post("http://0.0.0.0:8003/predict", json=input_data)
print(response.json())
```

Resposta:
```json
{"prediction_Id": "...", "predict": 0, "predict_prob": 0.01, "threshold": 0.465}
```

### Testes

```bash
pytest -v
```

```
app/tests/test_main.py::test_health_endpoint PASSED
app/tests/test_main.py::test_predict_benign PASSED
app/tests/test_main.py::test_predict_likely_malicious PASSED
```

## Como correr os notebooks

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install pandas numpy matplotlib seaborn scipy scikit-learn jupyter joblib

jupyter notebook notebooks/
```

## Próximos passos

1. Cada elemento criar a sua branch e preencher a coluna "Responsável" no backlog ([`management/Backlog_Scrum_IAAC.xlsx`](./management/Backlog_Scrum_IAAC.xlsx)).
2. Abrir e fundir os Pull Requests pendentes de cada elemento.
3. Validar o modelo com dados de produção/reais antes de considerar qualquer bloqueio automático (o dataset atual é provavelmente sintético e otimista).

## Equipa e organização

Cada elemento trabalha numa branch própria a partir das user stories do backlog (ver `management/Backlog_Scrum_IAAC.xlsx`, coluna "Branch"). Fluxo sugerido:

```bash
git checkout -b nome-do-elemento/numero-da-story
# ... trabalho ...
git add .
git commit -m "descrição da alteração"
git push -u origin nome-do-elemento/numero-da-story
```

Depois, abrir Pull Request para `main` e pedir revisão a outro elemento do grupo antes do merge.
