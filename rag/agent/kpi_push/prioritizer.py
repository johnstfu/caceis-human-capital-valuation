"""
prioritizer.py — Ordonne les KPI à pousser proactivement au CFAO.

Combien et lesquels pousser dépend du contexte BU, de l'historique de conversation,
et des poids appris par feedback/ranking_updater.
Par défaut : Y, P, ρ (board-level). λ et β sont leviers opérationnels, poussés en second.
"""

import logging
from typing import Optional

from contracts.schemas import KpiPush
from kpi_push.thresholds import KpiThreshold, get_board_level_kpis, get_threshold

log = logging.getLogger(__name__)

# Nombre max de KPI poussés par tour de conversation
MAX_KPI_PUSH = 3


class KPIPrioritizer:
    """
    Détermine quels KPI pousser et dans quel ordre pour un contexte donné.

    Prend en compte :
    - Les gaps de la BU vs groupe (seuils thresholds.py)
    - Les poids appris (feedback/ranking_updater)
    - L'historique de la conversation (évite de répéter les mêmes KPI)
    - Le mode board-level (priorité Y, P, ρ) vs opérationnel (λ, β)
    """

    def __init__(self, learned_weights: Optional[dict] = None):
        """
        Args:
            learned_weights : poids appris par feedback/ranking_updater
                              (dict {kpi: float}) ou None pour poids par défaut

        # TODO: stocker learned_weights ou initialiser les poids par défaut
        # TODO: poids défaut : Y=1.0, P=0.9, rho=0.85, lambda=0.6, beta=0.5
        """
        raise NotImplementedError

    def prioritize(
        self,
        bu_data: dict,
        conversation_history: list,
        max_push: int = MAX_KPI_PUSH,
    ) -> list[KpiPush]:
        """
        Calcule la liste ordonnée des KPI à pousser pour ce tour de conversation.

        Args:
            bu_data              : dict KPI de la BU (depuis bu_context)
            conversation_history : historique des tours précédents
            max_push             : nombre max de KPI à retourner

        Returns:
            list[KpiPush] triée par priorité décroissante (max max_push items)

        # TODO: pour chaque KPI board-level, calculer un score de priorité :
        #   score = gap_score × threshold_weight × learned_weight
        #   où gap_score = distance normalisée au seuil d'alerte
        # TODO: pénaliser les KPI déjà poussés dans les 2 derniers tours
        # TODO: retourner les max_push premiers
        """
        raise NotImplementedError

    def _compute_gap_score(self, kpi: str, bu_data: dict) -> float:
        """
        Calcule un score de gap normalisé [0, 1] pour un KPI et une BU.

        Args:
            kpi     : "Y" | "lambda" | "beta" | "rho" | "P"
            bu_data : dict KPI de la BU

        Returns:
            float — 0 = pas de gap, 1 = gap maximal

        # TODO: comparer la valeur BU au threshold_alert et threshold_warn
        # TODO: normaliser entre 0 et 1
        # TODO: P = 0 toujours (indicateur de résultat — pas de levier direct)
        """
        raise NotImplementedError

    def update_weights(self, new_weights: dict) -> None:
        """
        Met à jour les poids appris (appelé par ranking_updater).

        Args:
            new_weights : dict {kpi: float} depuis feedback/ranking_updater

        # TODO: valider que les clés sont des KPIs connus
        # TODO: mettre à jour self._weights
        """
        raise NotImplementedError
