"""Pontua CSVs sem rótulo, usando exatamente o pipeline serializado no treino."""
import argparse
from pathlib import Path
from src.inferencia import Predictor,ROOT
from src.preparacao import carregar

def main():
    p=argparse.ArgumentParser(); p.add_argument('csv_entrada',type=Path)
    p.add_argument('--modelo',type=Path,default=ROOT/'models/modelo_trojan.joblib')
    p.add_argument('--limiar',type=float,default=None)
    p.add_argument('--saida',type=Path,default=ROOT/'reports/scores.csv')
    args=p.parse_args(); result=Predictor(args.modelo).predict(carregar(args.csv_entrada),args.limiar)
    args.saida.parent.mkdir(parents=True,exist_ok=True); result.to_csv(args.saida,index=False)
    print(f'{len(result)} fluxos; {int(result.alerta.sum())} alertas para revisão. {args.saida}')
if __name__=='__main__': main()
