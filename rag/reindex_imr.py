#!/usr/bin/env python3
"""
reindex_imr.py — Réindexation ciblée des fichiers IMR2023 et IMR2024.

Supprime les chunks existants pour ces deux fichiers, puis
réextrait / rechunke / réembed / réindexe depuis zéro.

Usage :
    cd /Users/rayanekryslak-medioub/Desktop/CACEIS/rag
    python3 reindex_imr.py
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ingest.loader import _extract_pdf
from ingest.chunker import chunk_document
from ingest.embedder import LocalEmbedder
from store.vector_store import CACEISVectorStore


def _extract_pdf_ocr(path: Path, lang: str = "fra+eng") -> str:
    """
    Extrait le texte d'un PDF scanné via OCR (pytesseract + pdf2image).
    Fallback si pdfplumber retourne moins de 500 mots.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_path
        print(f"  OCR en cours (peut prendre 1-3 min)…")
        pages = convert_from_path(str(path), dpi=200)
        texts = []
        for i, page in enumerate(pages):
            t = pytesseract.image_to_string(page, lang=lang)
            if t.strip():
                texts.append(t)
            if (i + 1) % 10 == 0:
                print(f"    Page {i+1}/{len(pages)} OCR OK")
        return "\n".join(texts)
    except Exception as e:
        print(f"  ⚠  OCR error: {e}")
        return ""

BASE = Path("/Users/rayanekryslak-medioub/Desktop/CACEIS/Sujet Alberthon")
FOLDER = BASE / "Employee satisfaction & engagement"

TARGET_FILES = [
    "IMR2023_CACEIS_GROUP.pdf",
    "IMR2024_CACEIS_GROUP.pdf",
]


def get_chunk_id_prefix(filename: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", filename.lower().rsplit(".", 1)[0])
    return base + "_chunk_"


def delete_existing_chunks(store: CACEISVectorStore, filename: str) -> int:
    """Supprime tous les chunks d'un fichier de ChromaDB."""
    # Récupère tous les IDs
    all_data = store.collection.get(include=["metadatas"])
    metadatas = all_data.get("metadatas", [])
    ids = all_data.get("ids", [])

    to_delete = [
        chunk_id for chunk_id, meta in zip(ids, metadatas)
        if meta.get("source") == filename
    ]

    if to_delete:
        store.collection.delete(ids=to_delete)
        print(f"  Supprimé {len(to_delete)} chunks existants pour {filename}")
    else:
        print(f"  Aucun chunk existant pour {filename}")

    return len(to_delete)


def main():
    print("\n" + "="*62)
    print("  CACEIS — Réindexation IMR 2023 & 2024")
    print("="*62)

    store = CACEISVectorStore()
    embedder = LocalEmbedder()

    before_total = store.count()
    print(f"\n  Chunks avant : {before_total}\n")

    for filename in TARGET_FILES:
        pdf_path = FOLDER / filename
        print(f"\n── {filename} ──")

        if not pdf_path.exists():
            print(f"  ⚠  Fichier introuvable : {pdf_path}")
            continue

        # 1. Suppression des chunks existants
        delete_existing_chunks(store, filename)

        # 2. Extraction PDF (native puis OCR si insuffisant)
        print(f"  Extraction PDF native…")
        content = _extract_pdf(pdf_path)
        word_count = len(content.split())
        print(f"  Texte natif extrait : {word_count} mots")

        if word_count < 500:
            print(f"  PDF scanné détecté — bascule sur OCR…")
            content = _extract_pdf_ocr(pdf_path)
            word_count = len(content.split())
            print(f"  Texte OCR extrait : {word_count} mots")

        if word_count < 80:
            print(f"  ⚠  Contenu insuffisant ({word_count} mots) même après OCR")
            continue

        # 3. Chunking
        doc = {
            "source":  filename,
            "folder":  "Employee satisfaction & engagement",
            "content": content,
            "type":    "pdf",
        }
        chunks = chunk_document(doc)
        print(f"  Chunks créés  : {len(chunks)}")

        # 4. Embeddings
        print(f"  Embeddings…")
        texts = [c["text"] for c in chunks]
        embeddings = embedder.embed_batch(texts)

        # 5. Indexation
        print(f"  Indexation ChromaDB…")
        store.add_chunks(chunks, embeddings)
        print(f"  ✓ {len(chunks)} chunks indexés pour {filename}")

    after_total = store.count()
    print(f"\n{'='*62}")
    print(f"  Chunks après : {after_total}  (delta : +{after_total - before_total})")

    # Vérification par fichier
    print(f"\n  Vérification par fichier :")
    all_data = store.collection.get(include=["metadatas"])
    metadatas = all_data.get("metadatas", [])
    for filename in TARGET_FILES:
        count = sum(1 for m in metadatas if m.get("source") == filename)
        status = "✓" if count > 10 else "⚠"
        print(f"  {status}  {filename} : {count} chunks")

    print(f"\n{'='*62}\n")


if __name__ == "__main__":
    main()
