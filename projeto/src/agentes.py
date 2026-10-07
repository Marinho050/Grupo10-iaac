"""Dois agentes locais com execução direta ou LangGraph, sobre o mesmo contrato factual."""
from pathlib import Path
from typing import TypedDict
from functools import lru_cache
import argparse
import re
import json
import pandas as pd
from .inferencia import Predictor,ROOT
from .preparacao import carregar

class Estado(TypedDict,total=False):
    csv:str
    usar_llm:bool
    fatos:dict
    texto:str
    comentario_aprovado:bool

@lru_cache(maxsize=1)
def carregar_gerador():
    import torch
    from transformers import AutoTokenizer,AutoModelForCausalLM
    torch.set_num_threads(4)
    path=ROOT/'models/llm'
    tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True,trust_remote_code=False)
    model=AutoModelForCausalLM.from_pretrained(path,local_files_only=True,trust_remote_code=False,dtype=torch.float32)
    model.eval()
    return tokenizer,model

def agente_classificador(estado):
    predictor=Predictor(); df=carregar(estado['csv']); out=predictor.predict(df)
    facts={'fluxos':len(out),'alertas':int(out.alerta.sum()),'modelo':predictor.bundle['nome'],
           'limiar':predictor.bundle['limiar'],'criterio_deployment_atingido':predictor.bundle['deployment_approved'],
           'recall_teste':predictor.bundle['test_metrics']['recall'],'fpr_teste':predictor.bundle['test_metrics']['fpr'],
           'acao':'Revisão manual, sem bloqueio automático.'}
    return {'fatos':facts}

def validar_comentario(texto):
    """Aceita apenas explicação genérica de revisão humana, sem métricas ou alegações operacionais."""
    lower=texto.casefold()
    denied=re.search(r'\d|produ[cç][aã]o|conformidade|garant|bloque|aprovad|certific',lower)
    return bool(texto.strip() and len(texto)<=1500 and not denied and 'revis' in lower
                and ('human' in lower or 'analist' in lower))

def agente_relator(estado):
    if not estado.get('usar_llm',True):
        return {'texto':'Geração neural desativada explicitamente. Consulte os factos calculados.','comentario_aprovado':False}
    import torch
    from transformers import GenerationConfig
    tokenizer,model=carregar_gerador()
    messages=[{'role':'system','content':'Escreve apenas duas frases em português sobre a importância da revisão humana de alertas de rede. Não uses números, métricas, palavras sobre produção, certificação, conformidade ou bloqueios. Não avalies a qualidade de nenhum modelo.'},
              {'role':'user','content':'Porque deve um analista rever o contexto de um alerta de um classificador de tráfego de rede? Explica a revisão humana de forma genérica.'}]
    text=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    inputs=tokenizer([text],return_tensors='pt')
    with torch.inference_mode():
        config=GenerationConfig(max_new_tokens=140,do_sample=False,pad_token_id=tokenizer.eos_token_id,eos_token_id=tokenizer.eos_token_id)
        generated=model.generate(**inputs,generation_config=config)
    response=tokenizer.decode(generated[0][inputs.input_ids.shape[-1]:],skip_special_tokens=True)
    approved=validar_comentario(response)
    comment=response.strip() if approved else 'Comentário neural rejeitado pelo controlo de conteúdo. Consulte os factos calculados.'
    policy='O modelo não está aprovado para produção.' if not estado['fatos']['criterio_deployment_atingido'] else 'O critério offline foi atingido; o sistema continua em demonstração local.'
    return {'texto':comment+'\n\n'+policy,'comentario_aprovado':approved}

def executar(csv=ROOT/'examples/fluxos_sem_rotulo.csv',backend='python',usar_llm=True,guardar=True):
    state:Estado={'csv':str(csv),'usar_llm':usar_llm}
    if backend=='python':
        state.update(agente_classificador(state)); state.update(agente_relator(state))
    elif backend=='langgraph':
        from langgraph.graph import StateGraph,START,END
        graph=StateGraph(Estado); graph.add_node('classificador',agente_classificador); graph.add_node('relator',agente_relator)
        graph.add_edge(START,'classificador'); graph.add_edge('classificador','relator'); graph.add_edge('relator',END)
        state=graph.compile().invoke(state)
    else: raise ValueError('backend deve ser python ou langgraph.')
    facts=state['fatos']
    report='# Relatório auxiliar dos agentes\n\n'
    report+='Factos calculados pelo classificador, sem interpretação do LLM:\n\n'
    report+='| Campo | Valor |\n|---|---|\n'+''.join(f'| {k} | {v} |\n' for k,v in facts.items())
    report+='\n## Comentário gerado automaticamente\n\n'+state['texto']+'\n\n'
    report+='Este comentário requer revisão humana e não substitui as métricas, o relatório académico nem uma decisão operacional.\n'
    if guardar:
        path=ROOT/'reports'/f'relatorio_agentes_{backend}.md'; path.parent.mkdir(exist_ok=True); path.write_text(report,encoding='utf-8')
    return state

def main():
    p=argparse.ArgumentParser(); p.add_argument('--csv',type=Path,default=ROOT/'examples/fluxos_sem_rotulo.csv')
    p.add_argument('--backend',choices=['python','langgraph'],default='python'); p.add_argument('--sem-llm',action='store_true'); args=p.parse_args()
    result=executar(args.csv,args.backend,not args.sem_llm); print(result['texto'])
if __name__=='__main__':main()
