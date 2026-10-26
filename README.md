# 🛡️ Sistema de Deteção de Phishing com Machine Learning & FastAPI

Este projeto consiste numa solução completa de cibersegurança para deteção automatizada de e-mails de *phishing*. A aplicação combina um modelo de Aprendizagem Automática (*Random Forest Classifier*) com uma API REST em **FastAPI** e uma interface web interativa.

---

## 🚀 Tecnologias Utilizadas

- **Linguagem:** Python 3.14
- **Backend / API:** FastAPI, Uvicorn, Pydantic
- **Machine Learning:** Scikit-Learn (Random Forest), Pandas, Joblib
- **Visualização de Dados:** Matplotlib, Seaborn
- **Frontend:** HTML5, CSS3, JavaScript (Fetch API)
- **Desenvolvimento Interativo:** Jupyter Notebook

---

## 📁 Estrutura do Projeto

```text
Grupo10-iaac-1/
├── app/
│   ├── main.py                    # Servidor FastAPI e Interface Web (UI)
│   └── random_forest_phishing.pkl # Modelo treinado exportado
├── data/
│   └── phishing_emails.csv        # Dataset utilizado para treino
├── notebooks/
│   └── treino_phishing.ipynb      # Notebook de treino, métricas e Matriz de Confusão
├── requirements.txt               # Dependências do projeto
└── README.md                      # Documentação do projeto
```

---

## ⚙️ Instalação e Configuração

### 1. Clonar o Repositório e Aceder à Pasta
```bash
git clone <URL_DO_REPOSITORIO>
cd Grupo10-iaac-1
```

### 2. Ativar o Ambiente Virtual (`venv`)
- **Windows (CMD / PowerShell):**
  ```cmd
  .\venv\Scripts\activate
  ```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

---

## 🧠 Treino e Avaliação do Modelo

O treino da inteligência artificial está documentado de forma interativa no ficheiro `notebooks/treino_phishing.ipynb`.

O pipeline realiza:
1. Carregamento e exploração dos dados (`phishing_emails.csv`).
2. Divisão dos dados em conjuntos de Treino (80%) e Teste (20%).
3. Treino do algoritmo **Random Forest** (`n_estimators=100`).
4. Avaliação de métricas (Precisão, *Recall*, *F1-Score*) e geração da **Matriz de Confusão**.
5. Exportação automática do modelo otimizado para `app/random_forest_phishing.pkl`.

---

## 🖥️ Como Executar a Aplicação

1. Navega para a pasta da aplicação:
   ```bash
   cd app
   ```

2. Inicia o servidor Uvicorn:
   ```bash
   uvicorn main:app --reload
   ```

3. Acede às interfaces no teu navegador:
   - **Interface Gráfica (Web UI):** [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - **Documentação Swagger (API REST):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **Documentação ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📊 Exemplo de Utilização da API (`POST /predict`)

### Entrada (JSON):
```json
{
  "has_link": 1,
  "has_attachment": 0,
  "urgency_score": 8,
  "spelling_errors": 4,
  "email_length_words": 120
}
```

### Saída (JSON):
```json
{
  "prediction_id": "aca6977b-d0eb-4307-8d95-8ff30927fd51",
  "is_phishing": true,
  "phishing_probability": 0.87
}
```