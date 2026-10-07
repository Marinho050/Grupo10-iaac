"""Mostra os resultados já calculados, sem escolher limiares no teste."""
from .modelacao import ROOT
import pandas as pd

def main():
    for name in ['limiares_validacao.csv','importancia_permutacao.csv']:
        print(name); print(pd.read_csv(ROOT/'reports'/name).head(10).to_string(index=False))
if __name__=='__main__': main()
