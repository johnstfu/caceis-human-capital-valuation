"""
bu_context.py — Charge et formate le contexte d'une BU depuis kpi-output.json.

CONTRAINTE : lecture agrégée uniquement (niveau BU).
Aucun accès à des données individuelles. Source = rag/data/kpi-output.json exclusivement.
"""

import json
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

KPI_OUTPUT_PATH = Path(__file__).parent.parent.parent / "data" / "kpi-output.json"


class BUContext:
    """
    Fournit le contexte KPI d'une BU pour injection dans le prompt.

    Lit kpi-output.json en lecture seule — ne modifie jamais la source de vérité.
    Agrégation BU uniquement : aucune donnée individuelle n'est chargée ni exposée.
    """

    def __init__(self):
        # TODO: charger kpi-output.json à l'init (lazy ou eager — à décider)
        # TODO: indexer les BUs par id et par name pour lookup rapide
        raise NotImplementedError

    def get_bu_by_id(self, bu_id: str) -> Optional[dict]:
        """
        Retourne le dict KPI complet d'une BU par son identifiant.

        Args:
            bu_id : ex. "spf__fin_treasury__admin"

        Returns:
            dict KPI de la BU, ou None si non trouvée

        # TODO: lookup dans self._bu_index
        # TODO: retourner une copie (ne pas exposer la référence mutable)
        """
        raise NotImplementedError

    def get_bu_by_name(self, name: str) -> Optional[dict]:
        """
        Recherche une BU par nom (insensible à la casse, partial match toléré).

        Args:
            name : ex. "Finance & Admin", "finance admin", "SPF"

        Returns:
            dict KPI de la BU, ou None si non trouvée

        # TODO: normaliser name (lowercase, strip)
        # TODO: chercher exact match puis partial match
        # TODO: gérer l'alias SPF → Finance & Admin
        """
        raise NotImplementedError

    def format_for_prompt(self, bu_data: dict) -> str:
        """
        Formate les KPIs d'une BU pour injection dans le message utilisateur.

        Args:
            bu_data : dict retourné par get_bu_by_id() ou get_bu_by_name()

        Returns:
            str multi-ligne : nom BU, KPIs avec statut vs groupe, rang, effectif

        # TODO: reprendre le format de generator._build_kpi_summary()
        # TODO: ajouter le pont NBI/FTE (n_employees × NBI_FTE_REFERENCE_KEU)
        # TODO: ne jamais exposer de données à granularité inférieure au BU
        """
        raise NotImplementedError

    def list_all_bus(self) -> list[dict]:
        """
        Retourne la liste de toutes les BUs avec leurs KPIs et rangs.

        Returns:
            list[dict] triée par rang V_HC croissant (rang 1 = meilleur)

        # TODO: retourner une copie de self._bus triée par rank
        """
        raise NotImplementedError

    def get_group_summary(self) -> dict:
        """
        Retourne les statistiques groupe (moyennes, percentiles).

        Returns:
            dict group_summary extrait de kpi-output.json

        # TODO: retourner self._group_summary
        """
        raise NotImplementedError
