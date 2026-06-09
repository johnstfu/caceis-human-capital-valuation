"""
budget_advisor.py — Argumente un arbitrage budgétaire inter-BUs.

Répond à la question CFAO : "Quelle BU renforcer ou réduire,
et pourquoi ?" en s'appuyant sur les KPI V_HC + le pont euro (euro_bridge).

Positionné comme instrument d'arbitrage CFAO, pas comme décision RH.
Ne se prononce jamais sur des individus. Argumente depuis l'ActionStore uniquement.
"""

import logging
from typing import Optional

from contracts.schemas import ArbitrageProposal
from arbitrage.euro_bridge import EuroBridge

log = logging.getLogger(__name__)

# Nombre max de BUs comparées dans une proposition d'arbitrage
MAX_BUS_COMPARED = 5


class BudgetAdvisor:
    """
    Conseiller d'arbitrage budgétaire pour le CFAO.

    Analyse les BUs selon leur V_HC, identifie les opportunités de gain
    (BUs sous-performantes avec fort potentiel), et traduit en euros
    via EuroBridge (NBI/FTE × effectif × delta V_HC).

    Contraintes :
    - Argumente depuis les KPIs agrégés (BU level) uniquement
    - Cite toujours la source (ActionStore IDs)
    - Ne propose jamais de décision RH individuelle
    - Ne se substitue pas au CHRO pour les décisions de recrutement/licenciement
    """

    def __init__(self, bu_context, action_store, euro_bridge: Optional[EuroBridge] = None):
        """
        Args:
            bu_context   : instance BUContext (chargé depuis kpi-output.json)
            action_store : instance ActionStore (singleton existant)
            euro_bridge  : instance EuroBridge (créée si None)

        # TODO: stocker les références
        # TODO: instancier EuroBridge si non fourni
        """
        raise NotImplementedError

    def propose_arbitrage(
        self,
        target_budget_keu: Optional[float] = None,
        focus_kpis: Optional[list[str]] = None,
        top_n_bus: int = 3,
    ) -> ArbitrageProposal:
        """
        Génère une proposition d'arbitrage budgétaire inter-BUs.

        Args:
            target_budget_keu : enveloppe budgétaire disponible (k€, optionnel)
            focus_kpis        : KPIs à prioriser (défaut : Y, P, ρ — board-level)
            top_n_bus         : nombre de BUs dans la comparaison

        Returns:
            ArbitrageProposal avec BUs recommandées, actions associées, impact €

        # TODO: charger toutes les BUs via bu_context.list_all_bus()
        # TODO: scorer chaque BU = potentiel de gain × coût estimé d'intervention
        # TODO: sélectionner les top_n_bus avec le meilleur ratio gain/coût
        # TODO: pour chaque BU sélectionnée, récupérer les actions ActionStore
        # TODO: traduire en euros via euro_bridge.estimate_impact()
        # TODO: si target_budget_keu fourni, filtrer les actions dans l'enveloppe
        # TODO: construire et retourner ArbitrageProposal
        """
        raise NotImplementedError

    def compare_bus(
        self,
        bu_ids: list[str],
        kpi: Optional[str] = None,
    ) -> dict:
        """
        Compare plusieurs BUs sur un KPI donné ou sur V_HC global.

        Args:
            bu_ids : liste d'IDs de BUs à comparer
            kpi    : KPI de comparaison (None = V_HC composite)

        Returns:
            dict avec classement, valeurs, écarts au groupe

        # TODO: charger les BUs via bu_context.get_bu_by_id()
        # TODO: trier par valeur KPI décroissante
        # TODO: calculer l'écart à la moyenne groupe
        # TODO: retourner le tableau de comparaison
        """
        raise NotImplementedError
