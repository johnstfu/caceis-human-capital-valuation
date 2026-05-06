# CACEIS Human Capital Valuation

> A RAG-powered HR analytics system that computes a composite V_HC index per Business Unit and generates sourced action recommendations from CACEIS's own HR policy library.

---

## Quick Start

```bash
cd rag
pip install -r requirements.txt
python3 api.py
```

Then open: [http://localhost:8000/dashboard/pilot-bu-dashboard.html](http://localhost:8000/dashboard/pilot-bu-dashboard.html)

---

## What This Is

This project transforms 436,000 rows of siloed HR data (training records, absenteeism logs, engagement surveys, EAE evaluations) into a single **V_HC index** — a composite Human Capital score — for each of CACEIS's 26 Business Units.

A RAG pipeline on Anthropic's Claude retrieves context from 14 official CACEIS HR documents and generates actionable recommendations grounded in 26 verified actions from the internal action library.

The dashboard exposes three access tiers (Chief Officer / BU Leadership / Operational Manager) with tier-appropriate data depth, an AI chat panel, and a milestone-tracked action plan.

---

## Project Structure

```
caceis-human-capital-valuation/
│
├── rag/                    ← RAG pipeline: ingest, retrieval, generation, API
│   ├── api.py              ← FastAPI server (entry point)
│   ├── ingest_all.py       ← One-shot document indexing into ChromaDB
│   ├── requirements.txt
│   ├── .env.example        ← API key template
│   ├── ingest/             ← PDF/DOCX loading, chunking, embedding
│   ├── store/              ← ChromaDB vector store + action library store
│   ├── retrieval/          ← Semantic retriever
│   ├── generation/         ← Claude-based scorecard generator
│   ├── pipeline/           ← End-to-end BU scorecard orchestrator
│   ├── interface/          ← scorecard_api.py (FastAPI route handlers)
│   └── data/
│       ├── kpi-output.json         ← Computed KPIs for all 26 BUs
│       └── action_library_raw.json ← 26 sourced HR actions
│
├── interface/
│   └── pilot-bu-dashboard.html  ← Main dashboard (single-file, self-contained)
│
├── notebooks/
│   └── CACEIS_Human_Capital_Valuation.ipynb  ← KPI computation pipeline
│
├── docs/
│   ├── ARCHITECTURE.md          ← Technical architecture deep-dive
│   ├── KPI_DEFINITIONS.md       ← V_HC formula and KPI methodology
│   ├── DEPLOYMENT_STRATEGY.md   ← Production deployment guide
│   └── GDPR_COMPLIANCE.md       ← Data privacy and compliance notes
│
├── slides/
│   ├── CACEIS_Final_Presentation.pdf  ← Final project presentation
│   └── fiches/                        ← Slide-by-slide narrative notes
│
└── data/
    └── sample/
        └── kpi-output-sample.json  ← 3-BU sample for demo/dev
```

---

## The Five KPIs

| Symbol | Name | Question answered | CACEIS average |
|--------|------|-------------------|----------------|
| **Y** | Engagement | How engaged are employees? (IMR survey /5) | 3.40 / 5 |
| **λ** | Training volume | How many training hours per employee per year? | 44.6 h/emp/yr |
| **β** | Training quality | How well are training sessions rated? (EAE /5) | 3.40 / 5 |
| **P** | Productivity | What is the NBI/FTE growth rate? | Result indicator |
| **ρ** | Absenteeism | What is the absenteeism rate? (France) | 4.8 % |

These five KPIs feed a weighted composite formula:

```
V_HC = w_Y·Y + w_λ·norm(λ) + w_β·β + w_P·norm(P) − w_ρ·norm(ρ)
```

Weights: Y = 0.35 · λ = 0.20 · β = 0.25 · P = 0.10 · ρ = 0.10

---

## Architecture

```
Raw Excel / PDF                    Source documents
     │                                    │
     ▼                                    ▼
[Notebook: pandas]           [ingest_all.py: chunker + embedder]
     │                                    │
     ▼                                    ▼
kpi-output.json              ChromaDB vector store (local)
     │                                    │
     └──────────────┬─────────────────────┘
                    ▼
           [FastAPI api.py]
                    │
          ┌─────────┼──────────────┐
          ▼         ▼              ▼
    /api/kpi-data  /api/scorecard  /api/query
          │         │              │
          │    [RAG Pipeline]      │
          │    retriever →         │
          │    ActionStore →       │
          │    Claude (Sonnet)     │
          │         │              │
          └─────────▼──────────────┘
                    │
          pilot-bu-dashboard.html
          (Tier 1 / Tier 2 / Tier 3)
```

---

## Setup Guide

### Prerequisites

- Python 3.9+
- An [Anthropic API key](https://console.anthropic.com/)
- ~500MB disk space (ChromaDB index)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/caceis-human-capital-valuation.git
cd caceis-human-capital-valuation

# 2. Install dependencies
cd rag
pip install -r requirements.txt

# 3. Configure your API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...

# 4. Index source documents (requires Sujet Alberthon/ data files)
python3 ingest_all.py

# 5. Launch the API server
python3 api.py
```

### First Launch

1. Start the server: `python3 rag/api.py`
2. Open [http://localhost:8000/dashboard/pilot-bu-dashboard.html](http://localhost:8000/dashboard/pilot-bu-dashboard.html)
3. Select an access tier (T1 = Chief Officer, T2 = BU Leadership, T3 = Manager)
4. Pick a Business Unit from the dropdown
5. Click **Generate recommendations** to run the RAG pipeline for that BU

### Rebuilding the Vector Store

If you cloned the repo and `rag/data/chroma_db/` is empty (it is — it is gitignored):

```bash
cd rag
# Place source PDF/DOCX files in the expected paths (see ingest_all.py)
python3 ingest_all.py
# Indexing takes ~2–5 minutes for 14 documents
```

### Running Without Source Documents

The dashboard works in **static mode** using `rag/data/kpi-output.json` and `rag/data/action_library_raw.json` — no API key needed for KPI display. The **Generate recommendations** button and the AI chat panel require a running server with a valid Anthropic API key.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Technical architecture, design decisions, full data flow |
| [docs/KPI_DEFINITIONS.md](docs/KPI_DEFINITIONS.md) | V_HC formula derivation, KPI sources, confidence levels |
| [docs/DEPLOYMENT_STRATEGY.md](docs/DEPLOYMENT_STRATEGY.md) | Production deployment, security, scaling |
| [docs/GDPR_COMPLIANCE.md](docs/GDPR_COMPLIANCE.md) | Data privacy, aggregation approach, compliance notes |

---

## Data Sources

| File | Rows | KPI produced | Notes |
|------|------|-------------|-------|
| IMR surveys 2021–2024 | ~6,600 × 4 | Y (engagement) | Aggregated group-level |
| EAE evaluations 2023–2025 | ~6,400 | β (training quality) | BU-level averages |
| Training records | ~18,000 | λ (training volume) | Hours per employee |
| Absenteeism detail 2024–2025 | ~8,000 | ρ (absenteeism rate) | France scope only |
| NBI/FTE financial data 2022–2025 | 26 BUs × 4 years | P (productivity) | Δ% year-over-year |
| Action library | 26 actions | — | Sourced from CACEIS governance docs |

> **Note:** Raw data files (`Sujet Alberthon/`) are confidential and not included in this repository. Contact the team for access. The computed outputs (`kpi-output.json`, `action_library_raw.json`) are included for demonstration.

---

## GDPR Compliance

All KPIs are computed at Business Unit level (minimum 5 employees) — no individual-level data is stored, displayed, or transmitted. Source files remain on-premise and are never sent to external APIs; only aggregated BU metrics reach the Anthropic API as part of the RAG prompt. See [docs/GDPR_COMPLIANCE.md](docs/GDPR_COMPLIANCE.md) for the full compliance analysis.

---

## Presentation

Final project slides: [`slides/CACEIS_Final_Presentation.pdf`](slides/CACEIS_Final_Presentation.pdf)

---

## Authors

**AlbertSchool** · CACEIS HR Analytics Hackathon · 2025

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
