# Grupo 10 — IAAC: Deteção de Ransomware/Malware

Projeto de deteção de malware/ransomware a partir de características de ficheiros PE (Windows), seguindo a metodologia **CRISP-ML** e organizado em sprints **Scrum**.

A estrutura de serving (FastAPI + Docker) vem do template [Alex-Lekov/ml-fastapi](https://github.com/Alex-Lekov/ml-fastapi). O modelo que o template traz (CatBoost, dados de cancro da mama) é só um exemplo e será substituído por um modelo treinado com o dataset deste projeto.

## Estrutura do repositório

```
Grupo10-iaac/
├── app/                        # API FastAPI do template
│   ├── main.py
│   ├── config_prod.yml
│   ├── models/                 # modelo de exemplo (CatBoost)
│   └── tests/                  # testes da API
├── data/
│   ├── raw/ransom.csv          # dataset original (21 752 linhas x 77 colunas)
│   └── prepared/               # saída do notebook de preparação
│       ├── train.csv
│       ├── test.csv
│       └── feature_sets.json
├── docs/backlog_scrum.xlsx     # Product Backlog, Sprint Backlog e rituais Scrum
├── notebooks/
│   ├── 01_data_preparation.ipynb   # preparação dos dados (deste projeto)
│   ├── fit_sample_model.ipynb      # exemplo do template
│   └── use_sample.ipynb            # exemplo do template
├── Dockerfile
├── docker-compose.yml
├── requirements.txt            # dependências da API (Docker)
├── requirements-dev.txt        # dependências dos notebooks
├── LICENSE                     # GPL-3.0
└── README.md
```

## Dados

- **`data/raw/ransom.csv`**: 21 752 observações (10 876 `Benign` + 10 876 `Malware`), com as colunas-alvo `Class`, `Category` (Benign, Ransomware, RAT, Stealer, Trojan) e `Family` (26 famílias de malware + Benign). Inclui features estáticas do cabeçalho PE e contadores dinâmicos de sandbox.
- **`data/prepared/`**: resultado de `notebooks/01_data_preparation.ipynb`.
  - `train.csv` (17 960 linhas) e `test.csv` (3 679 linhas): features + alvos + `group`, `group_size`, `label_conflict_static` (e `cv_fold`/`family_fold` só no treino).
  - `feature_sets.json`: conjunto **A** (estático, 165 features, para bloqueio em tempo real), **B** (estático + dinâmico, 186 features, para triagem) e `dynamic_only` (21 features).

**Regras de uso:** treinar com `train.csv`, validar com `cv_fold` (ou `family_fold` para famílias novas) e usar `test.csv` **só na avaliação final**. Os grupos anti-fuga garantem que o mesmo binário nunca está em treino e teste. Reportar `Family` com a ressalva de que algumas famílias têm muito poucos grupos distintos.

## Notebooks (VS Code)

1. Abrir a pasta do repositório no VS Code (*File > Open Folder*).
2. Criar e ativar um ambiente virtual:
```bash
   python -m venv .venv
   # Windows:  .venv\Scripts\activate
   # Linux/macOS:  source .venv/bin/activate
   pip install -r requirements-dev.txt
```
3. Abrir `notebooks/01_data_preparation.ipynb` e escolher o kernel `.venv`. Os caminhos são relativos à pasta `notebooks/`, que é o diretório de trabalho por defeito no VS Code.

## API

### Com Docker
```bash
docker-compose up --build
```

### Localmente
```bash
pip install -r requirements.txt
cd app
python main.py
```
O endereço e a porta configuram-se em `app/config_prod.yml`.

Documentação interativa: http://localhost:8003/docs

Exemplo de pedido (modelo de exemplo do template):
```python
import requests

response = requests.post("http://localhost:8003/predict", json=input_data)
print(response.json())
```
O formato de `input_data` está documentado em `/docs`.

### Testes da API
```bash
cd app
pytest -v --disable-warnings
```

## Fluxo de trabalho Git

- `main`: versão estável; não se faz commit direto.
- Uma branch por pessoa/tarefa, por exemplo `feat/eda-univariada` ou `fix/split-agrupado`.
- Commits curtos e no imperativo (ex.: `feat: adicionar EDA bivariada`).
- Integração através de Pull Request revisto por, pelo menos, um colega.

## Gestão do projeto

O backlog está em `docs/backlog_scrum.xlsx` (folhas *Product Backlog*, *Sprint Backlog* e *Rituais Scrum*). Atualizar as colunas **Responsável** e **Status** ao longo de cada sprint.

## Créditos e licença

Código base do serving importado de [Alex-Lekov/ml-fastapi](https://github.com/Alex-Lekov/ml-fastapi). O repositório mantém a licença **GPL-3.0** (ficheiro `LICENSE`).