"""Análise exploratória descritiva; os resultados não selecionam features no teste."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from .preparacao import carregar,rotulos,metadados,FlowFeatures
ROOT=Path(__file__).resolve().parents[1]

def analisar(path=ROOT/'data/Trojan_Detection.csv'):
    raw=carregar(path); y=rotulos(raw); meta=metadados(raw)
    out=ROOT/'reports'; figs=ROOT/'figs'; out.mkdir(exist_ok=True); figs.mkdir(exist_ok=True)
    numeric=raw.select_dtypes(include='number').drop(columns=['Unnamed: 0'],errors='ignore')
    numeric.describe().T.assign(assimetria=numeric.skew(),curtose=numeric.kurt()).to_csv(out/'eda_descritiva.csv')
    temporal=pd.crosstab(meta.dia,raw.Class); temporal.to_csv(out/'eda_distribuicao_por_dia.csv')
    pd.crosstab(raw.Protocol,raw.Class).to_csv(out/'eda_protocolos.csv')
    signatures=[c for c in raw if c not in ['Class','Timestamp','Unnamed: 0']]
    stats=raw.groupby(signatures,dropna=False,sort=False).Class.agg(['nunique','size'])
    conflicting=stats[stats['nunique']>1]
    engineered=FlowFeatures().fit_transform(raw)
    feature_keys=pd.util.hash_pandas_object(engineered,index=False)
    model_groups=pd.DataFrame({'assinatura':feature_keys,'y':y}).groupby('assinatura').y.agg(['size','nunique','sum'])
    feature_conflicts=model_groups[model_groups['nunique']>1]
    empirical_ceiling=float(np.maximum(model_groups['sum'],model_groups['size']-model_groups['sum']).sum()/len(raw))
    quality={'linhas':len(raw),'colunas':len(raw.columns),'classes':raw.Class.value_counts().to_dict(),
             'valores_em_falta':int(raw.isna().sum().sum()),'valores_infinitos':int(np.isinf(numeric.to_numpy()).sum()),
             'duplicados_sem_indice':int(raw.drop(columns=['Unnamed: 0'],errors='ignore').duplicated().sum()),
             'colunas_constantes':raw.columns[raw.nunique(dropna=False)==1].tolist(),
             'grupos_assinatura_com_rotulos_distintos':len(conflicting),'linhas_nesses_grupos':int(conflicting['size'].sum()),
             'definicao_assinatura':'Todas as colunas exceto Class, Timestamp e índice. Repetição de tráfego não prova erro de rótulo.',
             'grupos_features_com_rotulos_distintos':len(feature_conflicts),'linhas_nesses_grupos_features':int(feature_conflicts['size'].sum()),
             'teto_exatidao_empirico_features_identicas':empirical_ceiling,
             'nota_assinatura_features':'Hash das estatísticas transformadas sem IPs e Timestamp. Contextos distintos podem ter features idênticas; teto descritivo deste ficheiro, não limite populacional.',
             'dias':len(temporal),'inicio':meta.dia.min(),'fim':meta.dia.max(),
             'temporal_viavel_para_fpr':False,'motivo_temporal':'Dias recentes contêm apenas Trojan; sem negativos, FPR e ROC AUC não são estimáveis.',
             'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}
    (out/'qualidade_dados.json').write_text(json.dumps(quality,indent=2,ensure_ascii=False),encoding='utf-8')
    temporal.plot.bar(stacked=True,figsize=(10,5),color=['#2b6cb0','#c53030']); plt.ylabel('Fluxos'); plt.xlabel('Dia'); plt.tight_layout(); plt.savefig(figs/'distribuicao_por_dia.png',dpi=150); plt.close()
    counts=raw.Class.value_counts(); fig,ax=plt.subplots(figsize=(6,4)); ax.bar(counts.index,counts.values,color=['#c53030','#2b6cb0']); ax.set_ylabel('Fluxos'); ax.set_title('Distribuição das classes'); fig.tight_layout(); fig.savefig(figs/'classes.png',dpi=150); plt.close(fig)
    features=FlowFeatures().fit_transform(raw)
    useful=features.loc[:,features.nunique()>1].replace([np.inf,-np.inf],np.nan)
    for method in ['pearson','spearman']:
        corr=useful.corr(method=method); corr.to_csv(out/f'correlacao_{method}.csv')
        fig,ax=plt.subplots(figsize=(12,10)); image=ax.imshow(corr,vmin=-1,vmax=1,cmap='coolwarm');
        step=max(1,len(corr)//20); ax.set_xticks(range(0,len(corr),step),corr.columns[::step],rotation=90,fontsize=7); ax.set_yticks(range(0,len(corr),step),corr.index[::step],fontsize=7)
        ax.set_title('Correlação '+method); fig.colorbar(image,ax=ax); fig.tight_layout(); fig.savefig(figs/f'correlacao_{method}.png',dpi=150); plt.close(fig)
    top=['Flow Duration','Total Fwd Packets','Total Backward Packets','Init_Win_bytes_forward','min_seg_size_forward','Flow Bytes/s']
    fig,axes=plt.subplots(2,3,figsize=(12,7))
    for ax,c in zip(axes.flat,top):
        vals=features[c]; a=vals[y==0].dropna(); b=vals[y==1].dropna()
        ax.boxplot([a,b],tick_labels=['Benign','Trojan'],showfliers=False); ax.set_title(c,fontsize=9)
    fig.tight_layout(); fig.savefig(figs/'bivariada_boxplots.png',dpi=150); plt.close(fig)
    # PCA é somente visualização, ajustada numa amostra reprodutível.
    sample=useful.sample(min(15000,len(useful)),random_state=42)
    scaled=StandardScaler().fit_transform(SimpleImputer(strategy='median').fit_transform(sample))
    pca=PCA(n_components=2,random_state=42); coords=pca.fit_transform(scaled)
    fig,ax=plt.subplots(figsize=(8,6)); ax.scatter(coords[:,0],coords[:,1],c=y.loc[sample.index],s=3,alpha=.4,cmap='coolwarm'); ax.set_xlabel(f'PC1 {pca.explained_variance_ratio_[0]:.1%}'); ax.set_ylabel(f'PC2 {pca.explained_variance_ratio_[1]:.1%}'); fig.tight_layout(); fig.savefig(figs/'pca_2d.png',dpi=150); plt.close(fig)
    print(json.dumps(quality,ensure_ascii=False),flush=True); return quality

def main():
    p=argparse.ArgumentParser(); p.add_argument('--dados',type=Path,default=ROOT/'data/Trojan_Detection.csv'); args=p.parse_args(); analisar(args.dados)
if __name__=='__main__': main()
