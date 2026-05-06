# Architecture Technique — CACEIS Human Capital Valuation

---

## 1. Vue d'ensemble

Le système est structuré en deux couches indépendantes qui se composent :

```
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 1 — DÉTERMINISTE                                     │
│  Notebook Python + pandas → KPIs par BU → kpi-output.json   │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│  COUCHE 2 — SÉMANTIQUE                                       │
│  ChromaDB + ActionStore + Claude → Scorecard par BU          │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│  INTERFACE                                                   │
│  FastAPI (api.py) → pilot-bu-dashboard.html                  │
└─────────────────────────────────────────────────────────────┘
```

Les deux couches sont découplées : la couche déterministe peut tourner sans réseau, la couche sémantique appelle l'API Anthropic uniquement à la demande (bouton "Generate recommendations").

---

## 2. Couche déterministe

**Fichier principal :** `notebooks/CACEIS_Human_Capital_Valuation.ipynb`
**Sortie :** `rag/data/kpi-output.json`

### Pipeline

```
Excel brut (6 sources)
    │
    ├── IMR 2021–2024          → kpi_Y     (engagement moyen /5 par BU)
    ├── EAE / Quick Review     → kpi_beta  (qualité formation /5)
    ├── Training Records       → kpi_lambda (heures formation / ETP)
    ├── Absenteeism detail     → kpi_rho   (taux absentéisme %)
    ├── NBI/FTE financier      → kpi_P     (productivité Δ% YoY)
    └── Tous                   → V_HC      (indice composite 0→1)
```

### Formule V_HC

```
V_HC = 0.35·norm(Y) + 0.20·norm(λ) + 0.25·norm(β) + 0.10·norm(P) − 0.10·norm(ρ)
```

Normalisation min-max sur les 26 BUs. ρ entre avec un signe négatif (absentéisme élevé = malus).

### Sorties dans kpi-output.json

- `business_units[]` : 26 objets BU avec tous les KPIs, rang, effectif, sources
- `group_summary` : moyennes et percentiles groupe
- `composite_index` : poids et métadonnées de la formule
- `imr_series_*` : séries temporelles pour les graphiques de tendance
- `absenteeism_fr_monthly_2024` : données mensuelles pour le graphique d'absentéisme

---

## 3. Couche sémantique

### 3.1 Indexation (ingest_all.py)

```
Documents source (14 PDFs/DOCX)
    │
    ├── loader.py     → extraction texte brut
    ├── chunker.py    → découpe en chunks ~500 tokens avec overlap
    ├── embedder.py   → sentence-transformers (all-MiniLM-L6-v2)
    └── vector_store.py → persistance ChromaDB (local, ~15MB)
```

L'indexation est **one-shot** : elle s'exécute une fois sur les fichiers sources confidentiels. Le résultat (`chroma_db/`) est gitignored mais persistant localement.

### 3.2 Retrieval (retriever.py)

Pour une BU donnée, `CACEISRetriever.retrieve(query, top_k=7)` :
1. Embed la query avec le même modèle sentence-transformers
2. Interroge ChromaDB par similarité cosinus
3. Retourne les 7 chunks les plus proches avec score et source

La query est construite dynamiquement par `rag_pipeline._build_query()` en fonction des gaps KPI de la BU.

### 3.3 ActionStore (action_store.py)

Lookup **déterministe** sur `action_library_raw.json` : 26 actions sourcées pré-validées, indexées par KPI cible et gap threshold. Pour chaque BU, l'ActionStore sélectionne les actions pertinentes **avant** l'appel LLM, ce qui :
- Garantit que les recommandations s'appuient sur des actions réelles CACEIS
- Réduit le risque d'hallucination
- Rend les recommandations auditables (chaque action a un ID `ACT_XXX` et une source)

### 3.4 Génération (generator.py)

`CACEISGenerator.generate_scorecard()` envoie à Claude Sonnet un prompt structuré :

```
System : rôle conseiller RH CACEIS senior, règles de citation, format JSON obligatoire
User   : KPIs de la BU + actions pré-sélectionnées (priorité 1) + contexte ChromaDB (priorité 2)
```

Le modèle retourne un JSON `scorecard` avec :
- `summary` : situation RH en 1 phrase
- `recommendations[]` : 2–3 recommandations avec source, priorité, KPI impacté, impact estimé
- `confidence` / `confidence_reason`
- `alert_kpis` : liste des KPIs en dessous des seuils groupe

---

## 4. Interface

