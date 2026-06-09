"""
question_selector.py — Sélectionne les 1-2 questions de relance à pousser au CFAO.

Prend en compte le contexte courant (KPI en gap, historique de conversation)
et les poids appris (feedback/ranking_updater) pour éviter les répétitions.
"""

import logging
from typing import Optional

from contracts.schemas import PushedQuestion
from questions.question_pool import RelanceQuestion, get_questions_by_trigger, get_questions_by_kpi

log = logging.getLogger(__name__)

MAX_QUESTIONS_PER_TURN = 2


class QuestionSelector:
    """
    Sélectionne contextuellement les questions de relance à pousser.

    Évite les répétitions sur les N derniers tours.
    Favorise les questions validées (signal positif feedback).
    """

    def __init__(self, learned_weights: Optional[dict] = None):
        """
        Args:
            learned_weights : poids appris par feedback/ranking_updater
                              {question_id: float} ou None pour poids par défaut

        # TODO: stocker learned_weights
        # TODO: poids défaut : 1.0 pour toutes les questions
        """
        raise NotImplementedError

    def select(
        self,
        kpi_gaps: list[str],
        conversation_history: list,
        context_triggers: Optional[list[str]] = None,
        max_questions: int = MAX_QUESTIONS_PER_TURN,
    ) -> list[PushedQuestion]:
        """
        Sélectionne les questions les plus pertinentes pour ce tour.

        Args:
            kpi_gaps             : KPIs en gap (depuis action_store ou prioritizer)
            conversation_history : historique des tours (pour éviter répétitions)
            context_triggers     : triggers supplémentaires ("arbitrage", "compare_history")
            max_questions        : max questions à retourner (défaut 2)

        Returns:
            list[PushedQuestion] — les questions sélectionnées avec leur justification

        # TODO: construire le pool de questions candidats depuis kpi_gaps + context_triggers
        # TODO: scorer chaque question : learned_weight × (1 - récence_penalty)
        # TODO: pénaliser questions posées dans les 3 derniers tours
        # TODO: retourner les max_questions meilleures
        """
        raise NotImplementedError

    def update_weights(self, new_weights: dict) -> None:
        """
        Met à jour les poids appris (appelé par ranking_updater).

        Args:
            new_weights : dict {question_id: float}

        # TODO: valider les clés (IDs existants dans QUESTION_POOL)
        # TODO: mettre à jour self._weights
        """
        raise NotImplementedError

    def _was_recently_asked(self, question_id: str, history: list, n_turns: int = 3) -> bool:
        """
        Vérifie si une question a déjà été posée dans les n_turns derniers tours.

        Args:
            question_id : ID de la question à vérifier
            history     : historique des ConversationTurn
            n_turns     : fenêtre de récence

        Returns:
            bool

        # TODO: parcourir les n_turns derniers tours
        # TODO: chercher question_id dans turn.pushed_questions
        """
        raise NotImplementedError
