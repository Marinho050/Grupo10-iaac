"""
data_understanding.py
======================

Etapa de Data Understanding (CRISP-ML(Q)) do projeto de Deteção de Conexões
Maliciosas (IAAC — Grupo 10).

Carrega o dataset bruto e produz um perfil de qualidade de dados: shape,
tipos, nulos, duplicados, zeros por coluna, estatísticas descritivas e a
relação de cada feature com o alvo (correlações de Pearson e Spearman).

Corresponde ao conteúdo de `notebooks/EDA_cybersecurity.ipynb`, em formato de
script reutilizável (sem os gráficos, que ficam no notebook). Ver também
`Data_Understanding.md` para a discussão das limitações do dataset.

Uso:
    python src/data_understanding.py [--data CAMINHO_PARA_O_CSV]
"""

import argparse
import os

import pandas as pd

TARGET = "Is_Malicious"
NUM_COLS = ["Packet_Size_Bytes", "Connection_Duration_ms", "Failed_Logins", "Geo_Distance_km"]
CAT_COLS = ["Protocol"]

DEFAULT_DATA_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "datasets", "Raw", "cybersecurity_network_logs.csv")
)


def load_data(path: str = DEFAULT_DATA_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def data_quality_report(df: pd.DataFrame) -> dict:
    """Shape, tipos, nulos, duplicados e zeros por coluna numérica."""
    return {
        "shape": df.shape,
        "dtypes": df.dtypes.astype(str).to_dict(),
        "n_nulls": df.isna().sum().to_dict(),
        "n_duplicates": int(df.duplicated().sum()),
        "n_zeros": {col: int((df[col] == 0).sum()) for col in NUM_COLS},
        "target_distribution": df[TARGET].value_counts().to_dict(),
        "target_prevalence": float(df[TARGET].mean()),
    }


def descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    stats = df[NUM_COLS].describe().T
    stats["skew"] = df[NUM_COLS].skew()
    stats["kurtosis"] = df[NUM_COLS].kurt()
    return stats


def target_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Correlação de Pearson e Spearman de cada numérica com o alvo."""
    pearson = df[NUM_COLS + [TARGET]].corr(method="pearson")[TARGET].drop(TARGET)
    spearman = df[NUM_COLS + [TARGET]].corr(method="spearman")[TARGET].drop(TARGET)
    return pd.DataFrame({"pearson": pearson, "spearman": spearman})


def malicious_rate_by_protocol(df: pd.DataFrame) -> pd.Series:
    return df.groupby("Protocol")[TARGET].mean().sort_values(ascending=False)


def malicious_rate_by_failed_logins(df: pd.DataFrame) -> pd.Series:
    return df.groupby("Failed_Logins")[TARGET].mean()


def iqr_outlier_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Nº de outliers (regra do IQR) e taxa de maliciosos dentro desses outliers,
    por coluna numérica — ver nota na EDA: não remover, correlacionam com o alvo."""
    rows = []
    for col in NUM_COLS:
        q1, q3 = df[col].quantile([.25, .75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (df[col] < lo) | (df[col] > hi)
        rows.append({
            "feature": col,
            "n_outliers": int(mask.sum()),
            "pct_outliers": round(float(mask.mean() * 100), 2),
            "malicious_rate_in_outliers": round(float(df.loc[mask, TARGET].mean()), 4) if mask.sum() else None,
        })
    return pd.DataFrame(rows).set_index("feature")


def profile(path: str = DEFAULT_DATA_PATH) -> dict:
    """Corre o perfil completo e devolve tudo num único dicionário."""
    df = load_data(path)
    return {
        "quality": data_quality_report(df),
        "descriptive_stats": descriptive_stats(df),
        "target_correlations": target_correlations(df),
        "malicious_rate_by_protocol": malicious_rate_by_protocol(df),
        "malicious_rate_by_failed_logins": malicious_rate_by_failed_logins(df),
        "outliers": iqr_outlier_summary(df),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perfil de qualidade de dados do dataset.")
    parser.add_argument("--data", default=DEFAULT_DATA_PATH, help="Caminho para o CSV.")
    args = parser.parse_args()

    report = profile(args.data)

    print("=== Qualidade dos dados ===")
    q = report["quality"]
    print(f"Shape: {q['shape']}")
    print(f"Duplicados: {q['n_duplicates']}")
    print(f"Zeros por coluna: {q['n_zeros']}")
    print(f"Distribuição do alvo: {q['target_distribution']} "
          f"(prevalência {q['target_prevalence']:.2%})")

    print("\n=== Estatísticas descritivas (com skew/kurtosis) ===")
    print(report["descriptive_stats"].round(2))

    print("\n=== Correlação com o alvo (Pearson vs Spearman) ===")
    print(report["target_correlations"].round(3))

    print("\n=== Taxa de maliciosos por protocolo ===")
    print(report["malicious_rate_by_protocol"].round(4))

    print("\n=== Taxa de maliciosos por nº de logins falhados ===")
    print(report["malicious_rate_by_failed_logins"].round(3))

    print("\n=== Outliers (IQR) e taxa de maliciosos dentro deles ===")
    print(report["outliers"])
