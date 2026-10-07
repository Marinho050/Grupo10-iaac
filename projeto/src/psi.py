"""PSI com extremos abertos e suporte a features constantes e valores em falta."""
import numpy as np
import pandas as pd

def psi(ref, novo, n_bins=10):
    ref, novo = np.asarray(ref,dtype=float), np.asarray(novo,dtype=float)
    def counts(x, edges):
        finite = x[np.isfinite(x)]
        return np.r_[np.histogram(finite,bins=edges)[0],len(x)-len(finite)].astype(float)
    finite = ref[np.isfinite(ref)]
    if len(ref)==0 or len(novo)==0 or len(finite)==0:
        raise ValueError('PSI exige amostras não vazias e referência com valores finitos.')
    if np.ptp(finite)==0:
        v = float(finite[0]); edges=np.array([-np.inf,v,np.nextafter(v,np.inf),np.inf])
    else:
        cuts=np.unique(np.quantile(finite,np.linspace(0,1,n_bins+1)))[1:-1]
        edges=np.r_[-np.inf,cuts,np.inf]
    a,b=counts(ref,edges),counts(novo,edges)
    a=(a+.5)/(a.sum()+.5*len(a)); b=(b+.5)/(b.sum()+.5*len(b))
    return float(np.sum((b-a)*np.log(b/a)))

def tabela_psi(ref, novo):
    return pd.DataFrame([{'feature':c,'psi':psi(ref[c],novo[c])} for c in ref.columns]).sort_values('psi',ascending=False)
