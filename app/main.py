"""API mínima (placeholder) para servir o modelo de deteção de malware.

Ainda não há modelo treinado: este ficheiro só garante que o
`docker-compose up` arranca e que o endpoint /health responde.
Quando existir modelo, acrescentar aqui o endpoint /predict.
"""
import uvicorn
from fastapi import FastAPI

app = FastAPI(title="IAAC - Grupo 10 - Deteção de Ransomware/Malware")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
