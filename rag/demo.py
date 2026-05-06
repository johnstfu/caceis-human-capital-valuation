#!/usr/bin/env python3
"""
demo.py — Démonstration du système RAG CACEIS.

Génère le scorecard de Finance & Admin (BU pilote) et l'affiche.

Usage :
    cd /Users/rayanekryslak-medioub/Desktop/CACEIS/rag
    python3 demo.py

    # Pour une autre BU :
    python3 demo.py --bu "Coverage France"

    # Pour lister les BUs disponibles :
    python3 demo.py --list

    # Pour tester le retrieval seul (sans génération) :
    python3 demo.py --retrieval-only "engagement formation absentéisme"
"""

import sys
import json
import logging
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(".env")

logging.basicConfig(
    level=logging.WARNING,  # Mode silencieux pour la démo
    format="%(levelname)s | %(message)s",
)


def print_scorecard(scorecard: dict):
    """Affiche le scorecard de façon lisible."""
    print("\n" + "═"*65)
    print(f"  SCORECARD RH — {scorecard.get('bu_name', '?').upper()}")
    print("═"*65)

    vhc  = scorecard.get("v_hc_index", 0)
    rank = scorecard.get("rank", "?")
    print(f"\n  V_HC Index    : {vhc:.4f}  (rang {rank})")
    print(f"  Résumé        : {scorecard.get('summary', '')}")

    alerts = scorecard.get("alert_kpis", [])
    if alerts:
        print(f"  KPIs en alerte: {', '.join(alerts)}")

    kpi_raw = scorecard.get("kpi_raw", {})
    if kpi_raw:
        print(f"\n  KPIs bruts :")
        labels = {"Y": "Engagement", "lambda": "Formation",
                  "beta": "Performance", "rho": "Absentéisme", "V_HC": "V_HC"}
        for k, label in labels.items():
            v = kpi_raw.get(k)
            if v is not None:
                if k == "rho":
                    print(f"    {label:12s}: {v*100:.2f}%")
                else:
                    print(f"    {label:12s}: {v:.3f}")

    recs = scorecard.get("recommendations", [])
    if recs:
        print(f"\n  {'─'*60}")
        print(f"  RECOMMANDATIONS ({len(recs)})")
        print(f"  {'─'*60}")
        for i, rec in enumerate(recs, 1):
            priority = rec.get("priority", "?").upper()
            kpi      = rec.get("kpi_impacted", "?")
            lever    = rec.get("lever", "?")
            desc     = rec.get("description", "")
            source   = rec.get("source", "")
            impact   = rec.get("estimated_impact", "")

            print(f"\n  [{i}] {lever}")
            print(f"      Priorité : {priority} | KPI : {kpi}")
            print(f"      {desc}")
            if impact:
                print(f"      Impact estimé : {impact}")
            if source:
                print(f"      Source : {source}")
    else:
        print("\n  ⚠️  Aucune recommandation générée")

    conf = scorecard.get("confidence", "?")
    conf_reason = scorecard.get("confidence_reason", "")
    print(f"\n  {'─'*60}")
    print(f"  Confiance : {conf.upper()} — {conf_reason}")

    sources = scorecard.get("retrieved_sources", [])
    if sources:
        print(f"\n  Documents utilisés :")
        for s in sources:
            print(f"    • {s}")

    n_chunks = scorecard.get("n_chunks_used", 0)
    if n_chunks:
        print(f"\n  Chunks RAG utilisés : {n_chunks}")

    print("\n" + "═"*65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Démo RAG CACEIS")
    parser.add_argument("--bu", default="Finance & Admin", help="Nom de la BU")
    parser.add_argument("--list", action="store_true", help="Liste les BUs")
    parser.add_argument("--json", action="store_true", help="Sortie JSON brut")
    parser.add_argument("--retrieval-only", metavar="QUERY",
                        help="Teste le retrieval seul pour une query")
    parser.add_argument("--status", action="store_true",
                        help="Affiche le statut de l'index")
    args = parser.parse_args()

    from interface.scorecard_api import (
        get_bu_scorecard, list_bus, index_status
    )

    # ── Status de l'index ─────────────────────────────────────────────────────
    if args.status:
        status = index_status()
        print(f"\nIndex ChromaDB :")
        print(f"  Chunks indexés : {status['chunks_total']}")
        print(f"  Sources ({len(status['sources'])}) :")
        for s in status["sources"]:
            print(f"    • {s}")
        return

    # ── Liste des BUs ─────────────────────────────────────────────────────────
    if args.list:
        bus = list_bus()
        print(f"\n{len(bus)} BUs disponibles :")
        for bu in bus:
            print(f"  • {bu}")
        return

    # ── Test retrieval seul ───────────────────────────────────────────────────
    if args.retrieval_only:
        from retrieval.retriever import CACEISRetriever
        retriever = CACEISRetriever()
        chunks = retriever.retrieve(args.retrieval_only, top_k=5)
        print(f"\nRetrieval — {len(chunks)} résultats pour : '{args.retrieval_only}'\n")
        for c in chunks:
            print(f"  [{c['score']:.3f}] {c['source']}")
            print(f"         {c['text'][:150]}…\n")
        return

    # ── Génération du scorecard ───────────────────────────────────────────────
    print(f"\nGénération du scorecard RAG — {args.bu}…")

    status = index_status()
    if status["chunks_total"] == 0:
        print("\n⚠️  Index vide ! Lance d'abord : python3 ingest_all.py")
        sys.exit(1)

    print(f"(Index : {status['chunks_total']} chunks de {len(status['sources'])} sources)\n")

    try:
        scorecard = get_bu_scorecard(args.bu)
    except ValueError as e:
        print(f"\n❌ {e}")
        sys.exit(1)

    if args.json:
        print(json.dumps(scorecard, indent=2, ensure_ascii=False))
    else:
        print_scorecard(scorecard)


if __name__ == "__main__":
    main()
