# AUDIT_CHIFFRES.md — Fiabilité des chiffres de présentation

> **Posture** : scepticisme par défaut. Chaque affirmation est vérifiée contre les sources
> du repo dans l'ordre de priorité : `kpi-output.json` → `generate-kpi.py` → notebook.
> Une affirmation sans source traçable est **NON SOURCÉ** jusqu'à preuve du contraire.
>
> **Périmètre** : chiffres apparaissant dans les slides "le défi" et "5 indicateurs".
> **Date d'audit** : 2026-06-09
> **Auditeur** : Claude Code (audit automatisé, lecture seule)

---

## 1. Tableau d'audit

### 1.1 Chiffres de volume (slide « Le défi »)

| Affirmation | Valeur présentée | Source trouvée | Valeur recalculée | Statut |
|---|---|---|---|---|
| Lignes brutes totales | 436 000+ | Aucune trace dans le repo | Non calculable (Excel requis) | **NON SOURCÉ** |
| Collaborateurs uniques | 12 711 | Aucune trace dans le repo | FTE 2024 = 6 636 (group_summary) | **NON SOURCÉ** |
| EAE — total lignes | 5 766 | `metadata.coverage.eae_evaluations` = 3 477 | 3 477 (valides) | **INCOHÉRENT** |
| EAE — valides | 3 477 | `metadata.coverage.eae_evaluations` = 3 477 | 3 477 ✓ | **VÉRIFIÉ** |
| EAE — taux validité | 88,8% | Aucune trace calculable | 3 477 / 5 766 = **60,3%** | **INCOHÉRENT** |
| Formations — total | 14 943 | `training.total_sessions` = 13 702 | 13 702 | **INCOHÉRENT** |
| Formations — exploitables | 13 446 | `training.total_sessions` = 13 702 | 13 702 (après filtre "annulé") | **INCOHÉRENT** |
| Lignes absentéisme | 127 825 | 12 points mensuels FR dans `absenteeism_fr_monthly_2024` | Non calculable (fallback utilisé) | **NON SOURCÉ** |
| Notes 2023 | 2 544 | EAE non segmenté par année dans le repo | Non calculable | **NON SOURCÉ** |
| Quick Reviews | 9 706 | Aucun count dans le repo (seule la moyenne 4,47 est stockée) | Non calculable | **NON SOURCÉ** |
| Lignes démographie | 275 609 | Données démographiques absentes du pipeline actuel | Non calculable | **NON SOURCÉ** |
| Nombre de BUs | 26 | `len(business_units)` = 26 | 26 ✓ | **VÉRIFIÉ** |

---

### 1.2 KPIs groupe (slide « 5 indicateurs »)

| Affirmation | Valeur présentée | Source trouvée | Valeur recalculée | Statut |
|---|---|---|---|---|
| Y (engagement) | 3,41 / 5 | `imr_series_group` 2021 = 3,41 · 2024 = **3,39** | 3,39 (2024) | **INCOHÉRENT** |
| λ (formation) | 68 h/pers | `group_summary.lambda_caceis_2024` = **44,6** (fallback hardcodé) | Avec FTE 2024 : 16,8 h · avec EAE pop : 32,2 h | **INCOHÉRENT** |
| β (performance) | 4,46 / 5 | `group_summary.beta_qr_caceis_2024` = **4,47** (Quick Review) · `beta_eae` = 3,39 | 4,47 (QR) ou 3,39 (EAE) | **APPROXIMATIF** |
| P (productivité financière) | +0,07 pt | Aucune valeur proche dans le repo | CAGR NBI/FTE 2022→2025 = **+0,14%** | **INCOHÉRENT** |
| ρ (absentéisme) | 2,6% | `kpi_rho.caceis_mean_stated` = 2,6 mais contexte = cible 2026 FA | `group_summary.rho_caceis_fr_2024` = **4,81%** | **INCOHÉRENT** |

---

