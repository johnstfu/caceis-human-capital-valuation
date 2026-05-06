"""
generator.py — Génère les recommandations RH via Claude.

Prend en entrée :
  - Les KPIs d'une BU
  - Le contexte récupéré (chunks pertinents)

Produit un scorecard JSON structuré avec recommandations citées.
"""

import os
import json
import logging
import re
import time

import anthropic
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

SYSTEM_PROMPT = """Tu es un conseiller RH expert senior pour CACEIS, société de gestion d'actifs de 6 600 collaborateurs (14 pays).
Tu analyses les KPIs de capital humain d'une Business Unit et proposes des recommandations actionnables.

SOURCES DE RECOMMANDATIONS (dans cet ordre de priorité) :
1. ACTIONS PRÉ-SÉLECTIONNÉES (section dédiée dans le message) — actions sourcées et vérifiées de la bibliothèque CACEIS. À intégrer en priorité.
2. CONTEXTE DOCUMENTAIRE — chunks sémantiques de la base ChromaDB. Complément si les actions pré-sélectionnées ne couvrent pas tous les gaps.

RÈGLES ABSOLUES :
- Cite TOUJOURS ta source entre crochets [Source: nom_fichier ou ACT_XXX] pour chaque affirmation factuelle
- Si une action pré-sélectionnée est marquée [À COMPLÉTER], signale-le dans la description
- Maximum 3 recommandations, chacune en 2-3 phrases concrètes
- Ton professionnel, concret, actionnable — niveau Direction RH
- JAMAIS de référence à des individus — uniquement des agrégats BU
- Si le contexte est insuffisant, indique-le explicitement dans confidence_reason

KPI P — RÈGLE SPÉCIALE :
Si le message contient "── KPI P ──", reproduis EXACTEMENT ce message dans les recommendations pour P :
"P est un indicateur de résultat. Les leviers directs sont Y (engagement), λ (formation) et β (QVCT)."
Ne propose PAS d'action directe sur P.

KPI ρ — RÈGLE SPÉCIALE :
Si le message contient "⚠ Note :" pour ρ, ajoute ce message en bas de la recommendation ρ.

INTERPRÉTATION DES KPIs (nomenclature V_HC) :
- Y  (Engagement /5)        : moyenne CACEIS = 3.40. Seuil gap : <3.40
- λ  (Formation h/emp/an)   : moyenne CACEIS = 44.6h. Seuil gap : <44.6h
- β  (QVCT /5)              : moyenne CACEIS = 3.40. Seuil gap : <3.40
- ρ  (Absentéisme %)        : moyenne CACEIS FR = 4.8%. Seuil gap : >4.8%
- P  (Productivité)         : indicateur de résultat — pas d'action directe
- V_HC (Indice composite 0→1)

FORMAT DE RÉPONSE OBLIGATOIRE — JSON pur, sans markdown, sans explication :
{
  "bu_name": "...",
  "v_hc_index": 0.0,
  "rank": "X/26",
  "summary": "Résumé en 1 phrase de la situation RH de la BU",
  "alert_kpis": ["Y", "rho"],
  "recommendations": [
    {
      "lever": "Titre court (5 mots max)",
      "description": "Description actionnable en 2-3 phrases. [Source: ACT_001 ou fichier.pdf]",
      "source": "ACT_001 ou nom_du_fichier_source.pdf",
      "priority": "haute|moyenne|faible",
      "kpi_impacted": "Y|λ|β|P|ρ",
      "estimated_impact": "Description de l'impact estimé (si sourcé)",
      "action_ids": ["ACT_001", "ACT_002"]
    }
  ],
  "confidence": "haute|moyenne|faible",
  "confidence_reason": "Explication du niveau de confiance"
}"""


