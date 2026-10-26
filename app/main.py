from fastapi.responses import HTMLResponse
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

@app.get("/", response_class=HTMLResponse, summary="Interface Gráfica")
def interface_grafica():
    html_content = """
    <!DOCTYPE html>
    <html lang="pt">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sistema Anti-Phishing</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .container { background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
            h2 { color: #1a73e8; text-align: center; margin-bottom: 20px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; font-weight: bold; margin-bottom: 5px; color: #333; }
            input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background-color: #1a73e8; color: white; border: none; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.3s; }
            button:hover { background-color: #1557b0; }
            #resultado { margin-top: 20px; padding: 15px; border-radius: 5px; text-align: center; font-weight: bold; display: none; }
            .legitimo { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .phishing { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        </style>
    </head>
    <body>

    <div class="container">
        <h2>Detetor de Phishing</h2>
        
        <div class="form-group">
            <label>Tem Link? (0 = Não, 1 = Sim)</label>
            <input type="number" id="has_link" min="0" max="1" value="1">
        </div>
        <div class="form-group">
            <label>Tem Anexo? (0 = Não, 1 = Sim)</label>
            <input type="number" id="has_attachment" min="0" max="1" value="0">
        </div>
        <div class="form-group">
            <label>Nível de Urgência (0 a 10)</label>
            <input type="number" id="urgency_score" min="0" max="10" value="5">
        </div>
        <div class="form-group">
            <label>Erros Ortográficos</label>
            <input type="number" id="spelling_errors" min="0" value="2">
        </div>
        <div class="form-group">
            <label>Tamanho (Nº de Palavras)</label>
            <input type="number" id="email_length_words" min="1" value="150">
        </div>
        
        <button onclick="fazerPredicao()">Analisar E-mail</button>

        <div id="resultado"></div>
    </div>

    <script>
        async function fazerPredicao() {
            const dados = {
                has_link: parseInt(document.getElementById('has_link').value),
                has_attachment: parseInt(document.getElementById('has_attachment').value),
                urgency_score: parseInt(document.getElementById('urgency_score').value),
                spelling_errors: parseInt(document.getElementById('spelling_errors').value),
                email_length_words: parseInt(document.getElementById('email_length_words').value)
            };

            const resposta = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dados)
            });

            const resultado = await resposta.json();
            const divResultado = document.getElementById('resultado');
            
            divResultado.style.display = 'block';
            
            if (resultado.is_phishing) { 
                divResultado.className = 'phishing';
                divResultado.innerHTML = `⚠️ ALERTA: PHISHING DETETADO!<br>Probabilidade: ${(resultado.phishing_probability * 100).toFixed(1)}%`; 
            } else {
                divResultado.className = 'legitimo';
                divResultado.innerHTML = `✅ E-MAIL LEGÍTIMO<br>Probabilidade de Phishing: ${(resultado.phishing_probability * 100).toFixed(1)}%`; 
            }
        }
    </script>

    </body>
    </html>
    """
    return html_content

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