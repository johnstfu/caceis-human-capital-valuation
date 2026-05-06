"""
action_store.py — Lookup déterministe des actions RH par gap KPI.

Source : data/action_library_raw.json (26 actions, nomenclature V_HC).

Pour chaque BU, détecte les KPIs en gap et retourne les actions
correspondantes, triées par priorité (a_completer: false en premier).
"""

import json
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

ACTION_LIBRARY_PATH = Path(__file__).parent.parent / "data" / "action_library_raw.json"

# Seuils de gap par KPI (nomenclature V_HC)
# type "lower_bad"  → gap si valeur < threshold
# type "higher_bad" → gap si valeur > threshold
# type "special"    → traitement dédié (P)
KPI_THRESHOLDS = {
    "Y": {"type": "lower_bad",  "threshold": 3.40,  "kpi_key": "kpi_Y"},
    "λ": {"type": "lower_bad",  "threshold": 44.6,  "kpi_key": "kpi_lambda"},
    "β": {"type": "lower_bad",  "threshold": 3.40,  "kpi_key": "kpi_beta_qr"},
    "ρ": {"type": "higher_bad", "threshold": 0.048, "kpi_key": "kpi_rho"},
    "P": {"type": "special",    "kpi_key":   "kpi_P"},
}

# Moyenne groupe λ (heures/emp/an) pour le pattern career_development
LAMBDA_MEAN = 44.6

# Messages spéciaux
P_MESSAGE = (
    "P est un indicateur de résultat. "
    "Les leviers directs sont Y (engagement), λ (formation) et β (QVCT). "
    "Aucune action directe sur P n'est disponible dans la bibliothèque."
)
RHO_GAP_NOTE = (
    "Actions limitées sur ce KPI — "
    "les leviers disponibles sont indirects via β (QVCT)."
)


