# CLAUDE.md — CACEIS Human Capital Valuation

## Arborescence & rôles

```
CACEIS/
├── interface/                    Couche présentation : dashboard HTML statique auto-contenu
│   ├── pilot-bu-dashboard.html   Dashboard T1/T2/T3 — Chart.js, tier toggle, tour guidé, levers
│   ├── index.html                Landing page institutionnelle
│   ├── guide.html                Documentation interactive 7 sections
│   └── data/generate-kpi.py     Recalcul KPI : Excel brut → kpi-output.json (lancement manuel)
│
├── rag/                          Couche sémantique : FastAPI + ChromaDB + ActionStore + Claude
│   ├── api.py                    Serveur HTTP — 6 endpoints (GET/POST)
│   ├── pipeline/rag_pipeline.py  Orchestration : retrieve → action_store → generate
│   ├── retrieval/retriever.py    Recherche sémantique ChromaDB (top-7 chunks)
│   ├── generation/generator.py   Appels Claude Sonnet — scorecard JSON structuré
│   ├── store/action_store.py     Gate déterministe sur action_library_raw.json (26 actions)
│   ├── store/vector_store.py     Gestion index ChromaDB local (~15 MB)
│   ├── ingest/                   Pipeline one-shot : loader → chunker → embedder
│   ├── agent/                    Module chatbot "Julien" — voir rag/agent/README.md
│   └── data/
│       ├── kpi-output.json       ← SOURCE DE VÉRITÉ (voir ci-dessous)
│       └── action_library_raw.json  26 actions RH pré-validées, auditables (ACT_001…ACT_026)
│
├── notebooks/                    Couche calcul : V_HC pandas, 38 cellules
│   └── CACEIS_Human_Capital_Valuation.ipynb
│
└── docs/                         Documentation technique
    ├── ARCHITECTURE.md           Vue 2-couches, flux de données, décisions d'architecture
    ├── KPI_DEFINITIONS.md        Formules, poids, seuils — référence formelle
    ├── GDPR_COMPLIANCE.md        Contraintes légales (agrégation, anonymisation, IRP)
    └── AUDIT.md                  Rapport d'audit (état des lieux, écarts, améliorations)
```

## Source de vérité données

**`rag/data/kpi-output.json`** — 26 BUs, agrégation stricte (min. 5 employés par cellule).

> **INTERDIT ABSOLU : aucun scoring individuel, aucune donnée nominative à quelque étape que
> ce soit du pipeline (ingest, chunks, embeddings, logs, réponses API, interface).**
> Référence : `docs/GDPR_COMPLIANCE.md`.

## Formule V_HC

```
V_HC = 0.35·norm(Y) + 0.20·norm(λ) + 0.25·norm(β) + 0.10·norm(P) − 0.10·norm(ρ)
```

Normalisation min-max sur les 26 BUs. ρ entre avec signe négatif (absentéisme élevé = malus).

### Hiérarchie KPI

| Niveau | KPIs | Usage |
|--------|------|-------|
| **Board / CFAO** | Y, P, ρ | Arbitrage budgétaire, décision stratégique |
| **Opérationnel** | λ, β | Leviers RH — pilotage management |

- P est un **indicateur de résultat** (lagging) : les leviers sont Y, λ, β. Pas d'action directe sur P.
- ρ (absentéisme) : seuil alerte France > 4,8 %. Scope France uniquement.

## Contraintes cardinales

1. **GDPR / IRP** : agrégation BU uniquement. Aucune donnée individuelle dans les chunks, logs ou réponses.
2. **Gate ActionStore** : l'agent argumente UNIQUEMENT depuis `action_library_raw.json`. Il ne génère jamais d'actions RH librement. Toute suggestion hors bibliothèque entre en `suggestion_queue` (non validée) — elle n'est jamais présentée comme action officielle.
3. **Positionnement CFAO** : instrument d'arbitrage budgétaire pour le DAF/CFAO. Ne jamais empiéter sur le terrain du CHRO.
4. **Vocabulaire interne** : Finance & Admin = **SPF** (fonction support). Ne pas désigner comme "BU".
5. **Ancrage financier** : ratio NBI/FTE ≈ 315 k€/tête. Pont obligatoire entre score humain et langage financier dans toute recommandation board-level.

## Commandes utiles

```bash
# Lancer le backend API (depuis rag/)
cd rag && python3 api.py
# → Dashboard : http://localhost:8000/dashboard/pilot-bu-dashboard.html
# → API docs  : http://localhost:8000/docs

# Recalculer les KPIs (depuis interface/data/)
cd interface/data && python3 generate-kpi.py
# → écrase rag/data/kpi-output.json

# Réindexer ChromaDB après ajout de documents (depuis rag/)
cd rag && python3 ingest_all.py

# Dashboard en mode statique (sans backend)
open interface/pilot-bu-dashboard.html
```

## Ce qui manque sciemment — ne pas "réparer" spontanément

| Manque | Raison délibérée |
|--------|-----------------|
| Pas de tests (pytest, Jest) | Hors scope MVP — à ajouter en phase prod |
| Pas de CI/CD | Déploiement manuel intentionnel à ce stade |
| localStorage pour suivi jalons | Pas de DB à déployer — choix de simplicité |
| HTML monolithique (4 278 lignes) | Zéro build tooling — documenté ARCHITECTURE.md §7 |
| CORS `allow_origins=["*"]` | Acceptable en démo locale — à restreindre en prod |
| IMR 2023-2024 hardcodés | PDFs image non OCRisés — valeurs manuelles documentées |