### 1.3 Ratio NBI/FTE (fond de l'argumentation financière)

| Affirmation | Valeur présentée | Source trouvée | Valeur recalculée | Statut |
|---|---|---|---|---|
| NBI/FTE | ~315 k€/tête | `nbi_fte_series` : 315,4 (2022) · 314,0 (2024) · **316,7 (2025)** | 314,0 (2024) ou 316,7 (2025) selon année de référence | **APPROXIMATIF** |

---

### 1.4 Seuils d'alerte

| Affirmation | Valeur présentée | Source trouvée | Valeur recalculée | Statut |
|---|---|---|---|---|
| Seuil alerte Y | < 3,40 | `group_summary.Y_caceis_2024` = 3,39 | Seuil = moyenne groupe (arrondi) | **VÉRIFIÉ** |
| Seuil alerte β | < 3,40 | `group_summary.beta_eae_caceis_2024` = 3,39 | Seuil = moyenne groupe (arrondi) | **VÉRIFIÉ** |
| Seuil alerte λ | < 44,6 h | `group_summary.lambda_caceis_2024` = 44,6 | Seuil = moyenne groupe exacte | **VÉRIFIÉ** |
| Seuil alerte ρ (France) | > 4,8% | `group_summary.rho_caceis_fr_2024` = 4,81% | Seuil = moyenne groupe arrondie | **VÉRIFIÉ** |

---

## 2. Analyses détaillées par chiffre critique

### 2.1 Y = 3,41/5 — INCOHÉRENT

**Problème** : 3,41 est le score IER **2021**, pas le score 2024.

```
imr_series_group :
  2021 → Y = 3,41  (source : IER 2021, n=3004)   ← valeur présentée
  2022 → Y = 3,29
  2023 → Y = 3,38
  2024 → Y = 3,39  (source : IMR 2024, n≈3200)   ← valeur correcte
```

**Risque** : présenté comme score actuel, ce chiffre indique une tendance fictive
à la hausse (+0,02 vs 2023). Le score 2024 réel est 3,39, stable vs 2023.

**Recommandation** : remplacer par **Y = 3,39/5 (IMR 2024)**.
Si l'intention est de montrer la trajectoire, indiquer explicitement l'année.

---

### 2.2 λ = 68 h/pers — INCOHÉRENT

**Problème** : valeur introuvable dans le repo avec n'importe quel dénominateur documenté.

```
training.total_hours = 111 816 h

Avec FTE 2024 (6 636)   : 111 816 / 6 636 = 16,8 h/FTE
Avec EAE pop  (3 477)   : 111 816 / 3 477 = 32,2 h/EAE
Avec fallback repo       : 44,6 h (= hardcoded, denominator = inconnu)
Pour obtenir 68 h        : denominator ≈ 1 644 "employés formés"
                           → non documenté, non vérifiable
```

**Note technique** : `generate-kpi.py` pose `global_lambda = 44.6` comme fallback
car le fichier Training est anonymisé (IDs employés absents → `employees_trained = 0`).
La valeur 68 semble issue d'un calcul antérieur non versé dans le repo.

