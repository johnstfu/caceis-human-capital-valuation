# AUDIT.md — CACEIS Human Capital Valuation
## Rapport lecture seule — 2026-06-08

> **Périmètre** : cohérence docs/code, déterminisme ActionStore, risques RGPD, hygiène secrets.
> **Règle** : ce fichier décrit, il ne modifie pas. Aucun fichier de données ni logique métier n'a été touché.

---

## 1. Cohérence KPI_DEFINITIONS.md ↔ generate-kpi.py ↔ notebook

### 1.1 β — Qualité de formation : écart de définition ⚠️

**KPI_DEFINITIONS.md** déclare :
> β — Source : "EAE (Entretien Annuel d'Évaluation) + Quick Review ratings"

**Réalité dans le code** :
- `action_store.py` utilise la clé `kpi_beta_qr` (Quick Review uniquement) pour la détection de gap (seuil 3,40).
- `generator.py` construit son résumé KPI avec `kpi_beta_qr` et le label explicite `"β — Qualité formation QR"`.
- `kpi-output.json` expose deux champs distincts : `kpi_beta_eae` (EAE) et `kpi_beta_qr` (Quick Review).
- Le dashboard utilise `kpi_beta_eae` pour les charts, `kpi_beta_qr` pour les leviers.

**Écart** : la doc dit "EAE + QR combinés" mais le pipeline opérationnel utilise QR seul comme β. La définition formelle et le code ne sont pas alignés sur la même source.

**Risque** : un prompt Claude Code écrit depuis KPI_DEFINITIONS.md utilisera la mauvaise clé JSON.

---

### 1.2 P — Productivité : CAGR vs YoY ⚠️

**KPI_DEFINITIONS.md** déclare :
> P — Unit : "Year-over-year % change in Net Banking Income per FTE"

**Réalité dans generate-kpi.py** :
Le script calcule un **CAGR 2022→2025** (Compound Annual Growth Rate sur 3 ans), pas un YoY.

**Écart** : "year-over-year" implique N vs N-1. Un CAGR sur 3 ans est une métrique différente (lissée, moins volatile). Les deux ont des usages légitimes, mais la doc doit être corrigée pour refléter ce que le code fait réellement.

---

### 1.3 ρ — Absentéisme : scope non documenté ✅ / ⚠️

KPI_DEFINITIONS.md mentionne "France only" — c'est correct et documenté. Mais ni la doc ni le dashboard n'alertent l'utilisateur que ρ est **invalide pour les BUs hors France** (14 pays dans le groupe). Le champ `kpi_rho` global appliqué à toutes les BUs peut induire une comparaison trompeuse.

---

### 1.4 Poids V_HC : cohérents ✅

| KPI | KPI_DEFINITIONS.md | ARCHITECTURE.md | generate-kpi.py (attendu) |
|-----|-------------------|-----------------|--------------------------|
| Y   | 0.35              | 0.35            | 0.35 |
| λ   | 0.20              | 0.20            | 0.20 |
| β   | 0.25              | 0.25            | 0.25 |
| P   | 0.10              | 0.10            | 0.10 |
| ρ   | −0.10             | −0.10           | −0.10 |

Cohérents entre docs et code. Aucun écart.

---

## 2. Déterminisme de l'ActionStore — la gate tient-elle vraiment ?

### 2.1 Ce que l'ActionStore garantit ✅

`action_store.py` est solide :
- Singleton chargé depuis `action_library_raw.json` uniquement.
- `get_all_actions_for_gaps()` retourne exclusivement des actions de la bibliothèque.
- ACT_013 exclue explicitement (sessions annulées).
- Le `format_for_prompt()` injecte les actions **avant** le contexte ChromaDB dans le user_message.

### 2.2 La faille : le SYSTEM_PROMPT ne ferme pas la porte ⚠️ CRITIQUE

Dans `generator.py`, le SYSTEM_PROMPT dit :

