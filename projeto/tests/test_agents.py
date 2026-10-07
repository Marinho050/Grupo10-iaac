from pathlib import Path
import pytest
from src.inferencia import ROOT
from src.agentes import executar

def test_agent_facts_without_llm():
    if not (ROOT/'models/modelo_trojan.joblib').exists(): pytest.skip('Modelo ainda não treinado.')
    result=executar(backend='python',usar_llm=False,guardar=False)
    assert result['fatos']['fluxos']==5
    assert result['fatos']['criterio_deployment_atingido'] is False
    assert result['fatos']['acao']=='Revisão manual, sem bloqueio automático.'
    assert 'desativada' in result['texto']

def test_agent_backends_same_facts():
    pytest.importorskip('langgraph')
    if not (ROOT/'models/modelo_trojan.joblib').exists(): pytest.skip('Modelo ainda não treinado.')
    direct=executar(backend='python',usar_llm=False,guardar=False)
    graph=executar(backend='langgraph',usar_llm=False,guardar=False)
    assert direct['fatos']==graph['fatos']


def test_reject_hallucinated_readiness():
    from src.agentes import validar_comentario
    assert not validar_comentario('Este alerta requer revisão humana, pois o modelo está pronto para produção.')
    assert not validar_comentario('Revisão humana garante conformidade com normas de segurança.')
    assert not validar_comentario('O analista revê os alertas com precisão de 99%.')
    assert validar_comentario('A revisão humana permite ao analista considerar o contexto de um alerta. O analista deve confirmar os acontecimentos antes de tomar decisões.')
