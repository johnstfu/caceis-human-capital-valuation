"""
retriever.py — Orchestre embedder + vector_store pour la recherche sémantique.
"""

import logging
from typing import List, Optional

from ingest.embedder import AnthropicEmbedder
from store.vector_store import CACEISVectorStore

log = logging.getLogger(__name__)


class CACEISRetriever:

    def __init__(self):
        self.embedder = AnthropicEmbedder()
        self.store    = CACEISVectorStore()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        folder_filter: Optional[str] = None,
    ) -> List[dict]:
        """
        Recherche sémantique : embed la query puis interroge ChromaDB.

        Args:
            query         : question en langage naturel
            top_k         : nombre de chunks à retourner
            folder_filter : restreint la recherche à un dossier source

        Returns:
            list de dicts {chunk_id, text, source, folder, score}
            triés par score décroissant
        """
        log.info(f"Retrieval — query : '{query[:80]}...'")

        if self.store.count() == 0:
            log.warning("Index vide — lance ingest_all.py d'abord")
            return []

        query_emb = self.embedder.embed_query(query)
        chunks    = self.store.search(
            query_embedding = query_emb,
            top_k           = top_k,
            folder_filter   = folder_filter,
        )

        log.info(f"Retrieval — {len(chunks)} chunks trouvés")
        for c in chunks:
            log.info(f"  [{c['score']:.3f}] {c['source']} — {c['text'][:60]}…")

        return chunks

    def format_context(self, chunks: List[dict]) -> str:
        """
        Formate les chunks pour injection dans le prompt Claude.

        Format :
            [Source: fichier.pdf | Dossier: HR Data | Score: 0.87]
            texte du chunk
            ---
        """
        if not chunks:
            return "Aucun document pertinent trouvé dans la base de connaissances CACEIS."

        parts = []
        for i, chunk in enumerate(chunks, 1):
            header = (
                f"[Source {i}: {chunk['source']} | "
                f"Dossier: {chunk['folder']} | "
                f"Pertinence: {chunk['score']:.2f}]"
            )
            parts.append(f"{header}\n{chunk['text']}")

        return "\n---\n".join(parts)

    def index_status(self) -> dict:
        """Retourne le statut de l'index ChromaDB."""
        return {
            "chunks_total":  self.store.count(),
            "sources":       self.store.get_sources(),
        }