```
SOURCES DE RECOMMANDATIONS (dans cet ordre de priorité) :
1. ACTIONS PRÉ-SÉLECTIONNÉES [...] À intégrer en priorité.
2. CONTEXTE DOCUMENTAIRE [...] Complément si les actions pré-sélectionnées ne couvrent pas tous les gaps.
```

**Ce qui manque** : il n'y a **aucune clause d'interdiction** explicite. Claude peut légitimement interpréter "complément" comme une permission de générer des actions libres depuis les chunks documentaires. La formulation "à intégrer en priorité" n'est pas équivalente à "tu ne peux proposer que des actions de cette liste".

**Conséquence** : si ChromaDB retourne un chunk mentionnant un programme inexistant ou non validé, le générateur peut le présenter comme recommandation sans ID ACT_XXX et sans source formelle. Le dashboard l'affichera sans badge "bibliothèque" mais sans erreur visible.

**Correction suggérée** (1 ligne dans SYSTEM_PROMPT) :
```
RÈGLE ABSOLUE : tu ne proposes JAMAIS une action qui n'est pas dans la liste des ACTIONS
PRÉ-SÉLECTIONNÉES ci-dessus. Si aucune action pré-sélectionnée ne couvre un gap, indique
explicitement "Aucune action disponible en bibliothèque pour ce KPI" — ne génère rien de libre.
```

### 2.3 Pattern career_development : non couvert par la gate ⚠️

`action_store.py` détecte le pattern (Y < 3,40 ET λ ≥ moyenne) et retourne `career_dev_actions`. Mais le SYSTEM_PROMPT de `generator.py` ne contient pas d'instruction sur ce pattern. Claude peut raisonner différemment et ignorer les actions career_dev injectées.

---

## 3. Pipeline RAG — risques de fuite de données individuelles

### 3.1 loader.py — SKIP_FILES : protection partielle ✅ / ⚠️

**Bien géré** :
- `Absentéisme_-_détail_affectation_*.xlsx` : explicitement ignorés.
- `2025 - Stats CACEIS EAE EP fichier de travail.xlsx` : ignoré.
- Fichiers > 8 MB : ignorés.

**Risque résiduel** :
- `Training_Records_Unnamed.xlsx` : **non ignoré**, lit jusqu'à 200 lignes × 12 colonnes. Si les premières lignes contiennent des identifiants employés (matricule, nom), ils seraient indexés dans ChromaDB.
- `RESULTATS ENQUETE MANAGERS.pdf` : indexé. Selon son contenu réel, des verbatims nominatifs pourraient être présents (enquêtes managers parfois semi-nominatives).

### 3.2 chunker.py — aucun filtre PII ⚠️

`chunk_document()` découpe le texte brut tel quel. **Aucun filtre regex ou NER** pour détecter et masquer : noms propres, matricules, adresses email, numéros de téléphone.

Si `loader.py` laisse passer un document avec des données nominatives, `chunker.py` les fragmente et `embedder.py` les vectorise sans alerte.

### 3.3 api.py — exposition partielle des chunks via `/api/query` ⚠️

L'endpoint `POST /api/query` retourne :
```json
"chunks": [{"source": "...", "score": 0.9, "excerpt": "...200 chars..."}]
```
Si un chunk contient un nom propre, il est exposé dans la réponse API (200 caractères visibles). Pas de sanitisation avant l'envoi.

### 3.4 Logs : niveau WARNING — protection passive ✅

`api.py` log au niveau WARNING uniquement. Les queries utilisateurs et les contenus de chunks ne sont **pas loggés** vers un fichier. Protection acceptable en l'état.

### 3.5 Verdict RGPD