class ActionStore:
    """
    Charge action_library_raw.json et expose les méthodes de lookup
    par gap KPI pour l'intégration dans le pipeline RAG.
    """

    _instance = None  # singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def _load(self):
        if self._loaded:
            return
        if not ACTION_LIBRARY_PATH.exists():
            raise FileNotFoundError(
                f"action_library_raw.json introuvable : {ACTION_LIBRARY_PATH}"
            )
        raw = json.loads(ACTION_LIBRARY_PATH.read_text(encoding="utf-8"))
        # ACT_013 retirée (sessions 2024 annulées — levier non actif)
        self._actions = [
            a for a in raw.get("actions", [])
            if a["action_id"] != "ACT_013"
        ]
        self._gap_notes = {
            gn["kpi"]: gn["message"]
            for gn in raw.get("metadata", {}).get("gap_notes", [])
        }
        self._loaded = True
        log.info(f"ActionStore chargé : {len(self._actions)} actions")

    # ─────────────────────────────────────────────── API publique

    def detect_gaps(self, kpi_data: dict) -> list:
        """
        Retourne la liste des KPIs en gap pour une BU donnée.

        Args:
            kpi_data : dict KPI de la BU (clés : kpi_Y, kpi_lambda, etc.)

        Returns:
            list de str — ex: ["Y", "ρ"]
        """
        self._load()
        gaps = []
        for kpi, cfg in KPI_THRESHOLDS.items():
            if cfg["type"] == "special":
                continue
            val = kpi_data.get(cfg["kpi_key"])
            if val is None:
                continue
            if cfg["type"] == "lower_bad" and val < cfg["threshold"]:
                gaps.append(kpi)
            elif cfg["type"] == "higher_bad" and val > cfg["threshold"]:
                gaps.append(kpi)
        return gaps

    def is_career_dev_triggered(self, kpi_data: dict) -> bool:
        """
        Pattern career_development : Y < 3.40 ET λ >= moyenne groupe.
        Engagement faible malgré volume de formation correct
        → le problème est la trajectoire perçue, pas les heures.
        """
        self._load()
        y   = kpi_data.get("kpi_Y", 5.0)
        lam = kpi_data.get("kpi_lambda", 0.0)
        return y < 3.40 and lam >= LAMBDA_MEAN

    def get_actions_for_kpi(
        self,
        kpi: str,
        include_career_dev: bool = False,
        max_actions: int = 5,
    ) -> list:
        """
        Retourne les actions correspondant à un KPI, triées par priorité.

        Ordre :
          1. a_completer: false (bien documentées)
          2. a_completer: true  (à valider manuellement)

        Args:
            kpi              : "Y" | "λ" | "β" | "ρ"
            include_career_dev : si True, inclut les actions career_development
            max_actions      : nombre max d'actions retournées

        Returns:
            list de dicts action
        """
        self._load()
        if kpi == "P":
            return []

        matched = [
            a for a in self._actions
            if a["kpi_cible"] == kpi
            and (include_career_dev or not a.get("career_development", False))
        ]

        # Priorité : a_completer: false en premier
        matched.sort(key=lambda a: (a.get("a_completer", False), a["action_id"]))
        return matched[:max_actions]

    def get_career_dev_actions(self, max_actions: int = 4) -> list:
        """Retourne les 4 actions career_development (ACT_024 à ACT_027)."""
        self._load()
        matched = [a for a in self._actions if a.get("career_development", False)]
        matched.sort(key=lambda a: (a.get("a_completer", False), a["action_id"]))
        return matched[:max_actions]

    def get_all_actions_for_gaps(self, kpi_data: dict) -> dict:
        """
        Point d'entrée principal pour le pipeline.

        Retourne un dict structuré avec :
          - gaps           : KPIs en gap
          - actions        : {kpi → list d'actions}
          - career_dev     : True/False
          - career_dev_actions : list si triggered
          - gap_notes      : {kpi → message} pour ρ et P
          - p_message      : message spécial pour P

        Args:
            kpi_data : dict KPI de la BU

        Returns:
            dict complet pour injection dans le pipeline
        """
        self._load()
        gaps = self.detect_gaps(kpi_data)
        career_dev = self.is_career_dev_triggered(kpi_data)

        result = {
            "gaps_detected":      gaps,
            "actions":            {},
            "career_dev_triggered": career_dev,
            "career_dev_actions": [],
            "gap_notes":          {},
            "p_message":          None,
        }

        # Actions par KPI en gap
        for kpi in gaps:
            result["actions"][kpi] = self.get_actions_for_kpi(kpi)
            if kpi == "ρ":
                result["gap_notes"]["ρ"] = RHO_GAP_NOTE

        # P : message spécial (toujours affiché si P est dans les KPIs)
        if kpi_data.get("kpi_P") is not None:
            result["p_message"] = P_MESSAGE

        # Career development
        if career_dev:
            result["career_dev_actions"] = self.get_career_dev_actions()

        log.info(
            f"ActionStore — gaps: {gaps}, "
            f"actions: { {k: len(v) for k, v in result['actions'].items()} }, "
            f"career_dev: {career_dev}"
        )
        return result

    def format_for_prompt(self, action_result: dict) -> str:
        """
        Formate le résultat de get_all_actions_for_gaps() pour injection
        dans le prompt Claude comme section structurée.

        Returns:
            str multi-ligne prêt pour injection dans user_message
        """
        if not action_result["gaps_detected"] and not action_result["p_message"]:
            return ""

        lines = ["ACTIONS PRÉ-SÉLECTIONNÉES (bibliothèque action_library_raw.json) :"]
        lines.append("Ces actions sont documentées et sourcées — intègre-les en priorité.\n")

        for kpi, actions in action_result["actions"].items():
            if not actions:
                continue
            lines.append(f"── KPI {kpi} (gap détecté) ──")
            for a in actions:
                status = " [À COMPLÉTER]" if a.get("a_completer") else ""
                lines.append(f"• {a['action_id']} — {a['titre']}{status}")
                lines.append(f"  Description : {a['description_metier']}")
                lines.append(f"  Trigger     : {a['gap_trigger']}")
                lines.append(f"  Source      : {', '.join(a['source_evidence'])}")
                lines.append(f"  Délai effet : {a['delai_effet']}")
                lines.append("")
            # Note gap ρ
            if kpi in action_result["gap_notes"]:
                lines.append(f"  ⚠ Note : {action_result['gap_notes'][kpi]}\n")

        # Career development
        if action_result["career_dev_triggered"] and action_result["career_dev_actions"]:
            lines.append("── Actions CAREER DEVELOPMENT (Y < 3.40 ET λ >= moyenne) ──")
            for a in action_result["career_dev_actions"]:
                status = " [À COMPLÉTER]" if a.get("a_completer") else ""
                lines.append(f"• {a['action_id']} — {a['titre']}{status}")
                lines.append(f"  Description : {a['description_metier']}")
                lines.append(f"  Pattern     : {a.get('pattern_trigger', a['gap_trigger'])}")
                lines.append("")

        # P message
        if action_result["p_message"]:
            lines.append(f"── KPI P ──")
            lines.append(f"  {action_result['p_message']}\n")

        return "\n".join(lines)

    def format_for_scorecard(self, action_result: dict) -> dict:
        """
        Formate pour inclusion dans le scorecard JSON final
        (consommé par le dashboard).

        Returns:
            dict avec les clés : gaps, actions_by_kpi, career_dev, gap_notes, p_message
        """
        return {
            "gaps_detected":        action_result["gaps_detected"],
            "actions_by_kpi":       {
                kpi: [
                    {
                        "action_id":              a["action_id"],
                        "titre":                  a["titre"],
                        "description_metier":     a["description_metier"],
                        "gap_trigger":            a["gap_trigger"],
                        "pattern_trigger":        a.get("pattern_trigger"),
                        "type":                   a["type"],
                        "programme_parent":       a["programme_parent"],
                        "duree":                  a["duree"],
                        "impact_attendu_metier":  a["impact_attendu_metier"],
                        "delai_effet":            a["delai_effet"],
                        "source_evidence":        a["source_evidence"],
                        "a_completer":            a.get("a_completer", False),
                        "career_development":     a.get("career_development", False),
                    }
                    for a in actions
                ]
                for kpi, actions in action_result["actions"].items()
            },
            "career_dev_triggered": action_result["career_dev_triggered"],
            "career_dev_actions":   [
                {
                    "action_id":          a["action_id"],
                    "titre":              a["titre"],
                    "description_metier": a["description_metier"],
                    "pattern_trigger":    a.get("pattern_trigger"),
                    "duree":              a["duree"],
                    "source_evidence":    a["source_evidence"],
                    "a_completer":        a.get("a_completer", False),
                }
                for a in action_result.get("career_dev_actions", [])
            ],
            "gap_notes":            action_result["gap_notes"],
            "p_message":            action_result["p_message"],
        }
