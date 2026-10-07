"""Experiência reproduzível: ajuste no treino, seleção na validação, teste reservado."""
from pathlib import Path
import argparse
import hashlib
import json
import time
import platform
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import VarianceThreshold
from sklearn.preprocessing import StandardScaler
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from threadpoolctl import threadpool_limits
from .preparacao import carregar, rotulos, metadados, FlowFeatures
from .avaliacao import separar, separar_aleatorio, metricas, escolher_limiar, bootstrap_auc_grupos
from .psi import tabela_psi

ROOT = Path(__file__).resolve().parents[1]

def guardar_json(path, obj):
    Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')

def candidatos():
    return {
        'trivial': DummyClassifier(strategy='prior'),
        'logistica': LogisticRegression(max_iter=1500,C=.1,random_state=42),
        'arvore': DecisionTreeClassifier(max_depth=10,min_samples_leaf=30,random_state=42),
        'rf': RandomForestClassifier(n_estimators=120,max_depth=16,min_samples_leaf=10,n_jobs=4,random_state=42),
        'hgb': HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=15,l2_regularization=10,early_stopping=False,random_state=42),
        'hgb_regularizado': HistGradientBoostingClassifier(max_iter=200,max_leaf_nodes=7,l2_regularization=30,learning_rate=.05,early_stopping=False,random_state=42),
        'hgb_sem_portas_host': HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=15,l2_regularization=10,early_stopping=False,random_state=42),
    }

def pipeline(nome, estimator):
    return Pipeline([('features',FlowFeatures(sem_portas=nome.endswith('sem_portas_host'),sem_host=nome.endswith('sem_portas_host'))),
                     ('imputar',SimpleImputer(strategy='median',keep_empty_features=True)),
                     ('variancia',VarianceThreshold()),
                     ('escala',StandardScaler() if nome=='logistica' else 'passthrough'),
                     ('modelo',estimator)])

