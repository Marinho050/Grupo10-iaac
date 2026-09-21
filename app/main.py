####################################### IMPORT #################################
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
import uuid
import pandas as pd
import numpy as np
from typing import Union
from pydantic import BaseModel, Field
import uvicorn
from loguru import logger
import sys
from catboost import CatBoostClassifier
import yaml


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
with open("config_prod.yml", 'r') as ymlfile:
    config = yaml.load(ymlfile, Loader=yaml.SafeLoader)

MODEL_DIR = config['MODEL_DIR']
VERSION = config['VERSION']


####################### Models ###########################################
# MODEL
model = CatBoostClassifier()      # parameters not required.
model.load_model(f'{MODEL_DIR}catboost_model_{VERSION}.cbm')

###############################################################################
# FastAPI

app = FastAPI(
    title="Sample API for ML Model Serving",
    version=VERSION,
    description="Based on ML with FastAPI Serving ⚡",
)

class PredictionInput(BaseModel):
    mean_radius: float
    mean_texture: float
    mean_perimeter: float
    mean_area: float
    mean_smoothness: float
    mean_compactness: float
    mean_concavity: float
    mean_concave_points: float
    mean_symmetry: float
    mean_fractal_dimension: float
    radius_error: float
    texture_error: float
    perimeter_error: float
    area_error: float
    smoothness_error: float
    compactness_error: float
    concavity_error: float
    concave_points_error: float
    symmetry_error: float
    fractal_dimension_error: float
    worst_radius: float
    worst_texture: float
    worst_perimeter: float
    worst_area: float
    worst_smoothness: float
    worst_compactness: float
    worst_concavity: float
    worst_concave_points: float
    worst_symmetry: float
    worst_fractal_dimension: float


class ResponseModel(BaseModel):
    prediction_Id: str
    predict: int
    predict_prob: Union[float, None]

############################# Requests ##########################################################

@app.post("/predict", response_model=ResponseModel, status_code=status.HTTP_200_OK)
async def prediction(input: PredictionInput):
    """Predicts the class and probability of the input data.

    Args:
        input (PredictionInput): Input data.

    Returns:
        dict: Predicted class and probability.
    """
    result = {
        "prediction_Id": str(uuid.uuid4()),
        "predict": 0,
        "predict_prob": 0.0,
        }
    
    logger.info(input.dict())

    # convert input to numpy array and select features
    input_data = np.array([input.dict()[feature] for feature in model.feature_names_])

    # predict class and probability
    result['predict'] = model.predict(input_data).item()
    result['predict_prob'] = model.predict_proba(input_data)[1]

    logger.info(result)
    return result


@app.get("/", include_in_schema=False)
async def redirect():
    return RedirectResponse("/docs")


@app.get('/health')
async def service_health():
    """Return service health"""
    return {"ok"}


########################## MAIN ###########################################################
###########################################################################################

if __name__ == "__main__":
    ######################## START ###########################################
    uvicorn.run(app, host=config['HOST'], port=config['PORT'])