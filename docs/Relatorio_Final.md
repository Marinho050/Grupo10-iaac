# Deteção de Conexões Maliciosas — Relatório Final

**IAAC — Grupo 10**

---

## 1. Introdução e Business Understanding

Este projeto tem como objetivo construir um classificador que identifica, a partir de registos de rede tipo NetFlow, conexões maliciosas vs. benignas, para apoiar a triagem de alertas de um Security Operations Center (SOC).

### 1.1 Objetivo de negócio

Reduzir o tempo de deteção de conexões maliciosas numa rede, sinalizando-as para revisão por um analista de nível 1, sem sobrecarregar a equipa com falsos alarmes.

### 1.2 Momento da predição

A predição é feita **no fim da conexão** (abordagem flow-based, compatível com NetFlow), já que as três features mais informativas do dataset (`Connection_Duration_ms`, `Packet_Size_Bytes`, `Failed_Logins`) só ficam completas nesse momento — não é possível prever ao nível do pacote individual com estes dados.

### 1.3 Custos de erro e critérios de sucesso

Foram assumidos os seguintes custos (pressupostos, justificados e documentados para revisão):

- **Falso negativo** (ataque não detetado): ≈500€ — tempo de resposta a incidente, possível exfiltração de dados, impacto reputacional.
- **Falso positivo** (alerta que não era nada): ≈8€ — cerca de 20 minutos de tempo de um analista SOC nível 1.

A proporção (~60:1 a favor de evitar falsos negativos) justifica privilegiar o **recall** mesmo à custa de mais falsos positivos, dentro de um limite aceitável.

**Critérios de sucesso definidos:**

| Nível | Critério |
|---|---|
| ML | Recall ≥ 90%, taxa de falsos positivos ≤ 1% |
| Negócio | Volume de alertas dentro da capacidade da equipa SOC |
| Económico | Custo esperado (FN×500€ + FP×8€) inferior ao custo de não ter deteção alguma |

### 1.4 Estratégia de implementação (holdout)

Para evitar que o próprio modelo altere o desfecho das conexões que avalia (e assim contamine dados futuros de treino), a estratégia inicial de implementação é em **modo alerta**, sem bloqueio automático — o modelo sinaliza, um analista humano decide.

---

## 2. Data Understanding

### 2.1 Dataset

`cybersecurity_network_logs.csv` — 25.000 conexões de rede, 6 colunas (5 features + `Is_Malicious`). Sem valores nulos nem duplicados. Prevalência de conexões maliciosas: 4,99% (1.247 em 25.000).

| Coluna | Descrição |
|---|---|
| `Protocol` | Protocolo de rede (TCP / UDP / ICMP) |
| `Packet_Size_Bytes` | Tamanho do pacote (bytes) |
| `Connection_Duration_ms` | Duração da conexão (ms) |
| `Failed_Logins` | Nº de tentativas de login falhadas |
| `Geo_Distance_km` | Distância geográfica estimada da origem (km) |
| `Is_Malicious` | Alvo (1 = maliciosa, 0 = benigna) |

### 2.2 Limitações identificadas

O dataset aparenta ser **sintético**: ausência total de nulos/erros, um sinal isolado (`Failed_Logins`) quase perfeitamente discriminativo, e nenhuma variável temporal, de IP ou de sessão. Isto limita a validade externa dos resultados — devem ser lidos como um limite superior otimista, não como desempenho esperado em produção. Detalhe completo em `Data_Understanding.md`.

---

## 3. Análise Exploratória de Dados (EDA)

Notebook completo: `notebooks/EDA_cybersecurity.ipynb`.

### 3.1 Principais achados

- **`Failed_Logins ≥ 3`** é o sinal isolado mais forte do dataset: 93–100% das conexões com esse valor são maliciosas.
- **`Packet_Size_Bytes`** e **`Geo_Distance_km`** discriminam bem mas de forma **bimodal/não-linear** — existem dois perfis de ataque distintos (pacotes grandes: 768 casos; pacotes pequenos: 479 casos). Isto explica a divergência entre a correlação de Pearson (≈0,66) e de Spearman (≈0,23) nestas variáveis.
- **`Connection_Duration_ms`** e **`Protocol`** têm pouco ou nenhum poder discriminativo isolado (correlação ≈0; taxas de maliciosos muito semelhantes entre protocolos).
- **Outliers não devem ser removidos** — nas variáveis mais discriminativas, quase metade dos outliers são precisamente as conexões maliciosas que se pretende detetar.
- **Casos difíceis identificados:** 179 conexões maliciosas "disfarçadas" (poucos logins falhados, pacote pequeno) e 428 conexões benignas com pacote grande (potenciais falsos positivos) — pontos de atenção para a avaliação do modelo.

