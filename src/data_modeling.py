"""
data_modeling.py
=================

Etapa de Modelação (CRISP-ML(Q)) do projeto de Deteção de Conexões Maliciosas
(IAAC — Grupo 10).

Compara Regressão Logística vs. Random Forest por validação cruzada (5-fold,
só no treino), escolhe o melhor por PR-AUC, afina o threshold de decisão na
validação (recall >= 90%, falsos positivos <= 1% — ver
`business_understanding.py`) e guarda o modelo final treinado.

Corresponde à secção 1-3 de `notebooks/Modelling_cybersecurity.ipynb`, em
formato de script reutilizável. A avaliação final no conjunto de teste fica
em `evaluation.py` (separada de propósito: o teste só deve ser tocado uma
única vez, depois de o modelo e o threshold estarem decididos).

Uso:
    python src/data_modeling.py [--data CAMINHO_PARA_O_CSV] [--out CAMINHO_DO_MODELO]
"""

import argparse
import os

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix,
                              make_scorer, precision_recall_curve, precision_score,
                              recall_score)
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline

from business_understanding import SUCCESS_CRITERIA
from data_preparation import DEFAULT_DATA_PATH, build_preprocessor, prepare

DEFAULT_MODEL_OUT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "models", "model_final.joblib")
)

CANDIDATE_MODELS = {
    "Logistic Regression": LogisticRegression(class_weight="balanced", max_iter=2000, random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=200, class_weight="balanced",
                                             random_state=42, n_jobs=-1),
}

CV_SCORING = {
    "recall": make_scorer(recall_score),
    "precision": make_scorer(precision_score, zero_division=0),
    "roc_auc": "roc_auc",
    "pr_auc": "average_precision",
}


def compare_models(X_train, y_train, n_splits: int = 5, random_state: int = 42) -> dict:
    """Validação cruzada estratificada dos modelos candidatos. Devolve, por
    modelo, as métricas médias/desvio-padrão de cada fold."""
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    preprocessor = build_preprocessor()

    results = {}
    for name, clf in CANDIDATE_MODELS.items():
        pipe = Pipeline([("preprocess", preprocessor), ("model", clf)])
        res = cross_validate(pipe, X_train, y_train, cv=cv, scoring=CV_SCORING, n_jobs=-1)
        results[name] = {
            "mean": {k: float(res[f"test_{k}"].mean()) for k in CV_SCORING},
            "std": {k: float(res[f"test_{k}"].std()) for k in CV_SCORING},
        }
    return results


def select_best_model(cv_results: dict, metric: str = "pr_auc") -> str:
    return max(cv_results, key=lambda name: cv_results[name]["mean"][metric])


def fit_final_pipeline(model_name: str, X_train, y_train) -> Pipeline:
    preprocessor = build_preprocessor()
    pipe = Pipeline([("preprocess", preprocessor), ("model", CANDIDATE_MODELS[model_name])])
    pipe.fit(X_train, y_train)
    return pipe


def tune_threshold(pipe: Pipeline, X_val, y_val,
                    min_recall: float = SUCCESS_CRITERIA.min_recall,
                    max_fp_rate: float = SUCCESS_CRITERIA.max_fp_rate) -> dict:
    """Escolhe, entre os thresholds que cumprem os dois critérios de sucesso
    na validação, o mais preciso (= menos alertas falsos). Se nenhum cumprir
    ambos, cai para o que maximiza recall sujeito a FP <= max_fp_rate."""
    val_proba = pipe.predict_proba(X_val)[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_val, val_proba)

    def fp_rate_at(threshold):
        y_pred = (val_proba >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_val, y_pred).ravel()
        return fp / (fp + tn)

    candidates = [
        (t, r, fp_rate_at(t), p)
        for p, r, t in zip(precisions[:-1], recalls[:-1], thresholds)
        if r >= min_recall and fp_rate_at(t) <= max_fp_rate
    ]

    if candidates:
        best_t, best_r, best_fp, best_p = max(candidates, key=lambda c: c[3])
    else:
        fallback = [
            (t, r, fp_rate_at(t), p)
            for p, r, t in zip(precisions[:-1], recalls[:-1], thresholds)
            if fp_rate_at(t) <= max_fp_rate
        ]
        best_t, best_r, best_fp, best_p = max(fallback, key=lambda c: c[1])

    return {"threshold": float(best_t), "recall": float(best_r),
            "fp_rate": float(best_fp), "precision": float(best_p)}


def train(path: str = DEFAULT_DATA_PATH) -> dict:
    """Pipeline completo de modelação: comparação, treino do melhor modelo e
    afinação do threshold. Não toca no conjunto de teste (ver evaluation.py)."""
    X_train, X_val, X_test, y_train, y_val, y_test = prepare(path)

    cv_results = compare_models(X_train, y_train)
    best_name = select_best_model(cv_results)
    pipe = fit_final_pipeline(best_name, X_train, y_train)
    threshold_info = tune_threshold(pipe, X_val, y_val)

    return {
        "cv_results": cv_results,
        "best_model_name": best_name,
        "pipeline": pipe,
        "threshold_info": threshold_info,
    }


def save_bundle(pipe: Pipeline, threshold: float, model_name: str, out_path: str = DEFAULT_MODEL_OUT):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    joblib.dump({
        "pipeline": pipe,
        "threshold": threshold,
        "model_name": model_name,
        "feature_engineering": "add High_Failed_Logins = Failed_Logins >= 3",
    }, out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Comparação de modelos, treino e afinação de threshold.")
    parser.add_argument("--data", default=DEFAULT_DATA_PATH, help="Caminho para o CSV.")
    parser.add_argument("--out", default=DEFAULT_MODEL_OUT, help="Caminho de saída do modelo final (.joblib).")
    args = parser.parse_args()

    result = train(args.data)

    print("=== Comparação de modelos (5-fold CV, no treino) ===")
    for name, metrics in result["cv_results"].items():
        m = metrics["mean"]
        print(f"{name:22s} recall={m['recall']:.4f}  precisão={m['precision']:.4f}  "
              f"roc_auc={m['roc_auc']:.4f}  pr_auc={m['pr_auc']:.4f}")

    print(f"\nModelo escolhido (maior PR-AUC): {result['best_model_name']}")

    t = result["threshold_info"]
    print("\n=== Threshold afinado na validação ===")
    print(f"threshold={t['threshold']:.3f}  recall={t['recall']:.4f}  "
          f"precisão={t['precision']:.4f}  taxa_FP={t['fp_rate']:.4%}")

    save_bundle(result["pipeline"], t["threshold"], result["best_model_name"], args.out)
    print(f"\nModelo final guardado em: {args.out}")
