# Data Understanding — Deteção de Conexões Maliciosas

IAAC — Grupo 10. Documento de apoio ao relatório final, cobrindo a fase de Data Understanding do CRISP-ML(Q).

## 1. Origem e recolha dos dados

- **Ficheiro:** `datasets/Raw/cybersecurity_network_logs.csv`
- **Volume:** 25.000 registos, 6 colunas (5 features + 1 alvo).
- **Unidade de observação:** uma conexão de rede (flow), não um pacote individual — as features só ficam completas no fim da conexão.
- **Origem:** dataset disponibilizado para o projeto (não há metadados sobre a rede/organização de origem nem sobre o período de captura). Aparenta ser sintético — ver secção 5.

## 2. Dicionário de dados

| Coluna | Tipo | Descrição | Intervalo observado | Notas |
|---|---|---|---|---|
| `Protocol` | categórica (texto) | Protocolo de rede da conexão | `TCP` (70,1%), `UDP` (20,2%), `ICMP` (9,7%) | Sem valores em falta |
| `Packet_Size_Bytes` | numérica (inteiro) | Tamanho do pacote, em bytes | 0 – 10.032 (mediana 357) | 26 valores a zero; assimetria alta (skew ≈4,1) |
| `Connection_Duration_ms` | numérica (inteiro) | Duração da conexão, em milissegundos | 0 – 1.213 (mediana 69) | 120 valores a zero; assimetria moderada (skew ≈2,0) |
| `Failed_Logins` | numérica (inteiro) | Nº de tentativas de login falhadas na conexão | 0 – 16 (mediana 0) | Quase toda zeros; sinal mais forte do dataset |
| `Geo_Distance_km` | numérica (inteiro) | Distância geográfica estimada entre origem e destino, em km | 0 – 8.661 (mediana 359) | 19 valores a zero; assimetria alta (skew ≈4,0) |
| `Is_Malicious` | binária (alvo) | 1 = conexão maliciosa, 0 = benigna | {0, 1} | Prevalência 4,99% (1.247 maliciosas em 25.000) |

## 3. Qualidade dos dados

| Verificação | Resultado |
|---|---|
| Valores nulos | Nenhum, em nenhuma coluna |
| Linhas duplicadas | Nenhuma |
| Tipos de dados | Consistentes (numéricos como inteiros, `Protocol` como texto, alvo binário) |
| Valores fora do domínio esperado (ex.: negativos) | Nenhum encontrado |
| Zeros suspeitos | 26 em `Packet_Size_Bytes`, 120 em `Connection_Duration_ms`, 19 em `Geo_Distance_km` — plausíveis (ex.: handshake falhado antes de trocar dados), mas não confirmados por documentação da origem |
| Outliers (IQR) | 4,9%–12,3% das linhas, consoante a variável — não removidos, ver EDA (correlacionam fortemente com `Is_Malicious`) |

**Conclusão:** dados tecnicamente "limpos" (sem nulos/duplicados/erros de tipo), o que reforça a suspeita de serem sintéticos ou já pré-processados antes de nos serem entregues.

## 4. Relação das features com o alvo (resumo da EDA)

| Feature | Poder discriminativo | Observação |
|---|---|---|
| `Failed_Logins` | Muito forte | `≥3` falhas → 93–100% maliciosas |
| `Packet_Size_Bytes` | Forte, não-linear | Dois perfis de ataque (pacotes grandes vs. pequenos); Pearson 0,66 vs. Spearman 0,23 |
| `Geo_Distance_km` | Forte, não-linear | Padrão semelhante ao `Packet_Size_Bytes` |
| `Connection_Duration_ms` | Nulo | Correlação ≈0 com o alvo |
| `Protocol` | Fraco | Taxas de maliciosos muito próximas entre TCP/UDP/ICMP (4,9%–5,6%) |

Detalhe completo com gráficos: `notebooks/EDA_cybersecurity.ipynb`.

## 5. Limitações do dataset

1. **Provável origem sintética.** A ausência total de nulos/duplicados/erros, a assimetria muito regular das variáveis e um sinal isolado (`Failed_Logins`) quase perfeitamente discriminativo não são típicos de tráfego de rede real, que costuma ser mais ruidoso. Um baseline simples atinge recall ≈90%+ sem qualquer afinação — resultado otimista demais para um cenário de produção.
2. **Sem timestamp, IP ou identificador de sessão.** Impossibilita qualquer análise temporal (ex.: "tentativas de login falhadas por minuto", padrões por hora do dia) ou agregações por origem/destino, que seriam úteis num SOC real.
3. **Sem metadados de origem.** Não se sabe se os dados vêm de uma rede empresarial, um honeypot, ou são gerados artificialmente — o que limita a validade externa das conclusões.
4. **Apenas 5 features.** Um SOC real tem tipicamente dezenas de variáveis (portas, flags TCP, payload, reputação de IP, etc.); este dataset é uma simplificação didática.
5. **Prevalência fixa (4,99%).** Não se sabe se reflete a taxa real de conexões maliciosas na rede de origem, ou se foi construída artificialmente (ex.: amostragem estratificada do autor do dataset).

## 6. Implicações para a modelação

- **Cautela na generalização:** os resultados finais (recall 93,6%, FP 0,08% — ver `notebooks/Modelling_cybersecurity.ipynb`) devem ser lidos como um limite superior otimista, não como uma estimativa de desempenho em produção.
- **Não avançar para bloqueio automático** sem validação em dados reais (ou pelo menos um dataset com mais ruído e variáveis), mantendo o modo "alerta apenas" definido no Business Understanding.
- **`Failed_Logins` como feature dominante** é um ponto de atenção: um adversário que soubesse disto poderia tentar evitar múltiplos logins falhados para escapar à deteção (adversarial evasion) — vale a pena referir esta limitação no relatório final.

---
*Documento gerado a partir da análise em `notebooks/EDA_cybersecurity.ipynb`, `notebooks/Data_Preparation_cybersecurity.ipynb` e `notebooks/Modelling_cybersecurity.ipynb`.*
