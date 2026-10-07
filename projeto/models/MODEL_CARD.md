# Modelo de deteção de trojans

Uso pretendido: demonstração académica e apoio a revisão de fluxos CICFlowMeter concluídos. Não aprovado para bloqueio de tráfego em produção.

Treino: dataset fornecido pelo aluno, SHA256 em reports/avaliacao_final.json, capturas de 2017. Classes: Benign 0, Trojan 1. Pipeline completo com FlowFeatures, mediana ajustada só no treino, remoção de variância zero e HistGradientBoostingClassifier. IPs e datas não são features.

Seleção: sete candidatos avaliados na validação; maximizar recall sob FPR de 5%, desempatar por AUC PR/ROC. O limiar final é 0,9275683468476112. Não houve refit no teste nem em todos os dados após a avaliação, para preservar o artefacto efetivamente medido.

Teste: 5 604 linhas, 449 IPs de origem novos, 2 676 Trojan e 2 928 Benign. AUC ROC 0,642496; recall 0,042975; FPR 0,042350; precisão 0,481172. Matriz TN 2 804, FP 124, FN 2 561, TP 115. O critério original do canvas não é atingido.

Limitações: poucos IPs dominam treino e validação; distribuição de classes varia por contexto; IPs de destino podem repetir; validação temporal recente não tem negativos; dados antigos e custos/capacidade do SOC não confirmados. Scores não foram calibrados numa amostra recente representativa. O IC por grupo é descritivo e não elimina viés de recolha.

Reprodução: Python e bibliotecas fixados em requirements-lock.txt; modelos individuais e pacote final em models/; seed 42 para teste e 43 para validação. O treino integral começa por python -m src.modelacao com o dataset local. O artefacto usa sklearn 1.7.2.

Monitorização e atualização: docs/operacao.md. Exigir novos dados rotulados com ambas as classes e uma nova reserva antes de melhorar a versão, porque o teste atual já foi observado.
