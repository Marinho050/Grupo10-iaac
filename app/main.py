####################################### IMPORT #################################
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
import uuid
import pandas as pd
from pydantic import BaseModel, Field
import uvicorn
from loguru import logger
import sys
import joblib
import yaml
import os

####################################### logger #################################

logger.remove()
logger.add(
    sys.stderr,
    colorize=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
    level=10,
)
logger.add(
    "log.log", rotation="1 MB", level="DEBUG", compression="zip"
)

####################################### SETUP #################################

####### LOAD CONFIG ##################################
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config_prod.yml")
with open(CONFIG_PATH, "r") as ymlfile:
    config = yaml.load(ymlfile, Loader=yaml.SafeLoader)

VERSION = config["VERSION"]

# MODEL_DIR no config_prod.yml é relativo à pasta app/ (ex: '../models/'), não à pasta
# a partir de onde o processo é lançado — resolvemos sempre a partir da localização
# deste ficheiro, para funcionar tanto com "python app/main.py" como com pytest a
# partir da raiz do projeto.
MODEL_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), config["MODEL_DIR"]))

####################### Models ###########################################
# Deteção de conexões maliciosas — pipeline scikit-learn (pré-processamento + Random Forest)
# treinado em notebooks/Modelling_cybersecurity.ipynb.
bundle = joblib.load(os.path.join(MODEL_DIR, "model_final.joblib"))
pipeline = bundle["pipeline"]
THRESHOLD = bundle["threshold"]

###############################################################################
# FastAPI

app = FastAPI(
    title="Deteção de Conexões Maliciosas — IAAC Grupo 10",
    version=VERSION,
    description="API de deteção de conexões de rede maliciosas, a partir de features tipo NetFlow ⚡",
)


class PredictionInput(BaseModel):
    Protocol: str = Field(..., examples=["TCP"], description="Protocolo de rede: TCP, UDP ou ICMP")
    Packet_Size_Bytes: float = Field(..., ge=0, examples=[805])
    Connection_Duration_ms: float = Field(..., ge=0, examples=[120])
    Failed_Logins: int = Field(..., ge=0, examples=[0])
    Geo_Distance_km: float = Field(..., ge=0, examples=[1169])


class ResponseModel(BaseModel):
    prediction_Id: str
    predict: int
    predict_prob: float
    threshold: float


############################# Requests ##########################################################

@app.post("/predict", response_model=ResponseModel, status_code=status.HTTP_200_OK)
async def prediction(input: PredictionInput):
    """Classifica uma conexão de rede como maliciosa (1) ou benigna (0).

    Args:
        input (PredictionInput): Features da conexão (Protocol, Packet_Size_Bytes,
            Connection_Duration_ms, Failed_Logins, Geo_Distance_km).

    Returns:
        dict: Classe prevista, probabilidade de ser maliciosa e o threshold usado.
    """
    result = {
        "prediction_Id": str(uuid.uuid4()),
        "predict": 0,
        "predict_prob": 0.0,
        "threshold": THRESHOLD,
    }

    logger.info(input.dict())

    row = pd.DataFrame([input.dict()])
    # mesma feature engineering do notebook de Data Preparation
    row["High_Failed_Logins"] = (row["Failed_Logins"] >= 3).astype(int)

    proba = float(pipeline.predict_proba(row)[0, 1])
    result["predict_prob"] = proba
    result["predict"] = int(proba >= THRESHOLD)

    logger.info(result)
    return result


@app.get("/", include_in_schema=False)
async def redirect():
    return RedirectResponse("/docs")


@app.get("/health")
async def service_health():
    """Return service health"""
    return {"ok"}


########################## MAIN ###########################################################
###########################################################################################

if __name__ == "__main__":
    ######################## START ###########################################
    uvicorn.run(app, host=config["HOST"], port=config["PORT"])
