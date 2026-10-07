"""Serviço comum ao CLI, API e notebook; não necessita da coluna Class."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from threadpoolctl import threadpool_limits
from .preparacao import normalizar
ROOT=Path(__file__).resolve().parents[1]

class Predictor:
    def __init__(self,path=ROOT/'models/modelo_trojan.joblib'):
        # Apenas artefactos locais do projeto, nunca ficheiros submetidos pela API.
        self.bundle=joblib.load(path)
        if self.bundle.get('schema_version')!=1:
            raise ValueError('Versão de esquema não suportada.')
        if self.bundle.get('sklearn_version',sklearn.__version__)!=sklearn.__version__:
            raise ValueError('A versão scikit-learn difere do treino; instalar requirements-lock.txt.')

    def predict(self,df,threshold=None):
        df=normalizar(df)
        if len(df)==0: raise ValueError('O pedido não contém fluxos.')
        t=self.bundle['limiar'] if threshold is None else threshold
        if not np.isfinite(t) or not 0<=t<=1:
            raise ValueError('O limiar deve estar entre 0 e 1.')
        with threadpool_limits(limits=4):
            scores=self.bundle['pipeline'].predict_proba(df)[:,1]
        out=pd.DataFrame({'score_trojan':scores,'alerta':scores>=t,'acao':np.where(scores>=t,'revisao_manual','sem_alerta')})
        if 'Flow ID' in df: out.insert(0,'Flow ID',df['Flow ID'].to_numpy())
        return out
