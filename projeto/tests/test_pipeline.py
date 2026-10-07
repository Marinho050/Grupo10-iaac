"""Casos de regressão para leakage, contrato, persistência, métricas e API."""
import json
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from src.preparacao import FlowFeatures,rotulos,normalizar
from src.modelacao import pipeline,ROOT
from src.avaliacao import separar,metricas,escolher_limiar
from src.psi import psi
from src.inferencia import Predictor

@pytest.fixture
def raw():
    return pd.DataFrame({'Flow Duration':[1.,2.,3.,4.,5.,6.], 'Flow Bytes/s':[0.,1.,2.,3.,4.,5.],
                         'Protocol':[6,17,6,17,6,17], 'Destination Port':[80,53,443,50000,80,53],
                         'Class':['Benign','Trojan']*3, 'Source IP':['a','b','c','d','e','f'],
                         'Timestamp':['01/01/2020 00:00:00']*6})

def test_no_label_needed_and_stable_categories(raw):
    f=FlowFeatures().fit(raw); full=f.transform(raw)
    single=f.transform(raw.iloc[:1].drop(columns=['Class','Source IP','Timestamp']))
    assert list(single)==list(full)
    assert not any(c in full for c in ['Class','Source IP','Timestamp','Destination Port'])

@pytest.mark.parametrize('column,value',[('Destination Port',-1),('Destination Port',65536),('Destination Port',1.5),('Protocol','bad'),('Flow Duration','bad')])
def test_invalid_values(raw,column,value):
    f=FlowFeatures().fit(raw); bad=raw.astype(object); bad.loc[0,column]=value
    with pytest.raises(ValueError): f.transform(bad)

def test_missing_schema_rejected(raw):
    f=FlowFeatures().fit(raw)
    with pytest.raises(ValueError,match='obrigatórias'): f.transform(raw.drop(columns=['Flow Duration']))

def test_imputer_uses_training_only(raw):
    tr=raw.iloc[:4].copy(); tr.loc[0,'Flow Duration']=np.nan
    m=pipeline('trivial',DummyClassifier(strategy='prior')).fit(tr,rotulos(tr))
    before=m.named_steps['imputar'].statistics_.copy()
    incoming=raw.iloc[4:].copy(); incoming['Flow Duration']=np.nan
    assert np.isfinite(m.predict_proba(incoming)).all()
    np.testing.assert_array_equal(before,m.named_steps['imputar'].statistics_)
    assert before[0]==3

def test_scores_independent_of_batch(raw):
    m=pipeline('trivial',DummyClassifier(strategy='prior')).fit(raw,rotulos(raw))
    np.testing.assert_allclose(m.predict_proba(raw)[:1],m.predict_proba(raw.iloc[:1]))

def test_duplicate_columns_rejected(raw):
    bad=pd.concat([raw,raw[['Protocol']]],axis=1)
    with pytest.raises(ValueError,match='duplicados'):normalizar(bad)

def test_bad_labels_rejected(raw):
    raw.loc[0,'Class']='unknown'
    with pytest.raises(ValueError):rotulos(raw)

def test_group_split():
    y=pd.Series([0,1]*100); groups=pd.Series(np.repeat(np.arange(100),2))
    parts=separar(y,groups)
    assert sum(map(len,parts.values()))==len(y)
    for a,b in [('treino','validacao'),('treino','teste'),('validacao','teste')]:
        assert not set(groups.iloc[parts[a]]) & set(groups.iloc[parts[b]])

def test_threshold_and_confusion():
    y=[0,0,1,1]; scores=[.1,.2,.8,.9]
    t=escolher_limiar(y,scores); m=metricas(y,scores,t)
    assert m['recall']==1 and m['fpr']==0
    assert m['tn']==m['tp']==2

def test_single_class_metrics():
    m=metricas([1,1],[.8,.9]); assert m['auc_roc'] is None and m['fpr'] is None

def test_psi_handles_out_of_range_and_constants():
    assert psi([1,2,3,4],[1,2,3,4])==pytest.approx(0)
    assert psi([1,2,3,4],[100,101,102,103])>.25
    assert psi([1,1,1,1],[2,2,2,2])>.25
    assert psi([1,1,1,1],[1,1,1,1])==pytest.approx(0)

def test_real_bundle_roundtrip_and_unlabeled():
    if not (ROOT/'models/modelo_trojan.joblib').exists(): pytest.skip('Treinar antes do teste de integração.')
    p=Predictor(); sample=pd.read_csv(ROOT/'examples/fluxos_sem_rotulo.csv')
    assert 'Class' not in sample
    result=p.predict(sample)
    assert len(result)==len(sample) and result.score_trojan.between(0,1).all()
    np.testing.assert_allclose(result.score_trojan.iloc[:1],p.predict(sample.iloc[:1]).score_trojan)
    with pytest.raises(ValueError):p.predict(sample,-.1)

def test_api():
    if not (ROOT/'models/modelo_trojan.joblib').exists(): pytest.skip('Treinar antes do teste da API.')
    from fastapi.testclient import TestClient
    from api import app
    with TestClient(app) as c:
        assert c.get('/health').status_code==200
        assert c.get('/').status_code==200
        request=json.loads((ROOT/'examples/pedido_api.json').read_text())
        assert c.post('/predict',json=request).status_code==200
        assert c.post('/predict',json={'flows':[{'Protocol':6}]}).status_code==422
        assert c.post('/predict',json={'flows':[]}).status_code==422
