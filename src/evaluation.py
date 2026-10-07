"""
evaluation.py
=============

Etapa de Avaliação (CRISP-ML(Q)) do projeto de Deteção de Conexões Maliciosas
(IAAC — Grupo 10).

Carrega o modelo final (treinado por `data_modeling.py`) e avalia-o **uma
única vez** no conjunto de teste — nunca usado até este ponto, nem para
escolher o modelo nem para afinar o threshold, para que a avaliação não
esteja enviesada.

Corresponde à secção 4-5 de `notebooks/Modelling_cybersecurity.ipynb`.

Uso:
    python src/evaluation.py [--data CAMINHO_PARA_O_CSV] [--model CAMINHO_DO_MODELO]
"""

import argparse
import os

import joblib
from sklearn.metrics import (average_precision_score, confusion_matrix,
                              precision_score, recall_score, roc_auc_score)

from business_understanding import SUCCESS_CRITERIA, expected_cost
from data_modeling import DEFAULT_MODEL_OUT
from data_preparation import DEFAULT_DATA_PATH, prepare


def evaluate(model_path: str = DEFAULT_MODEL_OUT, data_path: str = DEFAULT_DATA_PATH) -> dict:
    """Avalia o modelo guardado em `model_path` no conjunto de teste.

    Reconstrói o mesmo split (mesma seed) que `data_preparation.prepare` usou
    para treinar o modelo, por isso X_test/y_test aqui são exatamente os
    mesmos 3.750 registos nunca usados em treino, validação ou afinação de
    threshold.
    """
    bundle = joblib.load(model_path)
    pipeline = bundle["pipeline"]
    threshold = bundle["threshold"]

    _, _, X_test, _, _, y_test = prepare(data_path)

    test_proba = pipeline.predict_proba(X_test)[:, 1]
    y_pred = (test_proba >= threshold).astype(int)

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    fp_rate = fp / (fp + tn)
    recall = recall_score(y_test, y_pred)

    metrics = {
        "model_name": bundle.get("model_name", "desconhecido"),
        "threshold": threshold,
        "recall": float(recall),
        "precision": float(precision_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, test_proba)),
        "pr_auc": float(average_precision_score(y_test, test_proba)),
        "fp_rate": float(fp_rate),
        "confusion_matrix": cm.tolist(),
        "n_test": int(len(y_test)),
        "n_false_negatives": int(fn),
        "n_false_positives": int(fp),
        "success_criteria_met": SUCCESS_CRITERIA.is_met(recall, fp_rate),
        "expected_cost_eur": expected_cost(int(fn), int(fp)),
    }
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Avaliação final do modelo no conjunto de teste.")
    parser.add_argument("--data", default=DEFAULT_DATA_PATH, help="Caminho para o CSV.")
    parser.add_argument("--model", default=DEFAULT_MODEL_OUT, help="Caminho do modelo final (.joblib).")
    args = parser.parse_args()

    m = evaluate(args.model, args.data)

    print("=== Avaliação final — conjunto de teste (usado uma única vez) ===")
    print(f"Modelo: {m['model_name']}  |  threshold: {m['threshold']:.3f}")
    print(f"N (teste): {m['n_test']}  |  FN: {m['n_false_negatives']}  |  FP: {m['n_false_positives']}")
    print(f"Recall:    {m['recall']:.4f}")
    print(f"Precisão:  {m['precision']:.4f}")
    print(f"ROC-AUC:   {m['roc_auc']:.4f}")
    print(f"PR-AUC:    {m['pr_auc']:.4f}")
    print(f"Taxa de FP:{m['fp_rate']:.4%}")
    print(f"Matriz de confusão:\n{m['confusion_matrix']}")
    print(f"\nCusto esperado no teste: {m['expected_cost_eur']:.0f} EUR")
    print(f"Critérios de sucesso cumpridos (recall>=90%, FP<=1%): {m['success_criteria_met']}")
