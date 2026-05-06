# Slides 07–09 : Pipeline RAG & Recommandations

## Slide 07 — Architecture RAG
ChromaDB (14 docs, ~1 200 chunks) · sentence-transformers · ActionStore (26 actions sourcées).
Retrieval top-7 · Anthropic Claude Sonnet · JSON structuré avec sources citées.

## Slide 08 — Exemple de scorecard (Finance & Admin)
3 recommandations générées. Sources : IMR 2024, FABLife Bilan 2024, Accord QVT 2024.
Confiance haute. Alert KPIs : ρ (5.2% > 4.8%), λ (38h < 44.6h).

## Slide 09 — Pourquoi RAG > Fine-tuning
Citabilité des sources · Mise à jour documentaire sans ré-entraînement · Auditabilité.
ActionStore déterministe = recommandations toujours ancrées dans les politiques CACEIS réelles.
