"""
thresholds.py — Seuils d'alerte par KPI pour le push proactif vers le CFAO.

Paramétrables : ajustables en workshop avec le CFAO sans toucher à la logique.
Deux niveaux : ALERT (écart significatif) et WARNING (à surveiller).
"""

from dataclasses import dataclass
from typing import Literal


KpiKey = Literal["Y", "lambda", "beta", "rho", "P"]
ThresholdType = Literal["lower_bad", "higher_bad", "special"]


@dataclass
class KpiThreshold:
    """
    Seuil d'alerte pour un KPI donné.

    Attributes:
        kpi_key       : clé dans kpi-output.json (ex: "kpi_Y")
        display_name  : label affiché au CFAO (ex: "Engagement (Y)")
        threshold_alert  : valeur déclenchant une alerte forte (priorité haute)
        threshold_warn   : valeur déclenchant un avertissement (priorité moyenne)
        direction        : "lower_bad" = valeur basse = problème, "higher_bad" = inverse
        board_level      : True si KPI prioritaire pour le CFAO (Y, P, ρ)
        unit             : unité d'affichage (ex: "/5", "h/emp/an", "%")
        group_mean       : moyenne groupe CACEIS (référence de comparaison)
    """
    kpi_key: str
    display_name: str
    threshold_alert: float
    threshold_warn: float
    direction: ThresholdType
    board_level: bool
    unit: str
    group_mean: float


# Seuils opérationnels par défaut — ajustables en workshop
# Source des moyennes groupe : kpi-output.json / group_summary
DEFAULT_THRESHOLDS: dict[str, KpiThreshold] = {
    # TODO: instancier KpiThreshold pour chaque KPI avec les valeurs ci-dessous :
    #
    # Y — Engagement (/5)
    #   alert  : < 3.20 (critique)
    #   warn   : < 3.40 (sous la moyenne CACEIS)
    #   board_level : True
    #
    # lambda — Formation (h/emp/an)
    #   alert  : < 30h
    #   warn   : < 44.6h (sous la moyenne CACEIS)
    #   board_level : False
    #
    # beta — Qualité formation (/5)
    #   alert  : < 3.20
    #   warn   : < 3.40
    #   board_level : False
    #
    # rho — Absentéisme (%)
    #   direction : higher_bad
    #   alert  : > 0.055 (> 5.5%)
    #   warn   : > 0.048 (> 4.8% moyenne CACEIS)
    #   board_level : True
    #   ⚠️ scope France uniquement — documenter la limitation dans display_name
    #
    # P — Productivité (CAGR NBI/FTE)
    #   direction : special (indicateur de résultat, pas de levier direct)
    #   board_level : True
}


def get_threshold(kpi: str) -> KpiThreshold:
    """
    Retourne le seuil configuré pour un KPI donné.

    Args:
        kpi : clé KPI ("Y", "lambda", "beta", "rho", "P")

    Returns:
        KpiThreshold

    Raises:
        KeyError si le KPI n'est pas dans DEFAULT_THRESHOLDS

    # TODO: return DEFAULT_THRESHOLDS[kpi]
    """
    raise NotImplementedError


def get_board_level_kpis() -> list[str]:
    """
    Retourne la liste des KPIs board-level (Y, P, ρ).

    Returns:
        list[str] des KPIs avec board_level=True, triés par priorité défaut

    # TODO: filtrer DEFAULT_THRESHOLDS sur board_level=True
    # TODO: ordre par défaut : Y, P, rho
    """
    raise NotImplementedError
