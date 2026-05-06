#!/usr/bin/env python3
"""
api.py — Backend FastAPI du système RAG CACEIS.

Endpoints :
  GET  /api/status              → statut de l'index
  GET  /api/bus                 → liste des BUs
  GET  /api/scorecard/{bu_name} → scorecard RAG complet
  POST /api/query               → question libre sur la base documentaire

Lancement :
    cd /Users/rayanekryslak-medioub/Desktop/CACEIS/rag
    python3 api.py

Ou via uvicorn :
    uvicorn api:app --reload --port 8000
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from interface.scorecard_api import get_bu_scorecard, list_bus, index_status
from retrieval.retriever import CACEISRetriever

KPI_DATA_PATH = Path(__file__).parent / "data" / "kpi-output.json"

logging.basicConfig(level=logging.WARNING)

app = FastAPI(title="CACEIS HCV RAG API", version="1.0.0")

# CORS — autorise les appels depuis le dashboard HTML (file:// et localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Sert les fichiers statiques du dashboard
INTERFACE_DIR = Path(__file__).parent.parent / "interface"
if INTERFACE_DIR.exists():
    app.mount("/dashboard", StaticFiles(directory=str(INTERFACE_DIR), html=True), name="dashboard")

# Singleton retriever (chargé une fois)
_retriever: CACEISRetriever = None

def get_retriever() -> CACEISRetriever:
    global _retriever
    if _retriever is None:
        _retriever = CACEISRetriever()
    return _retriever


# ── Modèles Pydantic ──────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    # Redirige vers le dashboard si disponible
    index = INTERFACE_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"status": "CACEIS RAG API running", "docs": "/docs"}


@app.get("/api/status")
def api_status():
    """Statut de l'index ChromaDB."""
    try:
        status = index_status()
        return {
            "ok": True,
            "chunks_total": status["chunks_total"],
            "sources_count": len(status["sources"]),
            "sources": status["sources"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bus")
def api_list_bus():
    """Liste des BUs disponibles."""
    try:
        return {"bus": list_bus()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kpi-data")
def api_kpi_data():
    """Retourne kpi-output.json complet — lecture statique, pas d'appel IA."""
    try:
        import json
        raw = json.loads(KPI_DATA_PATH.read_text(encoding="utf-8"))
        return raw
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scorecard/{bu_name:path}")
def api_scorecard(bu_name: str):
    """
    Génère le scorecard RAG complet pour une BU.
    Exemple : GET /api/scorecard/Finance%20%26%20Admin
    """
    try:
        scorecard = get_bu_scorecard(bu_name)
        return scorecard
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
def api_query(body: QueryRequest):
    """
    Question libre sur la base documentaire CACEIS.
    Retourne les chunks pertinents + une réponse générée par Claude.
    """
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question vide")

    try:
        retriever = get_retriever()

        # Retrieval
        chunks = retriever.retrieve(body.question, top_k=body.top_k)
        context = retriever.format_context(chunks)

        if not chunks:
            return {
                "answer": "Aucun document pertinent trouvé pour cette question.",
                "sources": [],
                "chunks": [],
            }

        # Génération via Claude
        import os
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            system="""Tu es un assistant RH expert CACEIS. Tu réponds aux questions en te basant
UNIQUEMENT sur les documents fournis dans le contexte. Cite tes sources [Source: fichier].
Sois concis (3-5 phrases max). Si la réponse n'est pas dans les documents, dis-le clairement.""",
            messages=[{
                "role": "user",
                "content": f"Question : {body.question}\n\nContexte documentaire :\n{context}"
            }],
        )

        answer = response.content[0].text.strip()

        return {
            "answer": answer,
            "sources": list({c["source"] for c in chunks}),
            "chunks": [
                {"source": c["source"], "score": c["score"], "excerpt": c["text"][:200]}
                for c in chunks
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*55)
    print("  CACEIS RAG API — http://localhost:8000")
    print("  Dashboard    — http://localhost:8000/dashboard")
    print("  Docs API     — http://localhost:8000/docs")
    print("="*55 + "\n")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
