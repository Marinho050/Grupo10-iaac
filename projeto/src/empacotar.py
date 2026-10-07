"""Verifica o pacote final; o treino e a serialização são feitos por src.modelacao."""
from .inferencia import Predictor

def main():
    p=Predictor(); print({'modelo':p.bundle['nome'],'limiar':p.bundle['limiar'],'deployment_approved':p.bundle['deployment_approved']})
if __name__=='__main__': main()
