"""
data_preparation.py
====================

Etapa de Data Preparation (CRISP-ML(Q)) do projeto de Deteção de Conexões
Maliciosas (IAAC — Grupo 10).

Expõe as funções reutilizáveis para o split estratificado, a feature
engineering (`High_Failed_Logins`) e o pipeline de pré-processamento
(`ColumnTransformer`), usadas por `data_modeling.py` e `evaluation.py` —
garante que o treino, a validação, o teste e a API (`app/main.py`) aplicam
sempre exatamente a mesma transformação.

Corresponde ao conteúdo de `notebooks/Data_Preparation_cybersecurity.ipynb`,
em formato de módulo importável.

Uso (como script, corre o pipeline e mostra os shapes resultantes):
    python src/data_preparation.py [--data CAMINHO_PARA_O_CSV]
"""

import argparse
import os

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

TARGET = "Is_Malicious"
NUM_COLS_LOG = ["Packet_Size_Bytes", "Geo_Distance_km"]
NUM_COLS_PLAIN = ["Connection_Duration_ms", "Failed_Logins"]
CAT_COLS = ["Protocol"]

RANDOM_STATE = 42

DEFAULT_DATA_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "datasets", "Raw", "cybersecurity_network_logs.csv")
)


def load_data(path: str = DEFAULT_DATA_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Feature engineering: Failed_Logins >= 3 é, isoladamente, o sinal mais
    forte do dataset (ver EDA) — explicitamo-lo como feature binária."""
    df = df.copy()
    df["High_Failed_Logins"] = (df["Failed_Logins"] >= 3).astype(int)
    return df


def plain_numeric_columns() -> list:
    return NUM_COLS_PLAIN + ["High_Failed_Logins"]


def split_data(df: pd.DataFrame, test_size: float = 0.30, val_fraction_of_temp: float = 0.50,
               random_state: int = RANDOM_STATE):
    """Split estratificado 70/15/15 (por omissão) em treino/validação/teste,
    preservando a prevalência da classe maliciosa em cada partição."""
    X = df.drop(columns=[TARGET])
    y = df[TARGET]

    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=val_fraction_of_temp, stratify=y_temp, random_state=random_state
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def build_preprocessor() -> ColumnTransformer:
    """ColumnTransformer: log1p + escalonamento nas variáveis muito
    assimétricas, escalonamento simples nas restantes, one-hot em Protocol.
    Deve ser ajustado (`fit`) só no conjunto de treino."""
    log_pipeline = Pipeline(steps=[
        ("impute", SimpleImputer(strategy="median")),
        ("log1p", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
        ("scale", StandardScaler()),
    ])

    plain_pipeline = Pipeline(steps=[
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])

    cat_pipeline = Pipeline(steps=[
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])

    return ColumnTransformer(transformers=[
        ("log_num", log_pipeline, NUM_COLS_LOG),
        ("plain_num", plain_pipeline, plain_numeric_columns()),
        ("cat", cat_pipeline, CAT_COLS),
    ])


def prepare(path: str = DEFAULT_DATA_PATH, random_state: int = RANDOM_STATE):
    """Carrega os dados, faz o split e devolve as partições já com a feature
    `High_Failed_Logins` adicionada (mas ainda não transformadas — o
    `ColumnTransformer` só é ajustado no treino, por quem o for usar)."""
    df = load_data(path)
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(df, random_state=random_state)

    X_train = add_features(X_train)
    X_val = add_features(X_val)
    X_test = add_features(X_test)

    return X_train, X_val, X_test, y_train, y_val, y_test


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split + pipeline de preparação de dados.")
    parser.add_argument("--data", default=DEFAULT_DATA_PATH, help="Caminho para o CSV.")
    args = parser.parse_args()

    X_train, X_val, X_test, y_train, y_val, y_test = prepare(args.data)

    print("=== Split estratificado ===")
    for name, (X, y) in {"treino": (X_train, y_train), "validação": (X_val, y_val),
                          "teste": (X_test, y_test)}.items():
        print(f"{name}: n={len(X)}, maliciosos={int(y.sum())}, taxa={y.mean():.2%}")

    preprocessor = build_preprocessor()
    preprocessor.fit(X_train)
    X_train_t = preprocessor.transform(X_train)

    print("\n=== Pipeline de pré-processamento ===")
    print("Features de saída:", list(preprocessor.get_feature_names_out()))
    print("Shape do treino transformado:", X_train_t.shape)