### FastAPI (api.py)

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `GET /` | GET | Redirect vers le dashboard |
| `GET /api/status` | GET | Statut ChromaDB (nb chunks, sources) |
| `GET /api/bus` | GET | Liste des 26 BUs |
| `GET /api/kpi-data` | GET | kpi-output.json complet (statique) |
| `GET /api/scorecard/{bu}` | GET | Scorecard RAG complet pour une BU |
| `POST /api/query` | POST | Question libre sur la base documentaire |
| `GET /dashboard/*` | GET | Fichiers statiques (pilot-bu-dashboard.html) |

### Dashboard (pilot-bu-dashboard.html)

Fichier HTML auto-contenu (~3800 lignes). Architecture interne :

```
KPI_DATA (JSON)          → fetch /api/kpi-data au chargement
onBuChange(buId)         → met à jour tous les composants
generateLevers()         → appelle /api/scorecard/{bu}, render leviers
sendRagMessage()         → appelle /api/query, affiche réponse
setTier(1|2|3)           → contrôle la visibilité des sections
localStorage hcv_suivi   → suivi des actions avec jalons J+7/J+45/J+90
```

**Tiers d'accès :**
- T1 (Chief Officer) : accès complet — KPIs, benchmarks, leviers détaillés, suivi, model internals
- T2 (BU Leadership) : KPIs + leviers résumés, pas de model internals ni suivi
- T3 (Operational) : scorecard KPI uniquement

---

## 5. Flux de données complet

```
[Excel brut]
     │ pandas / openpyxl
     ▼
[kpi-output.json]  ←─────────────────────────────────────────┐
     │                                                        │
     │ GET /api/kpi-data                                      │
     ▼                                                        │
[Dashboard — KPI cards, charts, benchmarks]                  │
     │                                                        │
     │ clic "Generate recommendations"                        │
     ▼                                                        │
[GET /api/scorecard/{bu}]                                     │
     │                                                        │
     ├── _build_query(bu, kpi_data)                           │
     │        │                                               │
     │        ▼                                               │
     │   [ChromaDB] → top-7 chunks                           │
     │                                                        │
     ├── ActionStore.get_all_actions_for_gaps(kpi_data)       │
     │        │                                               │
     │        ▼                                               │
     │   [action_library_raw.json] → actions filtrées        │
     │                                                        │
     └── generator.generate_scorecard(bu, kpi_data, chunks, actions)
              │
              ▼
         [Anthropic Claude Sonnet]
              │
              ▼
         scorecard JSON → Dashboard (leviers, badges priorité, suivi)
```

---

## 6. Stack technique

| Composant | Technologie | Version | Rôle |
|-----------|------------|---------|------|
| KPI pipeline | Python + pandas | 3.9+ / 2.x | Calcul déterministe |
| Embedding | sentence-transformers | — | Vectorisation chunks |
| Vector store | ChromaDB | — | Index sémantique local |
| LLM | Anthropic Claude Sonnet 4.6 | — | Génération recommandations |
| API | FastAPI + uvicorn | — | Serveur HTTP |
| Dashboard | HTML/CSS/JS vanilla | — | Interface utilisateur |
| Charts | Chart.js | 4.x | Radar, trend, multi-chart |
| Icons | Font Awesome | 6.5 | Icônes UI |

---

## 7. Décisions d'architecture

### Pourquoi RAG plutôt que fine-tuning ?

Les documents CACEIS sont trop peu nombreux (~14) et trop spécialisés pour entraîner un modèle. Le RAG permet de citer des sources précises et de mettre à jour la base documentaire sans ré-entraînement.

### Pourquoi pas LangChain ?

LangChain introduit une abstraction inutile pour ce cas d'usage. Le pipeline est simple (retrieve → format → generate) et l'implémenter directement donne un meilleur contrôle sur les prompts, les erreurs et les performances. Moins de dépendances = moins de surface de panne.

### Pourquoi localStorage pour le suivi des actions ?

Le suivi jalonné (J+7 / J+45 / J+90) est intentionnellement côté client : pas de base de données à déployer, pas de compte utilisateur, démo possible sans backend. La contrainte acceptée est que le suivi ne persiste que sur le navigateur courant.

### Pourquoi un fichier HTML monolithique pour le dashboard ?

Zéro configuration de build (webpack, vite, etc.), déployable partout, versioable dans un seul commit. Le coût est la taille (~3800 lignes), acceptable pour un prototype.

### Pourquoi deux copies de kpi-output.json (supprimées) ?

Un doublon avait été créé dans `interface/data/` lors du développement. Supprimé à l'étape 0 du nettoyage repo — source canonique = `rag/data/kpi-output.json`.
