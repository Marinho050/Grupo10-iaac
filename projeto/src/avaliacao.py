"""Separação por entidades e métricas com semântica explícita."""
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.metrics import (confusion_matrix, roc_auc_score, average_precision_score,
                             accuracy_score, precision_score, recall_score, f1_score, roc_curve, brier_score_loss)

def separar(y, grupos, seed=42):
    idx = np.arange(len(y))
    dev, test = next(GroupShuffleSplit(test_size=.25, random_state=seed).split(idx, y, grupos))
    train0, val0 = next(GroupShuffleSplit(test_size=.25, random_state=seed+1).split(dev, y.iloc[dev], grupos.iloc[dev]))
    parts = {'treino': dev[train0], 'validacao': dev[val0], 'teste': test}
    for name, rows in parts.items():
        if y.iloc[rows].nunique() != 2:
            raise ValueError(f'{name} não contém as duas classes; rever a estratégia sem escolher pelo desempenho.')
    for a,b in [('treino','validacao'),('treino','teste'),('validacao','teste')]:
        if set(grupos.iloc[parts[a]]) & set(grupos.iloc[parts[b]]):
            raise AssertionError('Sobreposição de IPs entre conjuntos.')
    return parts

def separar_aleatorio(y, seed=42):
    dev, test = train_test_split(np.arange(len(y)), test_size=.25, stratify=y, random_state=seed)
    train, val = train_test_split(dev, test_size=.25, stratify=y.iloc[dev], random_state=seed+1)
    return {'treino':train, 'validacao':val, 'teste':test}

def metricas(y, scores, limiar=.5):
    scores = np.asarray(scores, dtype=float)
    pred = scores >= limiar
    tn,fp,fn,tp = confusion_matrix(y, pred, labels=[0,1]).ravel()
    both = len(np.unique(y)) == 2
    return {'n': len(y), 'trojan': int(np.sum(y)), 'limiar':float(limiar),
            'auc_roc':float(roc_auc_score(y,scores)) if both else None,
            'auc_pr':float(average_precision_score(y,scores)) if both else None,
            'exatidao':float(accuracy_score(y,pred)), 'recall':float(recall_score(y,pred,zero_division=0)),
            'precisao':float(precision_score(y,pred,zero_division=0)), 'f1':float(f1_score(y,pred,zero_division=0)),
            'fpr':float(fp/(fp+tn)) if fp+tn else None, 'tn':int(tn), 'fp':int(fp), 'fn':int(fn), 'tp':int(tp),
            'brier':float(brier_score_loss(y,scores)), 'alertas':int(np.sum(pred))}

def escolher_limiar(y, scores, max_fpr=.05):
    """Maximiza recall respeitando FPR na validação. O teste nunca escolhe o limiar."""
    fpr, tpr, thresholds = roc_curve(y, scores, drop_intermediate=False)
    valid = np.flatnonzero(fpr <= max_fpr)
    best = valid[np.argmax(tpr[valid])]
    threshold = float(thresholds[best])
    return threshold if np.isfinite(threshold) else float(np.nextafter(max(scores), np.inf))

def bootstrap_auc_grupos(y, scores, groups, repetitions=300, seed=42):
    """Reamostra IPs inteiros, reconhecendo a dependência entre fluxos do mesmo IP."""
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame({'y':np.asarray(y), 'score':scores, 'g':np.asarray(groups)})
    chunks = {g: x for g,x in frame.groupby('g')}
    keys = list(chunks)
    aucs = []
    for _ in range(repetitions):
        sample = pd.concat([chunks[keys[i]] for i in rng.integers(0,len(keys),len(keys))])
        if sample.y.nunique() == 2:
            aucs.append(roc_auc_score(sample.y,sample.score))
    return {'ci95':np.quantile(aucs,[.025,.975]).tolist() if aucs else None,
            'replicacoes_validas':len(aucs), 'unidade':'Source IP', 'n_grupos':len(keys)}
