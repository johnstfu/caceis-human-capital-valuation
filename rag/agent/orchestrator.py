"""
orchestrator.py — Boucle de conversation principale du chatbot Julien.

Reçoit un message du CFAO, orchestre les sous-modules (persona, contexte BU,
retrieval, ActionStore, kpi_push, questions), et retourne une réponse argumentée.

Porte le TOGGLE reco/perso global (PersonalizationMode) :
  ON  → push recommandations + apprentissage de session actif
  OFF → réponses neutres, pas de push, pas d'apprentissage
Commutable à tout instant par l'utilisateur (utile en comité).
"""

import logging
from typing import Optional

from contracts.schemas import (
    ConversationTurn,
    KpiPush,
    PushedQuestion,
    ArbitrageProposal,
    FeedbackSignal,
    PersonalizationMode,
)
from context.cfo_persona import build_system_prompt
from context.bu_context import BUContext
from kpi_push.prioritizer import KPIPrioritizer
from questions.question_selector import QuestionSelector
from arbitrage.budget_advisor import BudgetAdvisor
from feedback.signal_logger import SignalLogger

# Imports des modules existants (ne pas dupliquer)
from retrieval.retriever import CACEISRetriever
from store.action_store import ActionStore

log = logging.getLogger(__name__)


class JulienOrchestrator:
    """
    Orchestrateur principal du chatbot Julien.

    Gère la boucle de conversation, le toggle reco/perso,
    et coordonne tous les sous-modules sans dupliquer le retrieval
    ni l'ActionStore existants.
    """

    def __init__(self, personalization_mode: PersonalizationMode = PersonalizationMode.ON):
        # TODO: instancier les sous-modules
        # TODO: instancier CACEISRetriever (singleton existant)
        # TODO: instancier ActionStore (singleton existant)
        # TODO: instancier KPIPrioritizer, QuestionSelector, BudgetAdvisor, SignalLogger
        # TODO: initialiser l'historique de conversation (list[ConversationTurn])
        raise NotImplementedError

    # ── Toggle reco/perso ─────────────────────────────────────────────────────

    def set_personalization_mode(self, mode: PersonalizationMode) -> None:
        """
        Commute le mode de personnalisation.

        Args:
            mode: PersonalizationMode.ON  → push + apprentissage actifs
                  PersonalizationMode.OFF → réponses neutres, pas d'apprentissage

        # TODO: mettre à jour self._mode, logger le changement
        """
        raise NotImplementedError

    def get_personalization_mode(self) -> PersonalizationMode:
        """Retourne le mode courant.

        # TODO: retourner self._mode
        """
        raise NotImplementedError

    # ── Boucle principale ─────────────────────────────────────────────────────

    def chat(
        self,
        user_message: str,
        bu_id: Optional[str] = None,
    ) -> ConversationTurn:
        """
        Point d'entrée principal : reçoit un message CFAO, retourne une réponse complète.

        Flux :
          1. Charger le contexte BU si bu_id fourni
          2. Construire le system prompt (cfo_persona + contexte BU)
          3. Retrieval sémantique (CACEISRetriever existant)
          4. Lookup ActionStore (gate déterministe — AUCUNE action libre)
          5. Prioriser les KPI à pousser (si mode ON)
          6. Sélectionner 1-2 questions de relance (si mode ON)
          7. Appel LLM (Claude) avec prompt composé
          8. Logger le signal d'usage (si mode ON)
          9. Retourner ConversationTurn complet

        Args:
            user_message : message texte du CFAO
            bu_id        : identifiant BU optionnel (ex: "spf__fin_treasury__admin")

        Returns:
            ConversationTurn avec réponse, kpi_pushes, questions, arbitrage si applicable

        # TODO: implémenter le flux complet ci-dessus
        # TODO: si mode OFF → skips étapes 5, 6, 8 ; réponse neutre sans push
        # TODO: gérer l'historique de conversation (ajouter le tour courant)
        """
        raise NotImplementedError

    # ── Helpers internes ──────────────────────────────────────────────────────

    def _compose_prompt(
        self,
        user_message: str,
        bu_context: Optional[dict],
        retrieved_context: str,
        actions_prompt: str,
        kpi_pushes: list[KpiPush],
        pushed_questions: list[PushedQuestion],
    ) -> tuple[str, str]:
        """
        Compose le system_prompt et le user_message final pour Claude.

        Returns:
            (system_prompt, user_message) — tuple prêt pour client.messages.create()

        # TODO: assembler system_prompt depuis build_system_prompt()
        # TODO: injecter bu_context, kpi_pushes, pushed_questions dans user_message
        # TODO: actions_prompt injecté AVANT le contexte documentaire (priorité gate)
        # TODO: si mode OFF → supprimer les instructions de push et de relance
        """
        raise NotImplementedError

    def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """
        Appel Claude Sonnet via client Anthropic.

        Args:
            system_prompt : prompt système composé
            user_message  : message utilisateur enrichi

        Returns:
            str — réponse brute du modèle

        # TODO: utiliser os.getenv("ANTHROPIC_API_KEY")
        # TODO: model = "claude-sonnet-4-6", max_tokens = 1200
        # TODO: injecter l'historique de conversation (messages précédents)
        """
        raise NotImplementedError

    def reset_conversation(self) -> None:
        """
        Réinitialise l'historique de conversation.

        # TODO: vider self._history
        # TODO: NE PAS réinitialiser feedback_store (persistant entre sessions)
        """
        raise NotImplementedError