---

## 4. Data Preparation

Notebook completo: `notebooks/Data_Preparation_cybersecurity.ipynb`.

- **Split estratificado** 70% treino / 15% validação / 15% teste, preservando a prevalência de 4,99% em todas as partições (187 positivos no conjunto de teste).
- **Feature engineering:** criação de `High_Failed_Logins` (`Failed_Logins ≥ 3`), a partir do sinal mais forte da EDA.
- **Pipeline (`ColumnTransformer`):** `log1p` + escalonamento em `Packet_Size_Bytes` e `Geo_Distance_km` (muito assimétricas); escalonamento simples nas restantes numéricas; one-hot encoding em `Protocol`. Ajustado apenas no treino, sem fuga de informação.
- **Desbalanceamento:** tratado com `class_weight="balanced"` em vez de reamostragem, evitando duplicar ou descartar dados.

---

## 5. Modelação

Notebook completo: `notebooks/Modelling_cybersecurity.ipynb`.

### 5.1 Comparação de modelos

Comparados por validação cruzada (5-fold, estratificada, só no treino):

| Modelo | Recall (CV) | Precisão (CV) | PR-AUC (CV) |
|---|---|---|---|
| Regressão Logística | 85,9% | 51,3% | 0,866 |
| **Random Forest** | **91,5%** | **97,6%** | **0,926** |

O Random Forest venceu claramente, confirmando a relação não-linear identificada na EDA.

### 5.2 Afinação do threshold

Com o threshold por omissão (0,5), o recall na validação (89,3%) ficava ligeiramente abaixo do alvo de 90%. Como a margem de falsos positivos era ampla, o threshold foi afinado para **0,465**, usando apenas dados de validação, elevando o recall para 90,4% sem violar o limite de falsos positivos.

### 5.3 Avaliação final (conjunto de teste, usado uma única vez)

| Métrica | Alvo | Resultado |
|---|---|---|
| Recall | ≥ 90% | **93,6%** |
| Taxa de falsos positivos | ≤ 1% | **0,08%** |
| PR-AUC | — | 0,957 |

De 187 conexões maliciosas no teste, o modelo deteta 175 (12 falsos negativos) e gera apenas 3 falsos positivos em 3.563 conexões benignas. **Ambos os critérios de sucesso definidos no Business Understanding foram cumpridos.**

---

## 6. Implementação

O modelo final (`models/model_final.joblib`) foi disponibilizado através de uma API REST (`app/main.py`, FastAPI), com um endpoint `/predict` que recebe as 5 features de uma conexão e devolve a classificação, a probabilidade e o threshold usado. Testado com testes automatizados (`app/tests/test_main.py`), incluindo casos benignos e maliciosos típicos.

---

## 7. Conclusões e limitações

O projeto cumpriu os critérios de sucesso definidos: um modelo Random Forest, com threshold afinado, deteta 93,6% das conexões maliciosas no conjunto de teste com apenas 0,08% de falsos positivos.

Estes resultados devem, no entanto, ser interpretados com cautela:

1. **O dataset é provavelmente sintético.** Tráfego de rede real é mais ruidoso; o desempenho em produção será provavelmente inferior ao obtido aqui.
2. **Risco de evasão adversarial.** `Failed_Logins` é a feature dominante — um atacante que evitasse múltiplas tentativas de login falhadas poderia escapar à deteção. Um modelo em produção deveria combinar múltiplos sinais independentes.
3. **Sem validação em dados reais.** Recomenda-se testar o modelo com tráfego de produção, mantendo o modo "alerta apenas" (sem bloqueio automático) até essa validação estar concluída.

### Próximos passos sugeridos

- Validar o modelo com dados de produção reais.
- Explorar features adicionais (timestamps, IP, sessão) caso venham a estar disponíveis.
- Reavaliar periodicamente o modelo à medida que novos dados/rótulos de analistas SOC forem recolhidos (deteção de drift).

---

*Documentação de suporte: `Data_Understanding.md`, `Backlog_Scrum_IAAC.xlsx`, e os notebooks em `notebooks/`.*
