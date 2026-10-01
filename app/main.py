import uuid
import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

# Inicializar a aplicação FastAPI
app = FastAPI(title="Phishing Detection API", version="1.0")

# Carregar o modelo treinado de Random Forest
# (Garante que o ficheiro .pkl está acessível no diretório correto)
model = joblib.load('random_forest_phishing.pkl')

# Definir a estrutura dos dados de entrada baseada nas caraterísticas reais do e-mail
class EmailInput(BaseModel):
    has_link: int
    has_attachment: int
    urgency_score: int
    spelling_errors: int
    email_length_words: int

@app.get("/")
def home():
    return {"message": "API de Deteção de Phishing a funcionar com sucesso!"}

@app.post("/predict")
def predict(data: EmailInput):
    # Converter os dados recebidos para um DataFrame do Pandas
    input_data = pd.DataFrame([data.dict()])
    
    # Executar a previsão e calcular a probabilidade
    prediction = int(model.predict(input_data)[0])
    prediction_prob = float(model.predict_proba(input_data)[0][1])
    
    # Gerar um ID único para o registo da predição
    prediction_id = str(uuid.uuid4())
    
    return {
        "prediction_Id": prediction_id,
        "predict": prediction,
        "predict_prob": prediction_prob
    }