**Recommandation** :
- Option A — utiliser **44,6 h/pers** (valeur du repo, défendable comme fallback documenté).
- Option B — retrouver le dénominateur exact (probablement nb d'employés ayant eu ≥1 formation)
  et documenter la méthodologie avant la présentation.
- En tout état de cause, préciser le dénominateur en note de slide.

---

### 2.3 β = 4,46/5 — APPROXIMATIF (mais source ambiguë)

**Problème** : il existe **deux β** dans le repo ; le slide n'indique pas lequel.

```
beta_eae (évaluation annuelle EAE)  = 3,39/5   n = 3 477
beta_qr  (Quick Review post-formation) = 4,47/5  n = inconnu

Slide : 4,46 → proche de beta_qr (4,47), mais non identique.
```

**Risque** : confondre les deux mesure des phénomènes très différents.
`beta_eae` mesure la performance RH formelle ; `beta_qr` mesure la satisfaction formation.
Les présenter sous le même symbole β est trompeur.

**Recommandation** :
- Distinguer explicitement β_EAE = **3,39/5** et β_QR = **4,47/5** dans les slides.
- Si une seule valeur β est présentée, indiquer sa source (EAE vs Quick Review).
- Corriger 4,46 → **4,47** (Quick Review) si c'est bien cette source.

---

### 2.4 P = +0,07 pt — INCOHÉRENT

**Problème** : valeur introuvable, aucune méthodologie ne la produit.

```
P dans le repo = CAGR NBI/FTE 2022→2025 = (316,7/315,4)^(1/3) − 1 = +0,1372% ≈ 0,14%

Vérifications croisées :
  Delta absolu NBI/FTE 2022→2025  : +1,3 k€     ≠ 0,07
  CAGR annuel                     : +0,14%        ≠ 0,07
  Delta NBI/FTE 2024→2025         : +2,7 k€       ≠ 0,07
  kpi_P stocké (P_cagr × 100)    : 0,14           ≠ 0,07
```

**Note** : `kpi_P = 0.14` dans chaque BU est stocké en "CAGR %" mais résulte de
`P_cagr × 100 = 0,0014 × 100`. La valeur stockée **0,14 représente 0,14%, non 14%** —
risque de lecture erronée dans le dashboard.

**Recommandation** : retirer le chiffre +0,07 pt ou sourcer la méthodologie exacte.
Remplacer par **P = +0,14% CAGR (NBI/FTE 2022→2025)** avec note de bas de slide :
"Source : P&L/FTE interne 2022–2025."

---

### 2.5 ρ = 2,6% — INCOHÉRENT (erreur de nature)

**Problème** : confusion entre valeur cible et valeur constatée.

```
group_summary.rho_caceis_fr_2024  = 4,81%   ← moyenne groupe France, actuelle
Finance & Admin rho (constaté)    = 3,2%    (fa_rho = 0.032, hardcodé)
2,6%  dans generate-kpi.py        = "ρ: 3,2% → 2,6% by 2026"  ← OBJECTIF 2026 FA
```

La valeur **2,6% est l'objectif cible de Finance & Admin à l'horizon 2026**,
codée dans les recommandations. Elle n'est PAS la moyenne groupe actuelle.

**Risque** : présenter 2,6% comme valeur courante sous-estime le problème d'absentéisme
de près de **2,2 pp** vs réalité (4,81%). Un interlocuteur DRH le repèrera immédiatement.

**Recommandation** : remplacer par **ρ = 4,81% (France, 2024)**.
Si l'objectif FA est présenté, le libeller explicitement : "Objectif 2026 : 2,6%".

---

### 2.6 NBI/FTE ~315 k€ — APPROXIMATIF

**Problème** : valeur vraie mais année de référence non documentée.

```
nbi_fte_series :
  2022 : 315,4 k€/FTE   ← valeur la plus proche du "315" présenté
  2023 : 263,3 k€/FTE   (effet périmètre post-fusion apparent)
  2024 : 314,0 k€/FTE
  2025 : 316,7 k€/FTE   ← group_summary.nbi_per_fte_2025_keur

euro_bridge.py et CLAUDE.md hardcodent : 315,0 k€/tête
```

**Note** : la chute à 263,3 en 2023 mérite attention — elle reflète vraisemblablement
l'intégration de nouveaux effectifs (6 371 FTE vs 3 964 en 2022) post-acquisition.
Si un interlocuteur finance demande la série, la discontinuité 2022→2023 sera questionnée.

**Recommandation** :
- Utiliser **314,0 k€/FTE (2024)** ou **316,7 k€/FTE (2025)** selon l'année de référence.
- Documenter l'année dans la slide ("NBI/FTE 2024 : ~314 k€/tête").
- Expliquer la discontinuité 2023 en note (intégration / changement de périmètre).

---

### 2.7 Chiffres de volume — NON SOURCÉ (en majorité)

Les 8 chiffres de volume (436 000+ lignes, 12 711 collaborateurs, etc.) ne sont pas
reproductibles depuis `kpi-output.json` : ils proviennent des **fichiers Excel bruts**
(`Sujet Alberthon/`) qui sont exclus du repo (`.gitignore`).

**Incohérences internes détectées sans accès aux Excel** :

| Affirmation | Problème interne |
|---|---|
| 5 766 EAE, 3 477 valides, 88,8% | Mutuellement incohérents : 3 477/5 766 = 60,3% ≠ 88,8%. Pour que 88,8% soit exact, le total serait ~3 917, pas 5 766. |
| 14 943 formations, 13 446 exploitables | Repo dit 13 702 sessions (après filtre "annulé"). Ni 14 943 ni 13 446 ne correspondent. |

**Recommandation** : vérifier ces counts directement sur les Excel avant la présentation.
Le script `generate-kpi.py` imprime les counts à l'exécution — relancer sur les données
sources pour obtenir les valeurs à jour.

---

## 3. Top 3 — Chiffres les plus risqués à présenter

### 🔴 Risque n°1 — ρ = 2,6% (CRITIQUE)

**Pourquoi c'est le plus dangereux** : c'est une valeur cible 2026 présentée comme
valeur actuelle, avec un écart de **−2,2 pp** sur la réalité (4,81%).
Tout interlocuteur DRH ou finance chez CACEIS connaît le taux réel.
Si ce chiffre est challengé en réunion, il invalide la crédibilité de l'ensemble.

**Action immédiate** : corriger en 4,81% (groupe France 2024) avant toute diffusion.

---

### 🔴 Risque n°2 — λ = 68 h/pers (CRITIQUE)

**Pourquoi c'est risqué** : +52% d'écart vs valeur du repo (44,6 h).
La valeur 68 n'est traçable à aucun dénominateur documenté dans le repo.
Si challengée ("comment calculez-vous ce 68 ?"), impossible à défendre sans retrouver
le fichier ou le calcul source.

**Action immédiate** : soit documenter le dénominateur exact (employés formés ≈ 1 644),
soit utiliser 44,6 h avec note de bas de slide précisant la méthodologie.

---

### 🟠 Risque n°3 — Triple incohérence EAE (5 766 / 3 477 / 88,8%)

**Pourquoi c'est risqué** : les trois chiffres sont mutuellement contradictoires.
Un analyste financier calculera 3 477 / 5 766 = 60,3% en temps réel et signalera l'erreur.
La crédibilité du "volume de données" présenté en slide de cadrage sera remise en cause.

**Action immédiate** : vérifier sur le fichier EAE source quel est le compte total de lignes,
recalculer le taux réel, et harmoniser les trois valeurs avant la présentation.

---

## 4. Récapitulatif par statut

| Statut | Nombre | Affirmations |
|---|---|---|
| **VÉRIFIÉ** | 6 | 26 BUs · EAE valides 3 477 · 4 seuils d'alerte |
| **APPROXIMATIF** | 2 | β = 4,46 (→ 4,47 QR) · NBI/FTE ~315 (→ 314,0/316,7 selon année) |
| **NON SOURCÉ** | 8 | Lignes brutes 436k · 12 711 collab · 127 825 abs · 2 544 notes 2023 · 9 706 QR · 275 609 démo · P = +0,07 pt |
| **INCOHÉRENT** | 6 | Y=3,41 (→3,39) · λ=68 (→44,6 ou sourcer) · ρ=2,6% (→4,81%) · EAE triple incohérence · Formations 14 943/13 446 |

---

*Audit réalisé en lecture seule. Aucune donnée source ni calcul métier modifié.*
*Sources consultées : `rag/data/kpi-output.json` v1.1.0 · `interface/data/generate-kpi.py` · `docs/KPI_DEFINITIONS.md`*
