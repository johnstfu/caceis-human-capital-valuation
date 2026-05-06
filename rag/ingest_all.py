#!/usr/bin/env python3
"""
ingest_all.py — Indexation complète des documents CACEIS (embeddings locaux).

Lance une seule fois pour construire la base vectorielle.
Idempotent : les chunks déjà indexés sont ignorés.

Usage :
    cd /Users/rayanekryslak-medioub/Desktop/CACEIS/rag
    python3 ingest_all.py

    # Pour réingérer depuis zéro :
    python3 ingest_all.py --reset
"""

import sys
import logging
import argparse
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(".env")

from ingest.loader import load_all_documents, FOLDERS
from ingest.chunker import chunk_documents
from ingest.embedder import LocalEmbedder
from store.vector_store import CACEISVectorStore

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true",
                        help="Recrée l'index depuis zéro")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  CACEIS RAG — Ingestion (embeddings locaux)")
    print("="*60 + "\n")

    # 1. Chargement
    print("1/4  Chargement des documents…")
    t0 = time.time()
    docs = load_all_documents(FOLDERS)
    if not docs:
        print("⚠️  Aucun document chargé.")
        sys.exit(1)
    print(f"     ✓ {len(docs)} documents  ({time.time()-t0:.1f}s)\n")

    # 2. Chunking
    print("2/4  Découpage en chunks…")
    t0 = time.time()
    chunks = chunk_documents(docs)
    print(f"     ✓ {len(chunks)} chunks créés  ({time.time()-t0:.1f}s)\n")

    # 3. Init store
    store = CACEISVectorStore()
    if args.reset:
        print("     RESET — suppression de l'index existant…")
        store.reset()

    already = store.count()
    if already > 0 and not args.reset:
        print(f"     ℹ️  {already} chunks déjà indexés — seuls les nouveaux seront ajoutés\n")

    # 4. Embeddings batch (local — instantané)
    print("3/4  Génération des embeddings (sentence-transformers local)…")
    t0 = time.time()
    embedder = LocalEmbedder()
    texts     = [c["text"] for c in chunks]
    embeddings = embedder.embed_batch(texts)
    print(f"     ✓ {len(embeddings)} embeddings  ({time.time()-t0:.1f}s)\n")

    # 5. Indexation ChromaDB
    print("4/4  Indexation ChromaDB…")
    t0 = time.time()
    store.add_chunks(chunks, embeddings)
    print(f"     ✓ Indexation terminée  ({time.time()-t0:.1f}s)\n")

    # Résumé
    total   = store.count()
    sources = store.get_sources()
    print("="*60)
    print(f"  ✅  Ingestion terminée")
    print(f"      Chunks indexés   : {total}")
    print(f"      Sources indexées : {len(sources)}")
    print(f"\n  Sources :")
    for s in sources:
        print(f"      • {s}")
    print(f"\n  Lance maintenant : python3 demo.py")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
