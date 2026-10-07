# Roadmap do projeto de deteção de trojans

Data de revisão: 7 de outubro de 2026. Responsável pela componente Trojan: Márcio Araújo. Este plano adapta as aulas de 18 e 21 de setembro ao dataset Trojan_Detection.csv e prolonga o trabalho até deployment e monitorização. As datas históricas não representam reuniões realizadas.

## Estado encontrado

Existiam canvas preenchido, dados, seis scripts, gráficos e resultados de experiências anteriores. Não existiam Git local, notebook executável, API Trojan, testes, backlog, documentação técnica ou evidência de reprodução neste computador. O repositório remoto continha um exemplo FastAPI de classificação de cancro da mama, preservado na raiz.

A inferência exigia Class; a imputação usava a mediana do lote e era calculada antes da separação; o limiar era escolhido no teste; o modelo HGB era fixado sem uma seleção formal; a medição de latência era apenas média de um lote; o PSI ignorava observações fora dos extremos da referência. Os resultados antigos ficam preservados na cópia de segurança, sem servir como evidência da versão corrigida.

## Etapas e evidências

| Etapa CRISP ML | Trabalho | Evidência de conclusão |
|---|---|---|
| Business understanding | Definir SOC, fluxo terminado, Trojan positivo, custos FN e FP e critério original | Canvas fornecido e docs/canvas_revisto.md |
| Data understanding | Confirmar classes, datas, constantes, assinaturas repetidas, EDA e Pearson/Spearman | reports/qualidade_dados.json, tabelas EDA e figs/ |
| Data preparation | Contrato sem Class na inferência, retirar IDs, transformar taxas e categorias, imputar só no treino | src/preparacao.py e testes de regressão |
| Modelagem | Baseline, logística, árvore, RF, HGB, HGB regularizado e ablação de portas e host | models/ e reports/comparacao_validacao.csv |
| Avaliação | Treino, validação e teste com Source IP disjunto; limiar na validação; teste final, bootstrap e métricas diárias | reports/splits.json e avaliacao_final.json |
| Deployment | CLI, API, dashboard, pacote serializado e Dockerfile | predict.py, api.py, static/ e models/ |
| Monitorização | PSI, latência individual e critérios para rever o modelo | reports/psi_deriva.csv e docs/operacao.md |
| Gestão SCRUM | Product backlog, sprints e registo verdadeiro do trabalho | docs/backlog.md e docs/scrum.md |
| Entrega | Notebook, módulos, testes, explicação do código e Git | notebooks/, tests/, docs/ e histórico da branch Márcio |

## Sequência de execução no VS Code

1. Abrir o repositório e a pasta projeto; selecionar projeto/.venv/Scripts/python.exe.
2. Executar python -m src.eda para atualizar a análise e qualidade.
3. Executar python -m src.modelacao para treinar candidatos, fixar limiar e avaliar o teste reservado.
4. Executar python -m pytest -q para validar contrato e integração.
5. Executar python predict.py examples/fluxos_sem_rotulo.csv e python -m uvicorn api:app --host 127.0.0.1 --port 8000.
6. Abrir notebooks/01_pipeline.ipynb e executar todas as células.
7. Rever os resultados em reports/avaliacao_final.json e a decisão original de deployment, sem reduzir metas para declarar sucesso.
8. Rever commits e publicar a branch Márcio sem alterar outras branches.

## Pendências externas

O grupo deve fornecer os restantes datasets, validar a escolha com o professor, identificar os outros elementos, preencher reuniões reais, aplicar os templates do Classroom e redigir o relatório académico de 25 a 30 páginas. A defesa individual de 5 a 7 minutos é uma atividade do aluno. Nenhuma reunião, aprovação, contribuição ou execução inexistente é marcada como feita.
