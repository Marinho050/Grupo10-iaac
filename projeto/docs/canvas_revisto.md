# Revisão do canvas para deteção de trojans

O objetivo é classificar fluxos concluídos como Benign ou Trojan, apoiando revisão humana no SOC. A amostra tem 177 482 fluxos de 2017; não representa automaticamente a prevalência de uma rede atual.

Os rótulos, colunas, datas e limitações são recalculados em reports/qualidade_dados.json. Os números de modelos do canvas original são experiências anteriores; a versão atual usa reports/avaliacao_final.json. Repetição de uma assinatura com classes distintas pode resultar de contextos temporais diferentes e não demonstra, por si só, rótulo incorreto ou um limite matemático de desempenho.

A disponibilidade de features é no fim do fluxo. O orçamento inferior a 100 ms inclui aqui transformação das estatísticas já extraídas, imputação e inferência. A extração de PCAP, rede e latência do sensor não foi medida.

O critério original continua a ser recall Trojan de pelo menos 90% e FPR de no máximo 5%. O limiar é selecionado exclusivamente na validação para maximizar recall sob FPR de 5%; a aceitação é verificada no teste sem retreinar no teste. Se falhar, o artefacto serve apenas para demonstração e revisão humana. O projeto não executa bloqueio automático.

O baseline usa a proporção de classes do treino. IPs e Timestamp não são features; Source IP define a separação de entidades. IPs de destino podem repetir e há apenas algumas origens dominantes. A ablação remove portas e features de pilha TCP, comparada exclusivamente na validação. Um teste temporal recente não permite FPR porque só tem positivos.

O custo monetário de FN e FP, a capacidade real do SOC, o responsável operacional, a origem/licença pública do dataset e a integração com sensores precisam de confirmação pelo grupo. Alertas por dia são uma projeção sob a amostragem observada e não uma previsão validada da carga de produção.

Monitorização: PSI das features, distribuição de scores, proporção de alertas, latência p95 e métricas quando houver rótulos confirmados. Drift não autoriza retreino automático nem prova degradação do classificador.
