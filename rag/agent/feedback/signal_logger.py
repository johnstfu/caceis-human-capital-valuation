"""
signal_logger.py — Journalise les signaux d'usage anonymes du chatbot.

PÉRIMÈTRE STRICT : signaux d'usage agrégés UNIQUEMENT.
Ce module ne stocke JAMAIS de données nominatives, de scores individuels
ou de profils par employé. Il ne modifie JAMAIS rag/data/.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal

from contracts.schemas import FeedbackSignal

log = logging.getLogger(__name__)

# Stockage séparé de rag/data/ — gitignored par défaut
FEEDBACK_STORE_PATH = Path(__file__).parent / "store" / "feedback_store.json"

SignalType = Literal[
    "kpi_explored",       # CFAO a creusé un KPI (scroll, question de suivi)
    "question_retained",  # CFAO a répondu à une question de relance
    "question_ignored",   # CFAO a ignoré une question de relance
    "action_validated",   # CFAO a validé une action de l'ActionStore
    "action_rejected",    # CFAO a rejeté une action de l'ActionStore
]


class SignalLogger:
    """
    Journalise les signaux d'usage anonymes pour le ranking_updater.

    IMPORTANT : ce module n'écrit que des identifiants (KPI keys, question IDs,
    action IDs) et des compteurs. Jamais de contenu libre, jamais de BU name
    si celui-ci peut identifier un individu (agrégation niveau BU minimum).
    """

    def __init__(self):
        # TODO: créer feedback_store.json si absent (structure vide)
        # TODO: charger les compteurs existants en mémoire
        raise NotImplementedError

    def log_signal(self, signal: FeedbackSignal) -> None:
        """
        Enregistre un signal d'usage.

        Args:
            signal : FeedbackSignal (type, identifiant, timestamp)

        # TODO: valider signal.type ∈ SignalType
        # TODO: incrémenter le compteur correspondant dans feedback_store
        # TODO: persister dans FEEDBACK_STORE_PATH
        # TODO: NE PAS logger le contenu du message utilisateur — seulement le type de signal
        """
        raise NotImplementedError

    def log_kpi_explored(self, kpi: str, bu_id: str) -> None:
        """
        Signal : le CFAO a creusé un KPI pour une BU.

        Args:
            kpi   : "Y" | "lambda" | "beta" | "rho" | "P"
            bu_id : identifiant BU agrégé (ex: "spf__fin_treasury__admin")
                    ⚠️ bu_id = identifiant de groupe, jamais d'individu

        # TODO: créer FeedbackSignal(type="kpi_explored", target_id=kpi, context_bu=bu_id)
        # TODO: appeler self.log_signal()
        """
        raise NotImplementedError

    def log_question_feedback(
        self,
        question_id: str,
        retained: bool,
    ) -> None:
        """
        Signal : une question de relance a été retenue ou ignorée.

        Args:
            question_id : ID de la question (ex: "Q_Y_01")
            retained    : True si le CFAO a répondu, False si ignoré

        # TODO: créer FeedbackSignal avec type "question_retained" ou "question_ignored"
        # TODO: appeler self.log_signal()
        """
        raise NotImplementedError

    def log_action_feedback(
        self,
        action_id: str,
        validated: bool,
    ) -> None:
        """
        Signal : une action de l'ActionStore a été validée ou rejetée.

        Args:
            action_id : ID de l'action (ex: "ACT_001")
            validated : True si validée, False si rejetée

        # TODO: créer FeedbackSignal avec type "action_validated" ou "action_rejected"
        # TODO: appeler self.log_signal()
        """
        raise NotImplementedError

    def get_counts(self) -> dict:
        """
        Retourne les compteurs courants pour le ranking_updater.

        Returns:
            dict structuré : {kpi_explored: {kpi: count}, question_retained: {id: count}, ...}

        # TODO: retourner une copie des compteurs en mémoire
        """
        raise NotImplementedError
