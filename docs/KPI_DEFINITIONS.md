# KPI Definitions — V_HC Index

> Detailed methodology for each of the five KPIs and the composite V_HC formula.

---

## V_HC Composite Formula

```
V_HC = 0.35·norm(Y) + 0.20·norm(λ) + 0.25·norm(β) + 0.10·norm(P) − 0.10·norm(ρ)
```

All KPIs are min-max normalised across the 26 CACEIS Business Units before weighting.
ρ (absenteeism) enters with a negative sign — a higher rate reduces the score.

---

## KPI Definitions

### Y — Engagement (/5)

| Field | Value |
|-------|-------|
| Source | IMR (Internal Morale Report) surveys 2021–2024 |
| Scale | 1–5 (5 = fully engaged) |
| Aggregation | Simple mean per BU, all respondents |
| CACEIS average | 3.40 |
| Gap threshold | < 3.40 triggers alert |
| Weight in V_HC | 35% |

---

### λ — Training Volume (hours/employee/year)

| Field | Value |
|-------|-------|
| Source | Training Records (Cold Review + Quick Review) |
| Unit | Hours per employee per year |
| CACEIS average | 44.6 h/emp/yr |
| Gap threshold | < 44.6 h triggers alert |
| Weight in V_HC | 20% |

---

### β — Training Quality (/5)

| Field | Value |
|-------|-------|
| Source | EAE (Entretien Annuel d'Évaluation) + Quick Review ratings |
| Scale | 1–5 (5 = excellent) |
| Aggregation | Weighted average, confidence interval reported |
| CACEIS average | 3.40 |
| Gap threshold | < 3.40 triggers alert |
| Weight in V_HC | 25% |

---

### P — Productivity (Δ% NBI/FTE)

| Field | Value |
|-------|-------|
| Source | NBI/FTE financial series 2022–2025 |
| Unit | Year-over-year % change in Net Banking Income per FTE |
| Notes | **Result indicator** — no direct HR lever; driven by Y, λ, β |
| Weight in V_HC | 10% |

> P is a lagging indicator. The recommended approach is to improve Y, λ, and β — P follows.

---

### ρ — Absenteeism Rate (%)

| Field | Value |
|-------|-------|
| Source | Absenteeism detail (Bilan Social) 2024–2025 |
| Scope | France only |
| Unit | % of working days lost |
| CACEIS average | 4.8% (France) |
| Gap threshold | > 4.8% triggers alert |
| Weight in V_HC | −10% (penalty) |

---

## Confidence Levels

Each KPI carries a `confidence` field in `kpi-output.json`:

| Level | Meaning |
|-------|---------|
| `haute` | Large sample (>100 observations), verified source |
| `moyenne` | Moderate sample or single-year data |
| `faible` | Small BU (<20 employees) or proxy calculation |

---

## Rank and Percentile

BUs are ranked 1–26 by V_HC score (1 = highest). The rank is included in
`kpi-output.json` as `rank` and `total_rank` fields.
