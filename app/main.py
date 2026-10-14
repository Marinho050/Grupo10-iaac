import uuid
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Inicialização com metadados claros
app = FastAPI(title="Phishing Detection API", version="1.1")

# Carregamento seguro do modelo
try:
    model = joblib.load('random_forest_phishing.pkl')
except FileNotFoundError:
    model = None
    print("Aviso: Modelo 'random_forest_phishing.pkl' não encontrado.")

# Esquema de dados com validação de limites (Segurança)
class EmailInput(BaseModel):
    has_link: int = Field(..., ge=0, le=1, description="0 (Não) ou 1 (Sim)")
    has_attachment: int = Field(..., ge=0, le=1, description="0 (Não) ou 1 (Sim)")
    urgency_score: int = Field(..., ge=0, le=10, description="Escala de urgência de 0 a 10")
    spelling_errors: int = Field(..., ge=0, description="Número total de erros ortográficos")
    email_length_words: int = Field(..., gt=0, description="Número de palavras (> 0)")

@app.get("/")
def health_check():
    """
    Endpoint de verificação de estado da API.
    Retorna uma mensagem simples para confirmar que o servidor Uvicorn está online.
    """
    return {"status": "online", "message": "API de Deteção de Phishing operacional."}

@app.post("/predict")
def predict(data: EmailInput):
    """
    Recebe as 5 métricas de um e-mail validadas pelo Pydantic,
    transforma-as num DataFrame e utiliza o modelo Random Forest 
    para prever a probabilidade de ser phishing.
    """
    if model is None:
        raise HTTPException(status_code=500, detail="Modelo não disponível no servidor.")
    
    input_data = pd.DataFrame([data.model_dump()])
    
    prediction = int(model.predict(input_data)[0])
    prediction_prob = round(float(model.predict_proba(input_data)[0][1]), 4)
    
    return {
        "prediction_id": str(uuid.uuid4()),
        "is_phishing": bool(prediction),
        "phishing_probability": prediction_prob
    }