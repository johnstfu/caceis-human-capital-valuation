# Dashboard — pilot-bu-dashboard.html

`interface/pilot-bu-dashboard.html` est le seul fichier d'interface du projet.
Fichier HTML auto-contenu (~3 800 lignes), aucune dépendance de build.

---

## Lancement

```bash
# Via le serveur FastAPI (recommandé)
cd rag && python3 api.py
# → http://localhost:8000/dashboard/pilot-bu-dashboard.html

# En local direct (fonctions statiques uniquement, pas de RAG)
open interface/pilot-bu-dashboard.html
```

---

## Structure de la page

```
Topbar
  └── Logo · Titre BU · Sélecteur BU · Tier toggle · Bouton Démo · Actions (IA, Guide, Export…)

Sidebar (mobile / navigation)
  └── Liens section · Lien Suivi · Documentation

Contenu (scroll vertical)
  ├── 1. Access Tier Selector
  ├── 2. KPI Scorecard
  ├── 3. Group Benchmark
  ├── 4. Action Levers (RAG)
  ├── 5. Trend & Multi-KPI charts
  ├── 6. Absenteeism chart
  ├── 7. Composite HCV Score (Model internals)
  ├── 8. Suivi des actions
  └── 9. Documentation / Lexique

Panneau RAG (slide-in droit)
```

---

## 1. Access Tier Selector

Trois profils d'accès configurables depuis la topbar (boutons T1 / T2 / T3) ou depuis les cartes de sélection en haut de page.

| Tier | Profil | Sections visibles |
|------|--------|-------------------|
| **T1** | Chief Officer | Tout — KPIs, benchmarks, leviers détaillés, suivi, model internals |
| **T2** | BU Leadership | KPIs + benchmarks + leviers résumés — pas de model internals ni suivi |
| **T3** | Operational Manager | KPI scorecard uniquement |

Le tier actif est mémorisé dans `data-tier` sur le `<body>` et contrôle la visibilité CSS via `setTier(n)`.

---

## 2. KPI Scorecard

Cinq cartes KPI disposées en grille :

| Carte | KPI | Unité | Seuil d'alerte |
|-------|-----|-------|---------------|
| Engagement | Y | /5 | < 3.40 |
| Training Volume | λ | h/emp/an | < 44.6 h |
| Training Quality | β | /5 | < 3.40 |
| Productivity | P | Δ% NBI/FTE | — (indicateur de résultat) |
| Absenteeism | ρ | % | > 4.8 % |

Chaque carte affiche :
- La valeur brute + barre de progression colorée
- Un **texte plain-language** (11px italique) qui traduit la valeur en phrase métier
- Un **bouton `? Expliquer`** (T1 + T2) qui ouvre le panel RAG en mode simplifié et envoie automatiquement un prompt pré-rédigé

En dessous des cartes : une **snapshot insight** dynamique (`Principal gap : … · Point fort : …`) générée à partir des KPIs réels de la BU.

### Couleurs des barres KPI

- **Vert** (`--green-l`) : au-dessus de la moyenne groupe
- **Amber** (`--amber-l`) : légèrement sous la moyenne
- **Coral** (`--coral-l`) : en alerte

---

## 3. Group Benchmark

Deux panneaux côte à côte :

**Benchmark bars** — comparaison visuelle BU vs groupe pour Y, λ, β, ρ.
Chaque ligne affiche : valeur BU · barre · valeur groupe · pill colorée (▲ above / ▼ below).

**Radar chart** — graphique pentagon (Chart.js) superposant la BU et la moyenne groupe sur les 5 axes KPI.

---

## 4. Action Levers — RAG

Section centrale du dashboard. Déclenchée par le bouton **Generate recommendations**.

### Flux

1. `generateLevers()` appelle `GET /api/scorecard/{bu_name}`
2. Le pipeline RAG (retriever + ActionStore + Claude) retourne un scorecard JSON
3. `renderLevers(scorecard, buName)` injecte les leviers dans la page

### Contenu généré

**Recommandations IA** (2–3 par BU) :
- Badge **Priorité 1 / 2 / 3** (coloré coral / amber / gris) calculé par `LEVER_SCORER`
- Titre du levier + KPI impacté
- Description actionnable avec source citée `[Source: ACT_XXX]`
- Ligne impact estimé + timing (`lever-timing`)
- Chips d'IDs d'actions (`ACT_001`, `ACT_002`…)
- Bouton **Valider** → enregistre dans le Suivi

**Actions de la bibliothèque** (issues de `action_library_raw.json`) :
- Organisées par KPI (Y / λ / β / ρ)
- Même structure badge priorité + bouton Valider

### Scoring des priorités (LEVER_SCORER)

```
score = gapScore(kpi, valeur_BU) + delaiScore(delai_effet) + careerPenalty
```

- `gapScore` : proportionnel à l'écart BU vs moyenne groupe
- `delaiScore` : 3 pts si effet 1–3 mois, 2 pts si 3–6 mois, 1 pt si 6–12 mois
- `careerPenalty` : −0.5 si action de type `career_development`

---

## 5. Trend & Multi-KPI Charts

