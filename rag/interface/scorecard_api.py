"""
scorecard_api.py — Interface principale du système RAG CACEIS.

Fonctions publiques :
  get_bu_scorecard(bu_name)   → scorecard d'une BU
  get_all_scorecards()        → scorecards de toutes les BUs
  list_bus()                  → liste des BUs disponibles
  index_status()              → statut de l'index ChromaDB
"""

import json
import logging
import sys
from pathlib import Path

# Ajoute le dossier parent (rag/) au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from pipeline.rag_pipeline import CACEISRAGPipeline

log = logging.getLogger(__name__)

# Chemin vers le fichier KPI
KPI_JSON = Path(__file__).parent.parent / "data" / "kpi-output.json"

# Pipeline singleton (chargé une seule fois)
_pipeline: CACEISRAGPipeline = None


def _get_pipeline() -> CACEISRAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = CACEISRAGPipeline()
    return _pipeline


def _load_kpi_data() -> dict:
    """Charge kpi-output.json et indexe les BUs par nom."""
    if not KPI_JSON.exists():
        raise FileNotFoundError(f"kpi-output.json introuvable : {KPI_JSON}")
    raw = json.loads(KPI_JSON.read_text(encoding="utf-8"))
    # Indexe par nom de BU
    index = {}
    for bu in raw.get("business_units", []):
        index[bu["name"]] = bu
    return index


# ── API publique ──────────────────────────────────────────────────────────────

def list_bus() -> list[str]:
    """
    Retourne la liste des BUs disponibles dans kpi-output.json.
    """
    data = _load_kpi_data()
    return sorted(data.keys())


def get_bu_scorecard(bu_name: str) -> dict:
    """
    Génère le scorecard RAG complet pour une BU.

    Args:
        bu_name : nom exact de la BU (ex: "Finance & Admin")

    Returns:
        dict scorecard avec recommandations, sources, confiance

    Usage :
        from interface.scorecard_api import get_bu_scorecard
        scorecard = get_bu_scorecard("Finance & Admin")
        print(scorecard["recommendations"])
    """
    kpi_index = _load_kpi_data()

    # Recherche flexible (case-insensitive, partielle)
    if bu_name not in kpi_index:
        lower_name = bu_name.lower()
        matches = [k for k in kpi_index if lower_name in k.lower()]
        if not matches:
            raise ValueError(
                f"BU '{bu_name}' introuvable. BUs disponibles : {list(kpi_index.keys())}"
            )
        bu_name = matches[0]
        log.info(f"BU name fuzzy match : '{bu_name}'")

    kpi_data  = kpi_index[bu_name]
    pipeline  = _get_pipeline()
    scorecard = pipeline.generate_bu_scorecard(bu_name, kpi_data)

    return scorecard


def get_all_scorecards(skip_existing: bool = True) -> list[dict]:
    """
    Génère les scorecards pour toutes les BUs dans kpi-output.json.

    Args:
        skip_existing : si True, charge depuis le cache si disponible

    Returns:
        list de scorecards triés par V_HC décroissant
    """
    kpi_index  = _load_kpi_data()
    pipeline   = _get_pipeline()
    scorecards = []

    # Tri par V_HC décroissant
    bus_sorted = sorted(
        kpi_index.items(),
        key=lambda x: x[1].get("v_hc_index", 0),
        reverse=True,
    )

    for i, (bu_name, kpi_data) in enumerate(bus_sorted, 1):
        log.info(f"\n[{i}/{len(bus_sorted)}] {bu_name}")
        try:
            sc = pipeline.generate_bu_scorecard(bu_name, kpi_data)
            scorecards.append(sc)
        except Exception as e:
            log.error(f"Erreur scorecard {bu_name}: {e}")
            scorecards.append({
                "bu_name":       bu_name,
                "error":         str(e),
                "recommendations": [],
            })

    return scorecards


def index_status() -> dict:
    """
    Retourne le statut de l'index ChromaDB.

    Returns:
        {"chunks_total": int, "sources": list[str]}
    """
    pipeline = _get_pipeline()
    return pipeline.index_status()
