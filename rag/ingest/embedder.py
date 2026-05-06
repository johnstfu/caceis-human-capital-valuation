"""
embedder.py — Embeddings locaux via sentence-transformers.

Modèle : all-MiniLM-L6-v2 (384 dims, ~90 MB, run 100% local, zéro API call)
  - Téléchargé une seule fois depuis HuggingFace (~30s première fois)
  - Toutes les inférences suivantes sont instantanées (CPU)
  - Qualité retrieval supérieure à l'approche custom 128-dims Claude

Claude reste utilisé uniquement pour la génération des recommandations.
"""

import logging
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

log = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


class LocalEmbedder:
    """
    Embeddings locaux via sentence-transformers.
    Aucun appel API, aucun rate limit, instantané après chargement.
    """

    _instance = None  # singleton — modèle chargé une seule fois

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
        return cls._instance

    def _load_model(self):
        if self._model is None:
            log.info(f"Chargement du modèle local {MODEL_NAME}…")
            self._model = SentenceTransformer(MODEL_NAME)
            log.info("Modèle chargé.")

    def embed_chunk(self, text: str) -> List[float]:
        """Embedding d'un chunk document."""
        self._load_model()
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Embedding d'une query utilisateur."""
        self._load_model()
        vec = self._model.encode(query, normalize_embeddings=True)
        return vec.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        """
        Embedding d'une liste de textes — optimisé batch GPU/CPU.
        Beaucoup plus rapide que d'appeler embed_chunk() en boucle.
        """
        self._load_model()
        log.info(f"Embedding batch de {len(texts)} textes…")
        vecs = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        log.info("Batch embedding terminé.")
        return [v.tolist() for v in vecs]

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        a = np.array(vec1, dtype=np.float32)
        b = np.array(vec2, dtype=np.float32)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        return float(np.dot(a, b) / denom) if denom > 1e-8 else 0.0

    @property
    def dimension(self) -> int:
        return EMBEDDING_DIM


# Alias pour compatibilité avec l'interface définie dans le spec
AnthropicEmbedder = LocalEmbedder
