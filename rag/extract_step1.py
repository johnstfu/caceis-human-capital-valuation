#!/usr/bin/env python3
"""
extract_step1.py — Extraction RAG des chunks pertinents par KPI.

7 requêtes (P exclu) × top 10 chunks → extraction_raw.json
Lance depuis rag/ : python3 extract_step1.py
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ingest.embedder import LocalEmbedder
from store.vector_store import CACEISVectorStore

OUTPUT_PATH = Path(__file__).parent / "data" / "extraction_raw.json"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ── Requêtes par KPI ─────────────────────────────────────────────────────────
# P exclu (aucune action directe — levier indirect via Y, λ, ρ)

QUERIES = {
    "Y": [
        "actions pour améliorer l'engagement des collaborateurs score IMR satisfaction",
        "programme engagement collaborateur motivation satisfaction travail CACEIS",
        "initiatives amélioration satisfaction engagement sondage",
    ],
    "λ": [
        "réduire le turnover rétention des talents fidélisation CACEIS",
        "programme rétention départs volontaires turnover reduction",
        "actions fidélisation collaborateurs départs prématurés",
    ],
    "ρ": [
        "réduire l'absentéisme gestion des absences présentéisme CACEIS",
        "programme réduction absentéisme bien-être santé au travail",
        "dispositif gestion absentéisme actions correctives",
    ],
    "γ": [
        "taux de promotion avancement carrière mobilité interne CACEIS",
        "programme promotion interne développement carrière",
        "politique mobilité interne promotion collaborateurs",
    ],
    "δ": [
        "formation professionnelle taux réalisation plan de formation CACEIS",
        "programme formation compétences développement professionnel",
        "dispositif formation employés heures formation",
    ],
    "α": [
        "évaluation annuelle EAE entretien annuel performance CACEIS",
        "programme évaluation performance objectifs feedback managérial",
        "dispositif entretien annuel EAE taux réalisation",
    ],
    "β": [
        "qualité de vie au travail QVCT bien-être stress management CACEIS",
        "programme QVCT qualité vie travail actions bien-être",
        "initiatives bien-être télétravail équilibre vie pro perso",
    ],
}

TOP_K = 10  # chunks par requête


def main():
    print("\n" + "="*62)
    print("  CACEIS RAG — Étape 1 : Extraction par KPI")
    print("="*62)

    store = CACEISVectorStore()
    embedder = LocalEmbedder()

    total_chunks = store.count()
    print(f"\n  Index : {total_chunks} chunks\n")

    results = {}
    seen_ids = {}  # Pour dédupliquer par KPI

    for kpi, queries in QUERIES.items():
        print(f"\n── KPI {kpi} ──")
        kpi_chunks = {}  # chunk_id → chunk_data

        for q in queries:
            q_vec = embedder.embed_query(q)
            hits = store.collection.query(
                query_embeddings=[q_vec],
                n_results=TOP_K,
                include=["documents", "metadatas", "distances"],
            )

            docs      = hits["documents"][0]
            metas     = hits["metadatas"][0]
            distances = hits["distances"][0]
            ids       = hits["ids"][0]

            for chunk_id, doc, meta, dist in zip(ids, docs, metas, distances):
                score = 1.0 - dist  # distance cosine → similarité
                if chunk_id not in kpi_chunks or score > kpi_chunks[chunk_id]["score"]:
                    kpi_chunks[chunk_id] = {
                        "chunk_id": chunk_id,
                        "source":   meta.get("source", "?"),
                        "folder":   meta.get("folder", "?"),
                        "text":     doc,
                        "score":    round(score, 4),
                    }

        # Trie par score décroissant, garde top 10
        sorted_chunks = sorted(kpi_chunks.values(), key=lambda x: x["score"], reverse=True)[:TOP_K]
        results[kpi] = sorted_chunks

        for c in sorted_chunks:
            print(f"    {c['score']:.3f}  {c['source'][:50]}  [{c['chunk_id']}]")

        print(f"  → {len(sorted_chunks)} chunks retenus pour KPI {kpi}")

    # Sauvegarde
    output = {
        "meta": {
            "generated_at":  time.strftime("%Y-%m-%dT%H:%M:%S"),
            "index_size":    total_chunks,
            "kpis_queried":  list(QUERIES.keys()),
            "top_k":         TOP_K,
            "note":          "P exclu — levier indirect uniquement",
        },
        "by_kpi": results,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*62}")
    print(f"  ✅  Extraction terminée")
    print(f"      Fichier : {OUTPUT_PATH}")
    total_kept = sum(len(v) for v in results.values())
    print(f"      Total chunks extraits : {total_kept}")
    print(f"\n  Par KPI :")
    for kpi, chunks in results.items():
        print(f"    {kpi} : {len(chunks)} chunks")
    print(f"\n{'='*62}\n")


if __name__ == "__main__":
    main()
