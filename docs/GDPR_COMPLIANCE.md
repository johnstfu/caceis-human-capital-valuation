# GDPR Compliance Notes

---

## Approach

All computations produce **Business Unit-level aggregates only**. No individual employee data is stored, displayed, or transmitted at any stage of the pipeline.

The minimum BU size threshold is **5 employees**. Any BU below this threshold has its KPIs suppressed to prevent re-identification.

Source HR files (`Sujet Alberthon/`) remain **on-premise** at all times. They are read locally by the Notebook/ingest pipeline and are never uploaded, cached, or forwarded to external services.

---

## Data Flow and Privacy Boundaries

| Stage | Data in transit | External? |
|-------|----------------|-----------|
| Notebook KPI computation | Raw Excel → aggregated JSON | No — local only |
| ChromaDB indexing | PDF/DOCX text chunks | No — local only |
| Scorecard generation (Anthropic) | BU-level KPIs + text chunks from governance docs | Yes — aggregated only |
| Dashboard display | kpi-output.json (aggregated) | No — served locally |

The only data that reaches Anthropic's API is:
1. Aggregated KPI scores per BU (no names, no individual data)
2. Text excerpts from official CACEIS governance documents (already public-facing or internally published)

---

## What Is Not Stored

- Individual employee names, IDs, or email addresses
- Individual evaluation scores or absence records
- Any field that could identify a specific person

---

## Legal Basis

The HR data used in this project was provided under CACEIS's internal data governance framework for the purpose of this research project. The output (V_HC index, recommendations) is intended for HR management use only.

---

For questions about data handling, contact the CACEIS Data Privacy Officer.