class CACEISGenerator:

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY manquante dans .env")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model  = "claude-sonnet-4-6"

    def _build_kpi_summary(self, bu_name: str, kpi_data: dict) -> str:
        """Construit un résumé textuel des KPIs pour le prompt."""
        lines = [f"BU analysée : {bu_name}", ""]
        lines.append("KPIs 2024 :")

        kpi_labels = {
            "kpi_Y":        ("Y  — Engagement",         "/5",        3.40,  True),
            "kpi_lambda":   ("λ  — Formation",           "h/emp/an", 44.6,  True),
            "kpi_beta_qr":  ("β  — Qualité formation QR", "/5",        3.40,  True),
            "kpi_rho":      ("ρ  — Absentéisme",         "%",         0.048, False),
            "kpi_P":        ("P  — Productivité",        "",          None,  True),
            "v_hc_index":   ("V_HC — Indice composite", "/1",         0.4521, True),
        }

        for key, (label, unit, mean, higher_is_better) in kpi_labels.items():
            val = kpi_data.get(key)
            if val is None:
                continue
            # P n'a pas de seuil de comparaison
            if mean is None:
                lines.append(f"  {label}: {val}")
                continue
            # Détermine si la valeur est en dessous ou au-dessus de la moyenne
            if higher_is_better:
                status = "▲ au-dessus" if val >= mean else "▼ en dessous"
            else:
                status = "▼ en dessous (positif)" if val <= mean else "▲ au-dessus (alerte)"

            if unit == "%":
                lines.append(f"  {label}: {val*100:.2f}% [{status} de la moyenne {mean*100:.2f}%]")
            else:
                lines.append(f"  {label}: {val:.3f} {unit} [{status} de la moyenne {mean:.3f}]")

        rank = kpi_data.get("rank", "?")
        total = kpi_data.get("total_rank", 26)
        lines.append(f"\nClassement : {rank}/{total} BUs CACEIS (V_HC)")

        n_emp = kpi_data.get("n_employees")
        if n_emp:
            lines.append(f"Effectif : ~{n_emp} collaborateurs")

        return "\n".join(lines)

    def _extract_alert_kpis(self, kpi_data: dict) -> list:
        """Identifie les KPIs en alerte (seuils nomenclature V_HC)."""
        alerts = []
        if kpi_data.get("kpi_Y", 5) < 3.40:
            alerts.append("Y")
        if kpi_data.get("kpi_lambda", 100) < 44.6:
            alerts.append("λ")
        if kpi_data.get("kpi_rho", 0) > 0.048:
            alerts.append("ρ")
        if kpi_data.get("kpi_beta_qr", 5) < 3.40:
            alerts.append("β")
        return alerts

    def generate_scorecard(
        self,
        bu_name: str,
        kpi_data: dict,
        retrieved_context: str,
        actions_prompt: str = "",
    ) -> dict:
        """
        Génère le scorecard complet d'une BU.

        Args:
            bu_name           : nom de la BU (ex: "Finance & Admin")
            kpi_data          : dict des KPIs de la BU
            retrieved_context : contexte formaté des chunks ChromaDB
            actions_prompt    : actions pré-sélectionnées depuis action_library_raw.json

        Returns:
            dict scorecard structuré
        """
        kpi_summary = self._build_kpi_summary(bu_name, kpi_data)

        # Section actions structurées (prioritaire sur le contexte sémantique)
        actions_section = ""
        if actions_prompt:
            actions_section = f"""
---
{actions_prompt}
"""

        user_message = f"""Voici les KPIs de la Business Unit à analyser :

{kpi_summary}
{actions_section}
---
CONTEXTE DOCUMENTAIRE CACEIS (documents de référence, complément) :

{retrieved_context}

---
Génère le scorecard JSON complet pour cette BU, avec 2-3 recommandations actionnables.
Priorise les ACTIONS PRÉ-SÉLECTIONNÉES ci-dessus. Complète avec le contexte documentaire si nécessaire."""

        try:
            time.sleep(0.5)
            response = self.client.messages.create(
                model      = self.model,
                max_tokens = 1500,
                system     = SYSTEM_PROMPT,
                messages   = [{"role": "user", "content": user_message}],
            )
            raw_text = response.content[0].text.strip()

            # Extrait le JSON (Claude peut ajouter du texte autour)
            match_start = raw_text.find("{")
            match_end   = raw_text.rfind("}")
            if match_start == -1 or match_end == -1:
                raise ValueError("Pas de JSON trouvé dans la réponse")

            scorecard = json.loads(raw_text[match_start: match_end + 1])

            # Enrichit avec les données KPI brutes
            scorecard["kpi_raw"] = {
                "Y":      kpi_data.get("kpi_Y"),
                "lambda": kpi_data.get("kpi_lambda"),
                "beta":   kpi_data.get("kpi_beta_qr"),
                "rho":    kpi_data.get("kpi_rho"),
                "V_HC":   kpi_data.get("v_hc_index"),
            }
            scorecard["alert_kpis"] = scorecard.get(
                "alert_kpis", self._extract_alert_kpis(kpi_data)
            )

            return scorecard

        except json.JSONDecodeError as e:
            log.error(f"JSON parse error pour {bu_name}: {e}")
            return self._fallback_scorecard(bu_name, kpi_data, str(e))
        except Exception as e:
            log.error(f"Generation error pour {bu_name}: {e}")
            return self._fallback_scorecard(bu_name, kpi_data, str(e))

    def _fallback_scorecard(self, bu_name: str, kpi_data: dict, error: str) -> dict:
        """Scorecard minimal en cas d'erreur API."""
        return {
            "bu_name":       bu_name,
            "v_hc_index":   kpi_data.get("v_hc_index", 0),
            "rank":          f"{kpi_data.get('rank', '?')}/{kpi_data.get('total_rank', 26)}",
            "summary":       "Analyse indisponible — erreur de génération",
            "recommendations": [],
            "confidence":    "faible",
            "confidence_reason": f"Erreur API : {error}",
            "alert_kpis":    self._extract_alert_kpis(kpi_data),
            "kpi_raw":       {
                "Y":      kpi_data.get("kpi_Y"),
                "lambda": kpi_data.get("kpi_lambda"),
                "beta":   kpi_data.get("kpi_beta_qr"),
                "rho":    kpi_data.get("kpi_rho"),
                "V_HC":   kpi_data.get("v_hc_index"),
            },
        }
