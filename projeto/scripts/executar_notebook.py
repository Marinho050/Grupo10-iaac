"""Executa o notebook com o interpretador corrente e grava as saídas para auditoria."""
from pathlib import Path
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
ROOT=Path(__file__).resolve().parents[1]

def main():
    path=ROOT/'notebooks/01_pipeline.ipynb'
    nb=nbformat.read(path,as_version=4)
    km=KernelManager(kernel_name='python3')
    km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
    client=NotebookClient(nb,timeout=600,kernel_manager=km,resources={'metadata':{'path':str(ROOT)}})
    client.execute(); nbformat.write(nb,path)
    print('Notebook executado:',len([x for x in nb.cells if x.cell_type=='code']),'células de código sem erros.')
if __name__=='__main__':main()
