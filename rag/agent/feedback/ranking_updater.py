"""
ranking_updater.py — Met à jour les poids de ranking à partir des signaux d'usage.

PÉRIMÈTRE STRICT : met à jour les préférences d'affichage (ordre des KPI, des questions,
des actions). Ne modifie JAMAIS les scores KPI, jamais kpi-output.json,
jamais les données sources. Aucun profil individuel.
"""

import logging
from typing import Optional

log = logging.getLogger(__name__)

# Facteur d'apprentissage (taux d'update par signal) — paramétrable
LEARNING_RATE = 0.05
# Valeur minimum de poids pour éviter l'extinction complète
MIN_WEIGHT = 0.1
# Valeur maximum de poids
MAX_WEIGHT = 2.0


class RankingUpdater:
    """
    Met à jour les poids de ranking KPI, questions et actions
    à partir des signaux journalisés par SignalLogger.

    Règles d'apprentissage :
    - Signal positif (kpi_explored, question_retained, action_validated)
      → augmente le poids de LEARNING_RATE
    - Signal négatif (question_ignored, action_rejected)
      → diminue le poids de LEARNING_RATE / 2 (asymétrique : apprend plus vite des succès)
    - Poids clampé dans [MIN_WEIGHT, MAX_WEIGHT]

    IMPORTANT : ce module ne lit/écrit que des poids de ranking (floats).
    Il n'accède pas aux données RH, aux KPIs des BUs, ni aux données individuelles.
    """

    def __init__(self, signal_logger):
        """
        Args:
            signal_logger : instance de SignalLogger (source des compteurs)

        # TODO: stocker la référence signal_logger
        # TODO: charger les poids courants depuis feedback_store.json
        """
        raise NotImplementedError

    def compute_updated_weights(self) -> dict:
        """
        Calcule les nouveaux poids depuis les compteurs de SignalLogger.

        Returns:
            dict avec sous-dicts :
              kpi_weights      : {kpi: float}
              question_weights : {question_id: float}
              action_weights   : {action_id: float}

        # TODO: récupérer les compteurs depuis signal_logger.get_counts()
        # TODO: appliquer la formule : poids_nouveau = poids_courant + LEARNING_RATE × delta
        #   où delta = (signaux_positifs - signaux_négatifs × 0.5) normalisé
        # TODO: clamper dans [MIN_WEIGHT, MAX_WEIGHT]
        # TODO: retourner le dict complet
        """
        raise NotImplementedError

    def push_weights_to_modules(
        self,
        kpi_prioritizer,
        question_selector,
    ) -> None:
        """
        Pousse les poids mis à jour vers KPIPrioritizer et QuestionSelector.

        Args:
            kpi_prioritizer   : instance KPIPrioritizer
            question_selector : instance QuestionSelector

        # TODO: appeler compute_updated_weights()
        # TODO: appeler kpi_prioritizer.update_weights(weights["kpi_weights"])
        # TODO: appeler question_selector.update_weights(weights["question_weights"])
        # TODO: persister les poids dans feedback_store.json
        """
        raise NotImplementedError

    def reset_weights(self) -> None:
        """
        Réinitialise tous les poids à 1.0 (réinitialisation manuelle).

        # TODO: remettre tous les poids à 1.0
        # TODO: persister dans feedback_store.json
        # TODO: logger la réinitialisation
        """
        raise NotImplementedError
