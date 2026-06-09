"""
rag.agent.feedback — Couche d'auto-apprentissage ISOLÉE.

PÉRIMÈTRE STRICT : ce module ne lit et n'écrit QUE des signaux d'usage agrégés
(KPI creusés, questions retenues, actions validées/rejetées).
Il n'accède JAMAIS à rag/data/, ne modifie JAMAIS kpi-output.json,
et ne stocke JAMAIS de données nominatives ou de scores individuels.
"""
