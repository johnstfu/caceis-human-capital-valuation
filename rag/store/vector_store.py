"""
vector_store.py — Stockage et recherche vectorielle locale via ChromaDB.

Mode : persistant sur disque dans data/chroma_db/ (pas de serveur).
Collection : "caceis_hr_library"

Les embeddings sont pré-calculés par AnthropicEmbedder et passés
explicitement à ChromaDB (pas d'embedding function interne ChromaDB).
"""

import logging
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings

log = logging.getLogger(__name__)

COLLECTION_NAME = "caceis_hr_library"


class CACEISVectorStore:

    def __init__(self, persist_dir: str = None):
        if persist_dir is None:
            persist_dir = str(Path(__file__).parent.parent / "data" / "chroma_db")

        Path(persist_dir).mkdir(parents=True, exist_ok=True)

        # Client ChromaDB persistant local — pas de serveur, données sur disque
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )

        # Crée ou récupère la collection
        # embedding_function=None → on passe les embeddings manuellement
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # similarité cosinus
        )
        log.info(f"ChromaDB initialisé : {persist_dir} ({self.count()} chunks)")

    # ── Écriture ──────────────────────────────────────────────────────────────

    def add_chunks(
        self,
        chunks: List[dict],
        embeddings: List[List[float]],
    ):
        """
        Indexe les chunks avec leurs embeddings pré-calculés.

        Args:
            chunks     : list de dicts {chunk_id, source, folder, text, token_count}
            embeddings : list de vecteurs float (même ordre que chunks)
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch chunks ({len(chunks)}) vs embeddings ({len(embeddings)})"
            )

        # ChromaDB nécessite des IDs uniques — on utilise chunk_id
        ids        = [c["chunk_id"]  for c in chunks]
        documents  = [c["text"]      for c in chunks]
        metadatas  = [
            {
                "source":      c["source"],
                "folder":      c["folder"],
                "token_count": c.get("token_count", 0),
            }
            for c in chunks
        ]

        # Insère par batch de 50 pour éviter les timeouts
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch_ids   = ids[i: i + batch_size]
            batch_docs  = documents[i: i + batch_size]
            batch_metas = metadatas[i: i + batch_size]
            batch_embs  = embeddings[i: i + batch_size]

            # Filtre les IDs déjà présents (idempotent)
            existing = set(
                self.collection.get(ids=batch_ids, include=[])["ids"]
            )
            new_idx = [j for j, bid in enumerate(batch_ids) if bid not in existing]

            if new_idx:
                self.collection.add(
                    ids        = [batch_ids[j]   for j in new_idx],
                    documents  = [batch_docs[j]  for j in new_idx],
                    metadatas  = [batch_metas[j] for j in new_idx],
                    embeddings = [batch_embs[j]  for j in new_idx],
                )
                log.info(f"  Indexé batch {i//batch_size + 1}: {len(new_idx)} chunks")
            else:
                log.info(f"  Batch {i//batch_size + 1}: déjà indexé, skip")

    def reset(self):
        """Supprime et recrée la collection (pour réingestion complète)."""
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        log.info("Collection réinitialisée")

    # ── Lecture / Recherche ───────────────────────────────────────────────────

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        folder_filter: Optional[str] = None,
    ) -> List[dict]:
        """
        Recherche les top_k chunks les plus proches de l'embedding de query.

        Args:
            query_embedding : vecteur float (128 dims, normalisé)
            top_k           : nombre de résultats
            folder_filter   : filtre optionnel sur le dossier source

        Returns:
            list de dicts {text, source, folder, score, chunk_id}
        """
        where = {"folder": folder_filter} if folder_filter else None

        try:
            results = self.collection.query(
                query_embeddings = [query_embedding],
                n_results        = min(top_k, self.count()),
                where            = where,
                include          = ["documents", "metadatas", "distances"],
            )
        except Exception as e:
            log.error(f"ChromaDB search error: {e}")
            return []

        chunks_out = []
        ids        = results.get("ids", [[]])[0]
        docs       = results.get("documents", [[]])[0]
        metas      = results.get("metadatas", [[]])[0]
        distances  = results.get("distances", [[]])[0]

        for chunk_id, doc, meta, dist in zip(ids, docs, metas, distances):
            # ChromaDB avec espace cosinus retourne la distance (0=identique, 2=opposé)
            # Conversion en score de similarité [0, 1]
            score = max(0.0, 1.0 - dist / 2.0)
            chunks_out.append({
                "chunk_id": chunk_id,
                "text":     doc,
                "source":   meta.get("source", ""),
                "folder":   meta.get("folder", ""),
                "score":    round(score, 4),
            })

        return chunks_out

    def count(self) -> int:
        """Nombre de chunks indexés."""
        try:
            return self.collection.count()
        except Exception:
            return 0

    def get_sources(self) -> List[str]:
        """Liste des fichiers sources indexés (uniques)."""
        try:
            all_metas = self.collection.get(include=["metadatas"])["metadatas"]
            return sorted(set(m["source"] for m in all_metas if m))
        except Exception:
            return []
