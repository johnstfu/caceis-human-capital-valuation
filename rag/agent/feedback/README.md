# rag/agent/feedback — Couche d'auto-apprentissage

## Périmètre strict

> **Ce module ne lit et n'écrit QUE des signaux d'usage agrégés.**
> Il n'accède JAMAIS à `rag/data/`, ne modifie JAMAIS `kpi-output.json`,
> et ne stocke JAMAIS de données nominatives, de scores individuels,
> ni de profils par employé.

## Ce que ce module apprend

| Signal | Mécanisme | Fichier |
|--------|-----------|---------|
| KPI creusés par l'utilisateur | Incrémente le poids du KPI dans `feedback_store.json` | `signal_logger.py` + `ranking_updater.py` |
| Questions retenues vs ignorées | Ajuste le poids de la question dans `feedback_store.json` | `signal_logger.py` + `ranking_updater.py` |
| Actions validées / rejetées | Met à jour le score de l'action dans `feedback_store.json` | `signal_logger.py` + `ranking_updater.py` |

## Ce que ce module n'apprend PAS (interdits absolus)

| Interdit | Raison |
|----------|--------|
| Profil par employé | RGPD / IRP — hors périmètre légal |
| Score individuel ajusté à l'usage | Contourne l'agrégation BU — interdit contractuellement |
| Modification de kpi-output.json | Source de vérité en lecture seule pour l'agent |
| Entrée dans ActionStore sans gate humaine | Voir suggestion_queue.py — validation RH/Gouvernance requise |

## Bouton feedback (suggestion_queue)

`suggestion_queue.py` implémente le bouton "Julien aurait voulu dire" :

1. Julien décrit une recommandation absente de la bibliothèque
2. Elle est écrite dans `suggestion_queue.json` avec statut `pending`
3. Elle génère un signal de ranking immédiat (affichage prioritaire)
4. **Elle n'entre dans `action_library_raw.json` QUE si un humain (RH + Gouvernance) valide**
5. L'agent ne la ressort jamais comme action officielle tant que statut ≠ `validated`

## Persistance

```
feedback/store/
├── feedback_store.json    Poids appris (KPI, questions, actions)
└── suggestion_queue.json  Suggestions Julien en attente de gate
```

Ces deux fichiers sont **gitignorés** — ils ne voyagent pas dans le repo.