def treinar(csv_path, destino=ROOT):
    destino=Path(destino); reports=destino/'reports'; models=destino/'models'
    reports.mkdir(exist_ok=True,parents=True); models.mkdir(exist_ok=True,parents=True)
    raw=carregar(csv_path); y=rotulos(raw); meta=metadados(raw)
    parts=separar(y,meta['Source IP']); tr,va,te=(parts[x] for x in ['treino','validacao','teste'])
    assignment=pd.DataFrame({'linha':np.arange(len(raw)),'conjunto':''})
    for name, rows in parts.items(): assignment.loc[rows,'conjunto']=name
    assignment.to_csv(reports/'split_indices.csv',index=False)
    split_info={name:{'n':len(rows),'benign':int((y.iloc[rows]==0).sum()),'trojan':int(y.iloc[rows].sum()),
                      'ips':int(meta.iloc[rows]['Source IP'].nunique())} for name,rows in parts.items()}
    guardar_json(reports/'splits.json',{'seed':42,'metodo':'GroupShuffleSplit por Source IP; 25% dos grupos para teste e 25% dos restantes para validação',
                                     'sobreposicao_source_ip':0,'conjuntos':split_info,
                                     'limite':'IP de destino e assinaturas de fluxo podem repetir; não prova generalização a todas as entidades.'})
    print('SPLITS',split_info,flush=True)
    fitted={}; rows=[]
    with threadpool_limits(limits=4):
        for name, estimator in candidatos().items():
            start=time.perf_counter(); model=pipeline(name,estimator); model.fit(raw.iloc[tr],y.iloc[tr])
            scores=model.predict_proba(raw.iloc[va])[:,1]; threshold=escolher_limiar(y.iloc[va],scores)
            result=metricas(y.iloc[va],scores,threshold)
            result.update(modelo=name,conjunto='validacao_grupos',tempo_treino_s=time.perf_counter()-start)
            rows.append(result); fitted[name]=(model,threshold)
            joblib.dump({'pipeline':model,'nome':name,'limiar':threshold,'schema_version':1},models/f'{name}.joblib',compress=3)
            print(name, {k:result[k] for k in ['auc_roc','recall','fpr','f1']},flush=True)
    comparison=pd.DataFrame(rows); comparison.to_csv(reports/'comparacao_validacao.csv',index=False)
    # O critério é pré-definido: recall sob FPR<=5%, depois AUC PR e ROC; nunca usa o teste.
    winner=comparison[comparison.modelo!='trivial'].sort_values(['recall','auc_pr','auc_roc'],ascending=False).iloc[0].modelo
    model,threshold=fitted[winner]
    with threadpool_limits(limits=4):
        val_scores=model.predict_proba(raw.iloc[va])[:,1]
        test_scores=model.predict_proba(raw.iloc[te])[:,1]
        test=metricas(y.iloc[te],test_scores,threshold)
        baseline=metricas(y.iloc[te],fitted['trivial'][0].predict_proba(raw.iloc[te])[:,1])
        ci=bootstrap_auc_grupos(y.iloc[te],test_scores,meta.iloc[te]['Source IP'])
        # Limiares explorados exclusivamente na validação.
        table=[metricas(y.iloc[va],val_scores,float(t)) for t in np.unique(np.r_[np.linspace(0,1,101),threshold])]
        pd.DataFrame(table).to_csv(reports/'limiares_validacao.csv',index=False)
        # Holdout aleatório é diagnóstico e fica fora da seleção.
        random_parts=separar_aleatorio(y); rd_train=random_parts['treino']; rd_test=random_parts['teste']
        random_model=pipeline('hgb',candidatos()['hgb']); random_model.fit(raw.iloc[rd_train],y.iloc[rd_train])
        random_metrics=metricas(y.iloc[rd_test],random_model.predict_proba(raw.iloc[rd_test])[:,1])
        # Interpretação descritiva do teste; nunca usada para voltar a escolher features/modelos.
        subset=raw.iloc[te].sample(min(3000,len(te)),random_state=42)
        selected=model.named_steps['features'].required_columns_
        imp=permutation_importance(model,subset[selected],y.loc[subset.index],scoring='roc_auc',n_repeats=3,random_state=42,n_jobs=1)
        pd.DataFrame({'feature':selected,'media_auc':imp.importances_mean,'desvio':imp.importances_std}).sort_values('media_auc',ascending=False).to_csv(reports/'importancia_permutacao.csv',index=False)
    transformed=model.named_steps['features'].transform(raw)
    days=sorted(meta.dia.unique()); ref=transformed[meta.dia==days[0]]; new=transformed[meta.dia==days[-1]]
    tabela_psi(ref,new).to_csv(reports/'psi_deriva.csv',index=False)
    frame=pd.DataFrame({'classe_real':y.iloc[te].to_numpy(),'score_trojan':test_scores,'alerta':test_scores>=threshold,
                        'dia':meta.iloc[te].dia.to_numpy()})
    frame.to_csv(reports/'predictions_teste.csv',index=False)
    per_day=[]
    for day, group in frame.groupby('dia'):
        item=metricas(group.classe_real,group.score_trojan,threshold); item['dia']=day; per_day.append(item)
    pd.DataFrame(per_day).to_csv(reports/'metricas_por_dia.csv',index=False)
    missing_days=meta.iloc[te].dia.nunique()
    # Projeção sob prevalência/amostragem do dataset, sem alegar volume real do SOC.
    total_per_day=len(raw)/meta.dia.nunique()
    projected=float((test_scores>=threshold).mean()*total_per_day)
    deployed=bool(test['recall']>=.9 and test['fpr']<=.05)
    features=model.named_steps['features']
    bundle={'pipeline':model,'nome':winner,'limiar':threshold,'schema_version':1,
            'required_columns':features.required_columns_,'test_metrics':test,'deployment_approved':deployed,
            'decision_policy':'revisao_manual','sklearn_version':sklearn.__version__}
    joblib.dump(bundle,models/'modelo_trojan.joblib',compress=3)
    # Mede preparação + inferência + decisão, por chamada individual (sem extração PCAP).
    samples=raw.iloc[te].sample(min(100,len(te)),random_state=42)
    durations=[]
    with threadpool_limits(limits=4):
        model.predict_proba(samples.iloc[:1])
        for i in range(len(samples)):
            start=time.perf_counter(); _=model.predict_proba(samples.iloc[[i]])[:,1]>=threshold
            durations.append((time.perf_counter()-start)*1000)
    result={'modelo':winner,'limiar':threshold,'validacao':metricas(y.iloc[va],val_scores,threshold),
            'teste':test,'baseline_teste':baseline,'auc_bootstrap_grupos':ci,'diagnostico_aleatorio_hgb':random_metrics,
            'criterio_original':{'recall_min':.90,'fpr_max':.05,'atingido_no_teste':deployed},
            'alertas_por_dia_projetados':projected,'dias_teste':int(missing_days),
            'latencia_ms':{'media':float(np.mean(durations)),'p95':float(np.quantile(durations,.95)),
                           'n':len(durations),'inclui':'transformação de estatísticas CSV, imputação, inferência e limiar; não captura PCAP'},
            'dataset_sha256':hashlib.sha256(Path(csv_path).read_bytes()).hexdigest(),
            'versoes':{'python':platform.python_version(),'sklearn':sklearn.__version__,'pandas':pd.__version__,'numpy':np.__version__},
            'politica':'Demonstração local e revisão manual; nunca bloqueia tráfego automaticamente.'}
    guardar_json(reports/'avaliacao_final.json',result)
    guardar_json(models/'schema.json',{'required_columns':features.required_columns_,'class_mapping':{'Benign':0,'Trojan':1},
                                      'sklearn_version':sklearn.__version__,'model':winner,'threshold':threshold})
    examples=destino/'examples'; examples.mkdir(exist_ok=True)
    raw.iloc[te[:5]][features.required_columns_].to_csv(examples/'fluxos_sem_rotulo.csv',index=False)
    guardar_json(examples/'pedido_api.json',{'flows':raw.iloc[te[:2]][features.required_columns_].to_dict(orient='records')})
    print('AVALIAÇÃO FINAL',json.dumps(result,ensure_ascii=False),flush=True)
    return result

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--dados',type=Path,default=ROOT/'data/Trojan_Detection.csv')
    args=parser.parse_args(); treinar(args.dados)

if __name__=='__main__': main()
