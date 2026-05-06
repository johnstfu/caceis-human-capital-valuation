"""
rag_pipeline.py — Orchestre retrieve → action_store → generate pour une BU.
"""

import logging

from retrieval.retriever import CACEISRetriever
from generation.generator import CACEISGenerator
from store.action_store import ActionStore

log = logging.getLogger(__name__)


class CACEISRAGPipeline:

    def __init__(self):
        self.retriever     = CACEISRetriever()
        self.generator     = CACEISGenerator()
        self.action_store  = ActionStore()

    def generate_bu_scorecard(self, bu_name: str, kpi_data: dict) -> dict:
        """
        Génère le scorecard complet d'une BU.

        Args:
            bu_name  : "Finance & Admin"
            kpi_data : dict KPI extrait de kpi-output.json

        Returns:
            scorecard dict avec recommandations citées + actions structurées
        """
        log.info(f"\n{'='*60}")
        log.info(f"RAG Pipeline — BU : {bu_name}")

        # 1. Construit la query sémantique
        query = self._build_query(bu_name, kpi_data)
        log.info(f"Query : {query[:100]}…")

        # 2. Récupère le contexte pertinent (top-7 chunks)
        chunks  = self.retriever.retrieve(query, top_k=7)
        context = self.retriever.format_context(chunks)

        # 3. Lookup action_library_raw.json par gap KPI (déterministe)
        action_result  = self.action_store.get_all_actions_for_gaps(kpi_data)
        actions_prompt = self.action_store.format_for_prompt(action_result)
        actions_sc     = self.action_store.format_for_scorecard(action_result)
        log.info(
            f"ActionStore — gaps: {action_result['gaps_detected']}, "
            f"career_dev: {action_result['career_dev_triggered']}"
        )

        # 4. Génère le scorecard (contexte sémantique + actions pré-sélectionnées)
        scorecard = self.generator.generate_scorecard(
            bu_name, kpi_data, context, actions_prompt
        )

        # 5. Enrichit avec les metadata de retrieval + actions structurées
        scorecard["retrieved_sources"]  = list({c["source"] for c in chunks})
        scorecard["query_used"]         = query
        scorecard["n_chunks_used"]      = len(chunks)
        scorecard["action_library"]     = actions_sc

        log.info(f"Scorecard généré — confiance: {scorecard.get('confidence', '?')}")
        return scorecard

    def _build_query(self, bu_name: str, kpi_data: dict) -> str:
        """
        Traduit les KPIs en query sémantique pour le retriever.

        Construit une requête qui décrit la situation RH de la BU
        pour cibler les documents les plus pertinents.
        """
        parts = [f"Recommandations RH pour {bu_name} CACEIS"]

        Y      = kpi_data.get("kpi_Y", 3.39)
        lam    = kpi_data.get("kpi_lambda", 44.6)
        beta   = kpi_data.get("kpi_beta_qr", 3.39)
        rho    = kpi_data.get("kpi_rho", 0.048)
        vhc    = kpi_data.get("v_hc_index", 0.45)

        # Engagement
        if Y < 3.20:
            parts.append("engagement faible critique amélioration enquête IMR satisfaction collaborateurs")
        elif Y < 3.39:
            parts.append("engagement sous la moyenne programme reconnaissance motivation We Care")
        else:
            parts.append("engagement satisfaisant maintien bonnes pratiques")

        # Formation
        if lam < 30:
            parts.append("formation insuffisante plan développement compétences budget formation")
        elif lam < 44.6:
            parts.append("formation amélioration qualité cold review impact quotidien")
        else:
            parts.append("formation volume correct qualité certifications e-learning")

        # Absentéisme
        if rho > 0.05:
            parts.append("absentéisme élevé FABLife QVCT bien-être santé risques psychosociaux accord QVT")
        elif rho > 0.026:
            parts.append("absentéisme surveillance programme bien-être préventif")

        # Performance
        if beta < 3.20:
            parts.append("performance faible EAE feedback management coaching objectifs")
        elif beta > 3.6:
            parts.append("haute performance talent review succession hauts potentiels")

        # Diversité & inclusion (toujours pertinent)
        parts.append("diversité inclusion baromètre D&I égalité professionnelle CACEIS")

        # Indice composite
        if vhc < 0.43:
            parts.append("indice capital humain faible plan transformation levier prioritaire")

        return " — ".join(parts)

    def index_status(self) -> dict:
        """Retourne le statut de l'index."""
        return self.retriever.index_status()
