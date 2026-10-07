# Grupo 10 — IAAC: Deteção de Ransomware/Malware

Projeto de deteção de malware/ransomware a partir de características de ficheiros PE (Windows), seguindo a metodologia **CRISP-ML** e organizado em sprints **Scrum**.

## Estrutura do repositório

```
grupo 10 iaac/
├── app/                      # API FastAPI (placeholder com /health)
├── data/
│   ├── raw/ransom.csv        # dataset original (21 752 linhas x 77 colunas)
│   └── prepared/             # saída do notebook de preparação
│       ├── train.csv
│       ├── test.csv
│       └── feature_sets.json
├── docs/backlog_scrum.xlsx   # Product Backlog, Sprint Backlog e rituais Scrum
├── notebooks/
│   └── 01_data_preparation.ipynb
├── Dockerfile
├── docker-compose.yml
├── requirements.txt          # dependências da API (Docker)
├── requirements-dev.txt      # dependências dos notebooks
├── LICENSE                   # GPL-3.0
└── README.md
```

## Dados

- **`data/raw/ransom.csv`**: 21 752 observações (10 876 `Benign` + 10 876 `Malware`), com as colunas-alvo `Class`, `Category` (Benign, Ransomware, RAT, Stealer, Trojan) e `Family` (26 famílias de malware + Benign). Inclui features estáticas do cabeçalho PE e contadores dinâmicos de sandbox.
- **`data/prepared/`**: resultado de `notebooks/01_data_preparation.ipynb`.
  - `train.csv` (17 960 linhas) e `test.csv` (3 679 linhas): features + alvos + `group`, `group_size`, `label_conflict_static` (e `cv_fold`/`family_fold` só no treino).
  - `feature_sets.json`: conjunto **A** (estático, 165 features, para bloqueio em tempo real), **B** (estático + dinâmico, 186 features, para triagem) e `dynamic_only` (21 features).

**Regras de uso:** treinar com `train.csv`, validar com `cv_fold` (ou `family_fold` para famílias novas) e usar `test.csv` **só na avaliação final**. Os grupos anti-fuga garantem que o mesmo binário nunca está em treino e teste. Reportar `Family` com a ressalva de que algumas famílias têm muito poucos grupos distintos.

## Como começar (VS Code)

1. Abrir a pasta `grupo 10 iaac` no VS Code (*File > Open Folder*).
2. Criar e ativar um ambiente virtual:
   ```bash
   python -m venv .venv
   # Windows:  .venv\Scripts\activate
   # Linux/macOS:  source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```
3. Abrir `notebooks/01_data_preparation.ipynb` e escolher o kernel `.venv`. Os caminhos são relativos à pasta `notebooks/`, por isso o notebook deve correr com essa pasta como diretório de trabalho (comportamento por defeito do VS Code).

## API com Docker

```bash
docker-compose up --build
```

Documentação interativa em http://localhost:8003/docs e verificação em http://localhost:8003/health. Neste momento a API é apenas um esqueleto; o endpoint de predição será acrescentado quando houver modelo treinado.

## Fluxo de trabalho Git (US-20)

- `main`: versão estável; não se faz commit direto.
- Uma branch por pessoa/tarefa, por exemplo `feat/eda-univariada` ou `fix/split-agrupado`.
- Commits curtos e no imperativo (ex.: `feat: adicionar EDA bivariada`).
- Integração através de Pull Request revisto por, pelo menos, um colega.

## Gestão do projeto

O backlog está em `docs/backlog_scrum.xlsx` (folhas *Product Backlog*, *Sprint Backlog* e *Rituais Scrum*). Atualizar as colunas **Responsável** e **Status** ao longo de cada sprint.

## Créditos e licença

A estrutura de serving com FastAPI e Docker é baseada em [Alex-Lekov/ml-fastapi](https://github.com/Alex-Lekov/ml-fastapi). O repositório mantém a licença **GPL-3.0** (ficheiro `LICENSE`).
