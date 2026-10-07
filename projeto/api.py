"""API local de demonstração; contrato validado e modelo carregado no arranque."""
from contextlib import asynccontextmanager
import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from src.inferencia import Predictor, ROOT

class Pedido(BaseModel):
    flows: list[dict[str,float|int|str|None]] = Field(min_length=1,max_length=1000)

@asynccontextmanager
async def lifespan(app):
    app.state.predictor=Predictor(os.environ.get('TROJAN_MODEL',str(ROOT/'models/modelo_trojan.joblib')))
    yield

app=FastAPI(title='Deteção de trojans IAAC',version='1.0.0',lifespan=lifespan)

@app.get('/health')
def health():
    b=app.state.predictor.bundle
    return {'status':'ok','model':b['nome'],'deployment_approved':b['deployment_approved'],'mode':'demonstracao_local'}

@app.get('/schema')
def schema():
    b=app.state.predictor.bundle
    return {'required_columns':b['required_columns'],'threshold':b['limiar'],'positive_class':'Trojan'}

@app.post('/predict')
def predict(request:Pedido):
    try:
        result=app.state.predictor.predict(pd.DataFrame(request.flows))
    except ValueError as exc:
        raise HTTPException(status_code=422,detail=str(exc)) from exc
    return {'model':app.state.predictor.bundle['nome'],'predictions':result.to_dict(orient='records'),
            'deployment_approved':app.state.predictor.bundle['deployment_approved']}

@app.get('/',include_in_schema=False)
def dashboard(): return FileResponse(ROOT/'static/index.html')
