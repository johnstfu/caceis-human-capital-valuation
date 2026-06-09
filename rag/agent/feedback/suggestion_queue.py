"""
suggestion_queue.py — File des suggestions de Julien en attente de gate humaine.

PÉRIMÈTRE STRICT : enregistre les suggestions de recommandations écrites par Julien
(reco qu'il aurait voulu faire mais absente de la bibliothèque).
Ces suggestions sont taggées "suggéré par l'utilisateur, NON validé".

RÈGLE ABSOLUE : une suggestion ne sort JAMAIS de cette file vers l'ActionStore
sans validation humaine explicite (RH + Gouvernance). L'agent ne la présente
jamais comme action officielle tant que statut ≠ "validated".

Ce module ne stocke JAMAIS de données nominatives. Les suggestions décrivent
des actions RH génériques, jamais des individus.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from contracts.schemas import UserSuggestion

log = logging.getLogger(__name__)

SUGGESTION_QUEUE_PATH = Path(__file__).parent / "store" / "suggestion_queue.json"

SuggestionStatus = Literal["pending", "validated", "rejected"]


class SuggestionQueue:
    """
    File d'attente des suggestions de Julien.

    Flux complet :
    1. Julien écrit une suggestion → statut "pending"
    2. Signal de ranking immédiat (priorité d'affichage dans la session)
    3. Gate humaine (RH + Gouvernance) → statut "validated" ou "rejected"
    4. Si "validated" → peut être ajoutée à action_library_raw.json manuellement
    5. L'agent NE sort JAMAIS une suggestion "pending" comme action officielle

    IMPORTANT : ce module ne contient JAMAIS de données nominatives.
    """

    def __init__(self):
        # TODO: créer suggestion_queue.json si absent (liste vide)
        # TODO: charger les suggestions existantes en mémoire
        raise NotImplementedError

    def add_suggestion(
        self,
        suggestion_text: str,
        kpi_target: str,
        context_bu_id: Optional[str] = None,
    ) -> UserSuggestion:
        """
        Ajoute une suggestion de Julien dans la file en statut "pending".

        Args:
            suggestion_text : description de la reco suggérée (action RH générique)
            kpi_target      : KPI concerné ("Y", "lambda", "beta", "rho", "P")
            context_bu_id   : BU du contexte (ID agrégé, jamais nominatif)

        Returns:
            UserSuggestion créée avec statut "pending" et timestamp

        # TODO: générer un suggestion_id unique (ex: "SUG_001")
        # TODO: créer UserSuggestion(text=..., status="pending", created_at=now)
        # TODO: persister dans SUGGESTION_QUEUE_PATH
        # TODO: retourner la suggestion créée
        # TODO: ⚠️ NE PAS ajouter à l'ActionStore — file d'attente seulement
        """
        raise NotImplementedError

    def get_pending_suggestions(self) -> list[UserSuggestion]:
        """
        Retourne toutes les suggestions en attente de validation.

        Returns:
            list[UserSuggestion] avec statut "pending", triées par date décroissante

        # TODO: filtrer self._suggestions sur status == "pending"
        """
        raise NotImplementedError

    def validate_suggestion(self, suggestion_id: str) -> UserSuggestion:
        """
        Marque une suggestion comme validée (action humaine explicite).

        Args:
            suggestion_id : ID de la suggestion à valider

        Returns:
            UserSuggestion mise à jour

        # TODO: trouver la suggestion par ID
        # TODO: changer statut → "validated", ajouter validated_at
        # TODO: persister
        # TODO: NE PAS modifier action_library_raw.json — étape manuelle séparée
        """
        raise NotImplementedError

    def reject_suggestion(self, suggestion_id: str) -> UserSuggestion:
        """
        Marque une suggestion comme rejetée.

        # TODO: même logique que validate mais statut → "rejected"
        """
        raise NotImplementedError

    def is_validated(self, suggestion_id: str) -> bool:
        """
        Vérifie si une suggestion est validée.

        Returns:
            bool — True uniquement si statut == "validated"

        # TODO: lookup par ID → return status == "validated"
        # TODO: GUARD CLAUSE : si ID non trouvé → return False (pas d'erreur silencieuse)
        """
        raise NotImplementedError
