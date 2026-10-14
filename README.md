# Deteção de trojans Grupo 10 IAAC

Este repositório contém o projeto de deteção de Trojan de Márcio Araújo. O código, os modelos, os dados locais, os testes e a documentação estão na pasta **projeto/**.

## Abrir no VS Code

Abra **Trojan-IAAC.code-workspace**. Neste computador, **Trojan-local.code-workspace** já tem o Git e o interpretador Python configurados.

Comece pelo [README do projeto](projeto/README.md), que explica como executar cada etapa. Para compreender os ficheiros, consulte o [guia técnico](projeto/docs/guia_tecnico.md).

## Abrir a demonstração local

No terminal, a partir da raiz deste repositório:

```powershell
cd projeto
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Mantenha o terminal aberto e visite http://127.0.0.1:8000/. Para parar, use Ctrl+C.

## Organização

| Pasta | Conteúdo |
|---|---|
| projeto/src | Preparação, treino, avaliação, inferência e agentes |
| projeto/models | Classificadores e respetivos manifestos |
| projeto/notebooks | Notebook do projeto Trojan |
| projeto/tests | Testes do código e da API |
| projeto/docs | Roadmap, explicação do código e gestão do projeto |
| projeto/reports | Resultados e evidências de validação |
| .github/workflows | Testes automáticos no GitHub |

O exemplo antigo de classificação de cancro da mama foi retirado desta branch em 14 de outubro de 2026, depois de criar uma cópia de segurança. Continua recuperável pelo histórico Git. Os comandos e ficheiros atuais referem-se ao projeto Trojan.

O modelo atual não atingiu o critério de desempenho do canvas. A aplicação é uma demonstração para revisão humana, sem bloqueio automático de tráfego.
