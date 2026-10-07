# Arquitetura e caso de uso

## Pipeline CRISP ML

```mermaid
flowchart LR
 A[CSV CICFlowMeter] --> B[Contrato e qualidade]
 B --> C[Separar por Source IP]
 C --> D[Treino e preparação ajustada no treino]
 C --> E[Validação de candidatos e limiares]
 D --> E
 E --> F[Pipeline e limiar fixos]
 F --> G[Teste reservado]
 G --> H[Modelos e métricas]
 H --> I[CLI API e notebook]
 I --> J[Revisão humana e PSI]
```

## Agentes em Python e LangGraph

```mermaid
flowchart LR
 A[Fluxos sem rótulo] --> B[Agente classificador]
 M[Pipeline local em models] --> B
 B --> C[Factos numéricos calculados]
 C --> D[Agente relator Transformers local]
 L[Qwen pré treinado em models llm] --> D
 C --> E[Tabela factual preservada]
 D --> F[Comentário auxiliar]
 E --> G[Relatório para revisão]
 F --> G
```

A versão direta chama as funções sequencialmente. A versão LangGraph liga os mesmos agentes num StateGraph. O LLM explica genericamente a revisão humana; os factos agregados são preservados separadamente no relatório. Não define scores, limiares ou bloqueios. O modelo generativo é pré-treinado, não afinado com este dataset.

## Caso de uso no SOC

```mermaid
sequenceDiagram
 participant U as Analista
 participant A as API local
 participant C as Classificador
 participant R as Relator local
 U->>A: Enviar estatísticas de fluxos
 A->>C: Validar esquema e pontuar
 C-->>A: Score e alerta para revisão
 A-->>U: Resultados e estado de deployment
 U->>R: Pedir relatório auxiliar pelo script
 R-->>U: Factos preservados e comentário neural
 U->>U: Rever contexto e confirmar incidente
```

Os diagramas cobrem a componente Trojan disponível. A integração com os outros datasets exige os respetivos dados, modelos e contratos de previsão do grupo.
