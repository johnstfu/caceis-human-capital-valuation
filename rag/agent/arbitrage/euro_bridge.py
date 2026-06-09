"""
euro_bridge.py — Traduit un score V_HC en langage financier via NBI/FTE.

Ancrage : NBI/FTE ≈ 315 k€/tête (source : kpi-output.json, série 2022-2025).
Pont entre score humain et euros pour le discours CFAO.

Formule de base :
  impact_keu = delta_vhc × n_employees × NBI_FTE_KEU × sensitivity_factor
"""

import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)

# Ratio NBI/FTE de référence (k€/tête) — mis à jour annuellement
NBI_FTE_KEU = 315.0

# Facteur de sensibilité V_HC → NBI/FTE (à calibrer en workshop CFAO)
# Représente : une hausse de 0.01 V_HC = sensitivity_factor % de NBI/FTE
DEFAULT_SENSITIVITY = 0.08  # 8 % de corrélation — à valider empiriquement


@dataclass
class ImpactEstimate:
    """
    Estimation d'impact financier d'une amélioration V_HC.

    Attributes:
        delta_vhc         : amélioration V_HC visée (ex: 0.05)
        n_employees       : effectif de la BU
        nbi_fte_keu       : ratio NBI/FTE utilisé (k€)
        sensitivity       : facteur de sensibilité appliqué
        impact_keu_low    : borne basse de l'impact (k€)
        impact_keu_high   : borne haute de l'impact (k€)
        impact_keu_mid    : valeur centrale (k€)
        assumptions       : hypothèses utilisées (texte libre)
    """
    delta_vhc: float
    n_employees: int
    nbi_fte_keu: float
    sensitivity: float
    impact_keu_low: float
    impact_keu_high: float
    impact_keu_mid: float
    assumptions: str


class EuroBridge:
    """
    Convertit des variations de V_HC en estimations d'impact financier.

    Usage principal : fournir au CFAO un ordre de grandeur en euros
    pour justifier une décision d'investissement RH.

    ⚠️ Les estimations sont des ordres de grandeur, pas des projections financières.
    Toujours présenter avec les bornes basse/haute et les hypothèses.
    """

    def __init__(
        self,
        nbi_fte_keu: float = NBI_FTE_KEU,
        sensitivity: float = DEFAULT_SENSITIVITY,
    ):
        """
        Args:
            nbi_fte_keu : ratio NBI/FTE de référence (k€/tête)
            sensitivity : facteur de sensibilité V_HC → NBI/FTE

        # TODO: stocker nbi_fte_keu et sensitivity
        """
        raise NotImplementedError

    def estimate_impact(
        self,
        delta_vhc: float,
        n_employees: int,
    ) -> ImpactEstimate:
        """
        Estime l'impact financier d'une amélioration V_HC pour une BU.

        Formule :
          impact_mid  = delta_vhc × n_employees × nbi_fte_keu × sensitivity
          impact_low  = impact_mid × 0.6   (borne conservatrice)
          impact_high = impact_mid × 1.4   (borne optimiste)

        Args:
            delta_vhc    : amélioration V_HC visée (ex: 0.05 pour +5 pts)
            n_employees  : effectif de la BU

        Returns:
            ImpactEstimate avec bornes basse/haute et hypothèses

        # TODO: calculer impact_mid, impact_low, impact_high
        # TODO: rédiger les assumptions (nbi_fte utilisé, sensitivity, date calibration)
        # TODO: retourner ImpactEstimate
        """
        raise NotImplementedError

    def format_for_cfao(self, estimate: ImpactEstimate) -> str:
        """
        Formate l'estimation en langage CFAO (k€ ou M€ selon magnitude).

        Args:
            estimate : ImpactEstimate calculée

        Returns:
            str — ex: "Impact estimé : 280–650 k€ (médiane 420 k€)
                       Hypothèses : NBI/FTE 315 k€/tête, sensibilité 8 %"

        # TODO: choisir k€ ou M€ selon la magnitude
        # TODO: inclure les bornes et les hypothèses en 2 lignes max
        # TODO: toujours qualifier : "ordre de grandeur", pas "projection"
        """
        raise NotImplementedError
