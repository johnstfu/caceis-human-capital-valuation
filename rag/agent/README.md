# rag/agent — Chatbot "Julien" (assistant CFAO)

## Rôle

Julien est un assistant conversationnel destiné au CFAO (Chief Financial & Administrative Officer) de CACEIS.
Il aide à l'arbitrage budgétaire entre BUs, pousse proactivement les KPI pertinents (Y, P, ρ)
et s'améliore à l'usage — uniquement sur la couche conversationnelle, jamais sur les données RH.

---

## Flux de traitement

```
message CFAO
    │
    ▼
[cfo_persona.py]          Injecte le system prompt : ton CFAO, vocabulaire CACEIS,
    │                     NBI/FTE, refus d'empiéter sur le CHRO
    ▼
[bu_context.py]           Charge le contexte BU depuis kpi-output.json (agrégé only)
    │
    ▼
[retrieval — existant]    Recherche sémantique ChromaDB (top-7 chunks)
    │
    ▼
[ActionStore — existant]  Gate déterministe : 26 actions pré-validées uniquement
    │ ← GATE : aucune action libre ne passe cette étape
    ▼
[kpi_push/prioritizer]    Ordonne les KPI à mettre en avant (défaut : Y, P, ρ)
    │
    ▼
[questions/selector]      Sélectionne 1-2 questions de relance contextuelles
    │
    ▼
[orchestrator.py]         Compose et envoie la réponse finale
    │
    ▼
réponse CFAO (texte + KPI poussés + questions de relance)
    │
    ▼
[feedback/signal_logger]  Journalise les signaux d'usage AGRÉGÉS (jamais nominatifs)
    │
    ▼
[feedback/ranking_updater] Met à jour les poids de ranking KPI/questions
```

---

## Ce qui apprend / ce qui n'apprend pas

### Boucles d'apprentissage légitimes

| Boucle | Mécanisme | Périmètre |
|--------|-----------|-----------|
| Ranking des KPI poussés | `ranking_updater.py` ajuste les poids selon les KPI creusés par l'utilisateur | Préférences d'affichage — aucun lien avec un individu |
| Reformulation des questions de relance | `ranking_updater.py` favorise les questions retenues vs ignorées | Style conversationnel uniquement |
| Feedback validation d'actions | `suggestion_queue.py` enregistre les suggestions de Julien | En attente de gate humaine — jamais dans l'ActionStore sans validation |

### Interdits absolus

| Interdit | Raison |
|----------|--------|
| Profil par employé | RGPD / IRP — données individuelles hors périmètre |
| Score individuel ajusté à l'usage | Contourne l'agrégation BU — interdit contractuellement |
| Feedback modifiant les données sources | `rag/data/kpi-output.json` est en lecture seule pour l'agent |

---

## Bouton feedback & toggle reco/perso

### Bouton feedback (suggestion_queue)

Julien peut décrire une recommandation qu'il aurait voulu faire mais qui n'existe pas
dans la bibliothèque d'actions. Ce flux est strictement encadré :

```
Julien décrit la reco
    │
    ▼
suggestion_queue.json   (taggée "suggéré par utilisateur, NON validé")
    │
    ├── Signal de ranking immédiat (priorité d'affichage)
    │
    └── Gate humaine (RH + Gouvernance) requise avant entrée dans ActionStore
             │
             ▼ si validée
        action_library_raw.json  (uniquement après décision humaine)
```

**L'agent ne ressort jamais une suggestion non validée comme action officielle.**

### Toggle reco/perso (PersonalizationMode)

Commutateur global dans `orchestrator.py` :

| Mode | Comportement |
|------|-------------|
| `ON` | Push recommandations, apprentissage de session actif |
| `OFF` | Réponses neutres, pas de push, pas d'apprentissage de session |

Utilisable en comité : permet à Julien de revenir à un mode "brut" à tout instant.

---

## Structure des fichiers

```
rag/agent/
├── __init__.py
├── README.md               (ce fichier)
├── orchestrator.py         Boucle de conversation principale + toggle reco/perso
│
├── context/
│   ├── cfo_persona.py      System prompt CFAO, vocabulaire CACEIS, ancrage NBI/FTE
│   └── bu_context.py       Chargement contexte BU depuis kpi-output.json
│
├── kpi_push/
│   ├── prioritizer.py      Ordonnancement des KPI à pousser
│   └── thresholds.py       Seuils d'alerte par KPI (paramétrables)
│
├── questions/
│   ├── question_pool.py    Banque de questions de relance
│   └── question_selector.py  Sélection contextuelle 1-2 questions
│
├── feedback/               ⚠️ Signaux d'usage agrégés UNIQUEMENT — voir feedback/README.md
│   ├── README.md
│   ├── signal_logger.py
│   ├── ranking_updater.py
│   ├── suggestion_queue.py
│   └── store/
│       ├── feedback_store.json    Poids appris (gitignored)
│       └── suggestion_queue.json  Suggestions en attente de gate (gitignored)
│
├── arbitrage/
│   ├── budget_advisor.py   Arbitrage budgétaire inter-BUs justifié par KPI
│   └── euro_bridge.py      Traduction score V_HC → euros via NBI/FTE
│
└── contracts/
    ├── schemas.py          Dataclasses Pydantic : tous les types d'échange
    └── INTERFACES.md       Contrats I/O entre sous-modules
```