| Point de contrôle | Statut | Détail |
|-------------------|--------|--------|
| Fichiers absentéisme détaillés | ✅ ignorés | SKIP_FILES |
| EAE brut (travail) | ✅ ignoré | SKIP_FILES |
| Training_Records | ⚠️ à vérifier | 200 premières lignes indexées |
| Résultats enquête managers | ⚠️ à vérifier | Contenu nominatif possible |
| Filtre PII chunker | ❌ absent | Aucun filtre regex/NER |
| Exposition chunks API | ⚠️ partielle | 200 chars excerpt retourné |

---

## 4. Hygiène secrets

| Contrôle | Statut | Détail |
|----------|--------|--------|
| `.env` dans `.gitignore` | ✅ | Couvert |
| `.env.example` sans clé réelle | ✅ | `sk-ant-your-key-here` |
| Clé hardcodée dans le code | ✅ absent | `os.getenv()` partout |
| **Chemin absolu hardcodé** | ❌ **PROBLÈME** | Voir ci-dessous |
| Rotation de clé documentée | ❌ absent | Pas de procédure |

**Problème chemin absolu** — `loader.py` ligne 27 :
```python
BASE = Path("/Users/rayanekryslak-medioub/Desktop/CACEIS/Sujet Alberthon")
```

Ce chemin est spécifique à la machine du développeur. `ingest_all.py` plantera sur tout autre environnement (collègue, CI, VM). À remplacer par :
```python
BASE = Path(os.getenv("CACEIS_DATA_DIR", Path(__file__).parent.parent.parent / "Sujet Alberthon"))
```

---

## 5. Améliorations prioritaires — à arbitrer

> Les items ci-dessous sont listés, non implémentés. Validation requise avant action.

### #1 — Fermer la gate ActionStore dans le SYSTEM_PROMPT [effort : 30 min / impact : CRITIQUE]

Ajouter dans `generator.py` SYSTEM_PROMPT une clause interdisant explicitement la génération libre d'actions hors bibliothèque. Actuellement, "à intégrer en priorité" ≠ "exclusivement".

### #2 — Corriger le chemin absolu dans loader.py [effort : 15 min / impact : HAUT]

Remplacer `BASE = Path("/Users/rayanekryslak-medioub/...")` par une variable d'environnement `CACEIS_DATA_DIR` avec fallback relatif. Bloquer pour tout déploiement sur autre machine.

### #3 — Aligner β dans KPI_DEFINITIONS.md [effort : 30 min / impact : MOYEN]

Clarifier si β opérationnel = `kpi_beta_qr` (Quick Review) ou `kpi_beta_eae` (EAE) ou une combinaison. Mettre à jour KPI_DEFINITIONS.md avec la définition exacte utilisée dans le pipeline.

### #4 — Vérifier Training_Records.xlsx et RESULTATS ENQUETE MANAGERS.pdf [effort : 1h / impact : HAUT RGPD]

Ouvrir manuellement ces deux fichiers et confirmer l'absence de données nominatives dans les 200 premières lignes (Training) et dans le contenu texte (PDF). Si présence : soit ajouter à SKIP_FILES, soit pré-anonymiser avant ingest.

### #5 — Corriger P dans KPI_DEFINITIONS.md : CAGR ≠ YoY [effort : 15 min / impact : MOYEN]

La doc dit "year-over-year" mais le code calcule un CAGR 2022→2025. Corriger la doc pour refléter la réalité ou aligner le code sur la définition.

---

## Résumé exécutif

| Dimension | Verdict |
|-----------|---------|
| Cohérence formule V_HC | ✅ Poids corrects — β et P mal documentés |
| Gate ActionStore | ⚠️ Déterministe côté store, contournable côté prompt |
| Risque RGPD pipeline | ⚠️ 2 fichiers à vérifier, 0 filtre PII actif |
| Hygiène secrets | ⚠️ Chemin absolu hardcodé — bloquant hors dev machine |

**Aucun blocker de sécurité grave** — le projet est sain pour une démo. Les 5 items ci-dessus suffisent pour passer en POC production.