**Trend chart** — évolution temporelle de Y (engagement) sur 2021–2024 pour la BU sélectionnée vs moyenne groupe. Chart.js line chart.

**Multi-KPI chart** — graphique multi-axes affichant λ, β, ρ côte à côte pour la BU. Permet de repérer visuellement les KPIs en décalage.

---

## 6. Absenteeism Chart

Histogramme mensuel du taux d'absentéisme 2024 (France) pour la BU sélectionnée, avec ligne de référence à 4.8% (moyenne groupe).

---

## 7. Composite HCV Score — Model internals

*Visible T1 uniquement.*

Graphique en barres horizontales décomposant la contribution de chaque KPI au score V_HC final, avec les poids PCA (Y×0.35 + λ×0.20 + β×0.25 + P×0.10 + (1−ρ)×0.10).

Affiche le score composite final et le rang de la BU (`X/26`).

---

## 8. Suivi des actions

*Visible T1 uniquement.*

Tableau des actions validées depuis la section Action Levers. Persiste dans `localStorage` (clé `hcv_suivi`).

### Colonnes

| Colonne | Description |
|---------|-------------|
| ID | Identifiant action (`ACT_XXX`) |
| Action | Titre |
| KPI | KPI cible |
| BU | Business Unit au moment de la validation |
| Validée le | Date ISO |
| Statut | `Not started` / `In progress` / `Done` (sélecteur inline) |

### Jalons automatiques

À chaque validation, trois jalons sont générés :

| Jalon | Délai | Objectif |
|-------|-------|----------|
| Kick-off | J+7 | Lancer l'action |
| Mi-parcours | J+45 | Point d'étape |
| Mesure KPI | J+90 | Évaluer l'impact |

Un jalon en retard (date dépassée, non coché) passe en **coral** avec badge `En retard`.
Le badge Suivi dans la sidebar devient **amber** si au moins un jalon est en retard, **vert** sinon.

### Barre de progression

Affichée en haut à droite : `X / N actions terminées` avec barre de fill verte.

### Boutons

- **Réinitialiser** — vide toutes les actions actives (avec confirmation)
- **Reset démo** — visible uniquement après un parcours Mode Démo

---

## 9. Documentation / Lexique

Accordéon à 4 panneaux :

| Panneau | Contenu |
|---------|---------|
| Formule V_HC | Décomposition mathématique de l'indice composite |
| Les 5 KPIs | Définition, source, seuil d'alerte de chaque KPI |
| Glossaire | Termes métier (IMR, EAE, FABLife, QVT, RAG…) |
| Limites du modèle | Biais potentiels, périmètre France pour ρ, taille des BUs |

---

## Panneau RAG (IA)

Panneau slide-in depuis la droite, accessible via le bouton **IA** dans la topbar ou le FAB flottant.

### Modes

| Mode | Déclencheur | Comportement |
|------|-------------|-------------|
| **Expert** | Question libre de l'utilisateur | RAG complet avec sources citées |
| **Simplifié** | Bouton `? Expliquer` sur une carte KPI | Réponse en 2–3 phrases sans jargon, sans sources |

Un badge mode (violet = expert, amber = simplifié) s'affiche 5 secondes après le déclenchement.

### Fonctions clés

- `sendRagMessage()` — envoie `POST /api/query` avec la question + top_k=5
- `ragSendExplain(prompt, notif, hideSources)` — mode simplifié avec sources masquées
- `explainKpi(kpi)` — construit le prompt depuis `EXPLAIN_PROMPTS[kpi]` avec la valeur réelle de la BU
- `ragShortcut(text)` — insère un texte pré-rédigé dans l'input

---

## Mode Démo

*Visible T1 uniquement.* Bouton **Démo** dans la topbar.

Parcours automatique en 4 actes :

| Acte | Action |
|------|--------|
| 1 | Sélectionne Finance & Admin, scroll vers le scorecard |
| 2 | Scroll vers les leviers, déclenche Generate recommendations |
| 3 | Valide le premier levier affiché |
| 4 | Ferme le panel RAG, scroll vers le Suivi |

Après la démo : bouton **Reset démo** apparaît dans le header Suivi pour remettre à zéro.

---

## Données

Le dashboard charge les données KPI depuis trois sources en fallback :

```javascript
1. './data/kpi-output.json'          // fichier local (dev)
2. '../rag/data/kpi-output.json'     // relatif au repo
3. 'http://localhost:8000/api/kpi-data'  // serveur FastAPI (prod)
```

Le scorecard RAG et le chat IA nécessitent le serveur (`api.py`) avec une clé Anthropic valide.

---

## Design system

| Variable | Valeur | Usage |
|----------|--------|-------|
| `--bg` | `#0d0d14` | Fond page |
| `--bg-card` | `#13131f` | Fond cartes |
| `--purple-l` | `#a8a0ff` | Accent principal, liens |
| `--amber-l` | `#f0b545` | Alertes moyennes, badges |
| `--coral-l` | `#f08080` | Alertes critiques, retards |
| `--green-l` | `#56d487` | États positifs, done |
| `--blue-l` | `#6ab0f5` | Bouton IA, sources |
| `--muted` | `#8888a8` | Textes secondaires |
