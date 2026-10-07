"""Contrato de entrada e engenharia determinística, reutilizados no treino e previsão."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted

IDS = {'', 'Unnamed: 0', 'Flow ID', 'Source IP', 'Destination IP', 'Timestamp', 'Source Port', 'Class'}
DUPLICADAS = {'Fwd Header Length.1'}
LOG_COLS = {'Flow Bytes/s', 'Flow Packets/s', 'Fwd Packets/s', 'Bwd Packets/s'}
HOST_COLS = {'Init_Win_bytes_forward', 'Init_Win_bytes_backward', 'min_seg_size_forward'}

def normalizar(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    if df.columns.duplicated().any():
        raise ValueError('Nomes de colunas duplicados após remover espaços.')
    return df

def carregar(path):
    return normalizar(pd.read_csv(path))

def rotulos(df):
    if 'Class' not in df:
        raise ValueError('Treino exige a coluna Class.')
    labels = df['Class'].astype('string').str.strip()
    if labels.isna().any() or not labels.isin(['Benign', 'Trojan']).all():
        raise ValueError('Class aceita apenas Benign e Trojan, sem valores em falta.')
    return labels.eq('Trojan').astype(int)

def metadados(df):
    required = ['Source IP', 'Timestamp']
    if any(c not in df for c in required) or df[required].isna().any().any():
        raise ValueError('Avaliação exige Source IP e Timestamp completos.')
    meta = df[[c for c in ['Flow ID','Source IP','Destination IP','Timestamp'] if c in df]].copy()
    meta['dia'] = pd.to_datetime(meta['Timestamp'], format='%d/%m/%Y %H:%M:%S', errors='raise').dt.strftime('%Y-%m-%d')
    return meta

class FlowFeatures(TransformerMixin, BaseEstimator):
    """Aprende apenas o esquema; imputação e seleção são passos posteriores do Pipeline."""
    def __init__(self, sem_portas=False, sem_host=False):
        self.sem_portas = sem_portas
        self.sem_host = sem_host

    def fit(self, X, y=None):
        df = normalizar(X)
        if len(df) == 0:
            raise ValueError('Não é possível treinar com zero fluxos.')
        ignored = IDS | DUPLICADAS | {'Protocol', 'Destination Port'}
        if self.sem_host:
            ignored = ignored | HOST_COLS
        self.numeric_columns_ = [c for c in df.columns if c not in ignored]
        if not self.numeric_columns_:
            raise ValueError('Não foram encontradas estatísticas numéricas de fluxos.')
        self.required_columns_ = self.numeric_columns_ + ['Protocol'] + ([] if self.sem_portas else ['Destination Port'])
        self.transform(df)
        return self

    def transform(self, X):
        check_is_fitted(self, 'numeric_columns_')
        df = normalizar(X)
        missing = sorted(set(self.required_columns_) - set(df.columns))
        if missing:
            raise ValueError('Colunas obrigatórias em falta: ' + ', '.join(missing))
        out = pd.DataFrame(index=df.index)
        for c in self.numeric_columns_:
            numeric = pd.to_numeric(df[c], errors='coerce')
            if (df[c].notna() & numeric.isna()).any():
                raise ValueError(f'Valor não numérico em {c}.')
            numeric = numeric.replace([np.inf, -np.inf], np.nan).astype(float)
            out[c] = np.sign(numeric) * np.log1p(np.abs(numeric)) if c in LOG_COLS else numeric
        proto = pd.to_numeric(df['Protocol'], errors='coerce')
        if proto.isna().any() or ((proto < 0) | (proto > 255) | (proto % 1 != 0)).any():
            raise ValueError('Protocol deve ser um inteiro de 0 a 255.')
        for name, value in [('TCP',6), ('UDP',17)]:
            out['proto_' + name] = proto.eq(value).astype(float)
        out['proto_outro'] = (~proto.isin([6,17])).astype(float)
        if not self.sem_portas:
            port = pd.to_numeric(df['Destination Port'], errors='coerce')
            if port.isna().any() or ((port < 0) | (port > 65535) | (port % 1 != 0)).any():
                raise ValueError('Destination Port deve ser um inteiro de 0 a 65535.')
            out['porta_conhecida'] = port.lt(1024).astype(float)
            out['porta_registada'] = ((port >= 1024) & (port < 49152)).astype(float)
            out['porta_efemera'] = port.ge(49152).astype(float)
        return out

    def get_feature_names_out(self, input_features=None):
        names = self.numeric_columns_ + ['proto_TCP', 'proto_UDP', 'proto_outro']
        if not self.sem_portas:
            names += ['porta_conhecida', 'porta_registada', 'porta_efemera']
        return np.asarray(names, dtype=object)
