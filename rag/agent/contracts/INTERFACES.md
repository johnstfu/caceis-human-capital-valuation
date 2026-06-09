# INTERFACES.md — Contrats d'I/O entre sous-modules de rag/agent/

> Référence pour l'implémentation. Toute modification des signatures dans `schemas.py`
> doit être répercutée ici. Les exemples de valeurs sont indicatifs.

---

## 1. orchestrator.py ↔ context/cfo_persona.py

**Appel :** `build_system_prompt(bu_name, personalization_on)`

| Direction | Type | Description |
|-----------|------|-------------|
| → IN | `str \| None` | Nom BU en cours d'analyse |
| → IN | `bool` | Mode personnalisation actif |
| ← OUT | `str` | System prompt complet pour Claude |

**Contrat :** le prompt retourné contient toujours la clause de refus CHRO,
la contrainte RGPD, et la règle ActionStore. Si `personalization_on=False`,
les instructions de push et de relance sont absentes.

---

## 2. orchestrator.py ↔ context/bu_context.py

**Appel :** `BUContext.get_bu_by_id(bu_id)` ou `get_bu_by_name(name)`

| Direction | Type | Description |
|-----------|------|-------------|
| → IN | `str` | ID BU (`"spf__fin_treasury__admin"`) ou nom partiel |
| ← OUT | `dict \| None` | Dict KPI complet de la BU (copie immuable) |

**Contrat :** retourne toujours une copie, jamais la référence mutable.
`None` si BU non trouvée — l'orchestrateur gère le cas gracieusement.

---

## 3. orchestrator.py ↔ kpi_push/prioritizer.py

**Appel :** `KPIPrioritizer.prioritize(bu_data, conversation_history, max_push)`

| Direction | Type | Description |
|-----------|------|-------------|
| → IN | `dict` | Dict KPI de la BU |
| → IN | `list[ConversationTurn]` | Historique de conversation |
| → IN | `int` | Nombre max de KPI à retourner (défaut 3) |
| ← OUT | `list[KpiPush]` | KPIs ordonnés par priorité décroissante |

**Contrat :** retourne au minimum 0, au maximum `max_push` éléments.
Si `personalization_on=OFF`, l'orchestrateur n'appelle pas prioritize.

---

## 4. orchestrator.py ↔ questions/question_selector.py

**Appel :** `QuestionSelector.select(kpi_gaps, conversation_history, context_triggers, max_questions)`

| Direction | Type | Description |
|-----------|------|-------------|
| → IN | `list[str]` | KPIs en gap (ex: `["Y", "rho"]`) |
| → IN | `list[ConversationTurn]` | Historique |
| → IN | `list[str] \| None` | Triggers additionnels (`["arbitrage"]`) |
| → IN | `int` | Nombre max de questions (défaut 2) |
| ← OUT | `list[PushedQuestion]` | Questions sélectionnées |

**Contrat :** jamais la même question dans deux tours consécutifs.
Si `personalization_on=OFF`, l'orchestrateur n'appelle pas select.

---

## 5. orchestrator.py ↔ store/action_store.py (existant)

**Appel :** `ActionStore.get_all_actions_for_gaps(kpi_data)` — API inchangée.

| Direction | Type | Description |
|-----------|------|-------------|
| → IN | `dict` | Dict KPI de la BU |
| ← OUT | `dict` | Gaps + actions + career_dev + gap_notes |

**Contrat :** l'orchestrateur passe ce résultat à `format_for_prompt()`
avant injection dans le user_message. **AUCUNE action ne contourne cette gate.**

---

## 6. orchestrator.py ↔ arbitrage/budget_advisor.py

**Appel :** `BudgetAdvisor.propose_arbitrage(target_budget_keu, focus_kpis, top_n_bus)`

| Direction | Type | Description |
|-----------|------|-------------|
| → IN | `float \| None` | Enveloppe budgétaire (k€, optionnel) |
| → IN | `list[str] \| None` | KPIs focus (défaut: `["Y", "P", "rho"]`) |
| → IN | `int` | Nombre de BUs dans la comparaison (défaut 3) |
| ← OUT | `ArbitrageProposal` | Proposition structurée avec impact € |

---

## 7. arbitrage/budget_advisor.py ↔ arbitrage/euro_bridge.py

**Appel :** `EuroBridge.estimate_impact(delta_vhc, n_employees)`

| Direction | Type | Description |
|-----------|------|-------------|
| → IN | `float` | Delta V_HC visé (ex: `0.05`) |
| → IN | `int` | Effectif de la BU |
| ← OUT | `ImpactEstimate` | Bornes low/mid/high en k€ + hypothèses |

**Contrat :** toujours retourner les 3 bornes. Jamais présenter comme "projection" —
libellé obligatoire : "ordre de grandeur".

---

## 8. feedback/signal_logger.py ↔ feedback/ranking_updater.py

**Appel :** `SignalLogger.get_counts()` → `RankingUpdater.compute_updated_weights()`

| Direction | Type | Description |
|-----------|------|-------------|
| → IN | — | (pas d'argument — SignalLogger injecté à l'init) |
| ← OUT | `dict` | `{kpi_weights, question_weights, action_weights}` |

**Contrat :** `ranking_updater` lit les compteurs, ne modifie pas le SignalLogger.
Les poids restent dans `[MIN_WEIGHT, MAX_WEIGHT]` — clampés.

---

## 9. feedback/ranking_updater.py → kpi_push/prioritizer.py + questions/question_selector.py

**Appel :** `push_weights_to_modules(kpi_prioritizer, question_selector)`

| Destination | Méthode appelée | Type des poids |
|------------|-----------------|----------------|
| `KPIPrioritizer` | `update_weights(dict)` | `{kpi: float}` |
| `QuestionSelector` | `update_weights(dict)` | `{question_id: float}` |

**Contrat :** appelé en fin de session uniquement (pas en temps réel).
Les modules récepteurs valident les clés avant application.

---

## 10. feedback/suggestion_queue.py → (gate humaine) → action_library_raw.json

**Ce flux n'est PAS automatisé.** C'est une opération manuelle :

```
suggestion_queue.get_pending_suggestions()
    → revue humaine (RH + Gouvernance)
    → suggestion_queue.validate_suggestion(id)  ou  .reject_suggestion(id)
    → si validée : ajout manuel dans action_library_raw.json par un humain
```

**L'agent ne peut pas déclencher ce flux. Aucun code ne doit l'automatiser sans décision explicite.**
