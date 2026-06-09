"""
question_pool.py — Banque de questions de relance pour le chatbot Julien.

Questions structurées par contexte (KPI en gap, comparaison historique, arbitrage).
Chaque question est taggée par KPI cible, contexte déclencheur et niveau (board/opérationnel).
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RelanceQuestion:
    """
    Une question de relance contextuelle.

    Attributes:
        id          : identifiant unique (ex: "Q_Y_01")
        text        : texte de la question posée au CFAO
        kpi_target  : KPI concerné ("Y", "lambda", "beta", "rho", "P", "VHC", "general")
        trigger     : condition déclencheur ("gap_Y", "compare_history", "arbitrage", "general")
        board_level : True si pertinente uniquement en vue CFAO
        follow_up   : True si question de suivi (après une question principale)
    """
    id: str
    text: str
    kpi_target: str
    trigger: str
    board_level: bool = True
    follow_up: bool = False


# Banque de questions — à enrichir en workshop avec le CFAO
QUESTION_POOL: list[RelanceQuestion] = [
    # TODO: instancier RelanceQuestion pour chaque question ci-dessous.
    # Exemples de questions à implémenter :
    #
    # Q_Y_01 : "Voulez-vous comparer l'engagement de cette BU sur les 3 dernières années ?"
    #           trigger="gap_Y", kpi_target="Y"
    #
    # Q_Y_02 : "Souhaitez-vous voir le détail du programme We Care pour cette BU ?"
    #           trigger="gap_Y", kpi_target="Y", follow_up=True
    #
    # Q_P_01 : "Voulez-vous exposer le pont NBI/FTE entre ce score et l'impact en euros ?"
    #           trigger="general", kpi_target="P", board_level=True
    #
    # Q_RHO_01 : "L'absentéisme de cette BU est-il corrélé à un pic saisonnier ?"
    #            trigger="gap_rho", kpi_target="rho"
    #
    # Q_ARB_01 : "Souhaitez-vous comparer les 3 BUs avec le plus fort potentiel de gain V_HC ?"
    #            trigger="arbitrage", kpi_target="VHC"
    #
    # Q_ARB_02 : "Voulez-vous simuler l'impact budgétaire d'un +0.5pt d'engagement sur 2 BUs ?"
    #            trigger="arbitrage", kpi_target="Y"
    #
    # Q_GEN_01 : "Y a-t-il une BU dont vous souhaitez approfondir le profil V_HC ?"
    #            trigger="general", kpi_target="general", board_level=True
]


def get_questions_by_trigger(trigger: str) -> list[RelanceQuestion]:
    """
    Filtre les questions par contexte déclencheur.

    Args:
        trigger : "gap_Y" | "gap_rho" | "arbitrage" | "compare_history" | "general"

    Returns:
        list[RelanceQuestion] filtrée et triée par board_level desc

    # TODO: filtrer QUESTION_POOL sur trigger
    # TODO: trier board_level=True en premier
    """
    raise NotImplementedError


def get_questions_by_kpi(kpi: str) -> list[RelanceQuestion]:
    """
    Filtre les questions par KPI cible.

    Args:
        kpi : "Y" | "lambda" | "beta" | "rho" | "P" | "VHC" | "general"

    Returns:
        list[RelanceQuestion]

    # TODO: filtrer QUESTION_POOL sur kpi_target
    """
    raise NotImplementedError
