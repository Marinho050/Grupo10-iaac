"""
business_understanding.py
==========================

Etapa de Business Understanding (CRISP-ML(Q)) do projeto de Deteção de
Conexões Maliciosas (IAAC — Grupo 10).

Este módulo não processa dados — documenta, em código executável, as decisões
de negócio tomadas e disponibiliza as fórmulas usadas para as justificar
(custo esperado de erro, volume diário de alertas). Serve de referência única
para os valores citados no README, no Relatório Final e nos restantes
módulos (`data_modeling.py`, `evaluation.py`).

Correr como script imprime um resumo dessas decisões e um exemplo de cálculo.
"""

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# 1. Custos de erro (pressupostos, documentados para revisão)
# ---------------------------------------------------------------------------

COST_FALSE_NEGATIVE_EUR = 500.0
"""Custo assumido de um ataque não detetado: tempo de resposta a incidente,
possível exfiltração de dados, impacto reputacional."""

COST_FALSE_POSITIVE_EUR = 8.0
"""Custo assumido de um alerta falso: ~20 minutos de um analista SOC nível 1
a ~25€/hora."""


def expected_cost(n_false_negatives: int, n_false_positives: int,
                   cost_fn: float = COST_FALSE_NEGATIVE_EUR,
                   cost_fp: float = COST_FALSE_POSITIVE_EUR) -> float:
    """Custo esperado total, dados os erros observados.

    custo_esperado = FN * custo_FN + FP * custo_FP
    """
    return n_false_negatives * cost_fn + n_false_positives * cost_fp


# ---------------------------------------------------------------------------
# 2. Critérios de sucesso
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SuccessCriteria:
    min_recall: float = 0.90
    max_fp_rate: float = 0.01

    def is_met(self, recall: float, fp_rate: float) -> bool:
        return recall >= self.min_recall and fp_rate <= self.max_fp_rate


SUCCESS_CRITERIA = SuccessCriteria()


# ---------------------------------------------------------------------------
# 3. Capacidade da equipa SOC — volume de alertas esperado
# ---------------------------------------------------------------------------

ANALYST_DAILY_CAPACITY = 50
"""Alertas que um analista SOC nível 1 consegue investigar por dia, sem
degradar a qualidade da análise (pressuposto: 40-60/dia)."""

PREVALENCE = 0.0499
"""Prevalência de conexões maliciosas observada no dataset."""


def expected_daily_alerts(daily_connections: int, recall: float, fp_rate: float,
                           prevalence: float = PREVALENCE) -> float:
    """Nº esperado de alertas/dia = volume * (prevalência*recall + (1-prevalência)*taxa_FP)."""
    return daily_connections * (prevalence * recall + (1 - prevalence) * fp_rate)


# ---------------------------------------------------------------------------
# 4. Decisões de modelação (documentadas, não recalculadas aqui)
# ---------------------------------------------------------------------------

PREDICTION_MOMENT = "fim da conexão (flow-based, compatível com NetFlow)"
HOLDOUT_STRATEGY = "modo alerta, sem bloqueio automático, até validação com dados reais"


def summary() -> str:
    lines = [
        "=== Business Understanding — Deteção de Conexões Maliciosas ===",
        f"Custo de falso negativo: {COST_FALSE_NEGATIVE_EUR:.0f} EUR",
        f"Custo de falso positivo: {COST_FALSE_POSITIVE_EUR:.0f} EUR",
        f"Proporção FN:FP: {COST_FALSE_NEGATIVE_EUR / COST_FALSE_POSITIVE_EUR:.0f}:1",
        f"Critério de sucesso: recall >= {SUCCESS_CRITERIA.min_recall:.0%}, "
        f"taxa de falsos positivos <= {SUCCESS_CRITERIA.max_fp_rate:.0%}",
        f"Momento da predição: {PREDICTION_MOMENT}",
        f"Estratégia de holdout: {HOLDOUT_STRATEGY}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(summary())

    # Exemplo com os resultados finais obtidos em evaluation.py
    # (12 falsos negativos, 3 falsos positivos, em 3.750 conexões de teste)
    n_fn, n_fp, n_test = 12, 3, 3750
    cost = expected_cost(n_fn, n_fp)
    print(f"\nExemplo — custo esperado no teste: {cost:.0f} EUR "
          f"({n_fn} FN x {COST_FALSE_NEGATIVE_EUR:.0f} + {n_fp} FP x {COST_FALSE_POSITIVE_EUR:.0f})")

    alerts_per_day = expected_daily_alerts(daily_connections=25000, recall=0.936, fp_rate=0.0008)
    print(f"Exemplo — alertas/dia esperados (25.000 conexões/dia, recall 93,6%, FP 0,08%): "
          f"{alerts_per_day:.0f}")
