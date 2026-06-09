"""
cfo_persona.py — Construit le system prompt adapté au CFAO CACEIS.

Injecte : ton financier, vocabulaire interne CACEIS, ancrage NBI/FTE,
contrainte de non-empiétement sur le CHRO, règles RGPD de l'agent.
"""

from typing import Optional


# Ratio NBI/FTE de référence (source : kpi-output.json, série 2022-2025)
NBI_FTE_REFERENCE_KEU = 315  # k€/tête


# Vocabulaire interne CACEIS à respecter impérativement
VOCABULARY_RULES = """
- Finance & Admin = SPF (fonction support) — ne jamais appeler "BU"
- Absentéisme : scope France uniquement — ne pas extrapoler aux autres pays
- P (productivité) est un indicateur de résultat — les leviers sont Y, λ, β
- KPI board-level : Y (engagement), P (productivité), ρ (absentéisme)
- KPI opérationnels : λ (volume formation), β (qualité formation)
"""


def build_system_prompt(
    bu_name: Optional[str] = None,
    personalization_on: bool = True,
) -> str:
    """
    Construit le system prompt complet pour Julien en mode CFAO.

    Args:
        bu_name           : nom de la BU en cours d'analyse (optionnel)
        personalization_on: si False, supprime les instructions de push et de relance

    Returns:
        str — system prompt prêt pour client.messages.create(system=...)

    # TODO: assembler les sections ci-dessous dans l'ordre :
    #   1. Rôle et positionnement (CFAO, arbitrage budgétaire)
    #   2. Ce que Julien NE fait PAS (empiéter sur CHRO, données individuelles)
    #   3. Ancrage financier (NBI_FTE_REFERENCE_KEU)
    #   4. VOCABULARY_RULES
    #   5. Gate ActionStore (reproduire la règle : aucune action libre)
    #   6. Si personalization_on=True : instructions de push et de relance
    #   7. Contrainte RGPD (agrégation BU uniquement, jamais de nominatif)
    #   8. Format de réponse attendu (structure JSON ou texte selon usage)
    """
    raise NotImplementedError


def get_refusal_instruction() -> str:
    """
    Retourne la clause de refus pour toute question qui empiéterait
    sur le périmètre CHRO ou demanderait des données individuelles.

    Returns:
        str — instruction à injecter dans le system prompt

    # TODO: rédiger la clause explicite de refus :
    #   - "Tu ne fournis jamais de données sur un individu nommé"
    #   - "Tu ne te prononces pas sur les décisions de recrutement / licenciement"
    #   - "Tu ne remplaceras jamais l'avis du CHRO sur les sujets RH stratégiques"
    """
    raise NotImplementedError


def get_financial_bridge_instruction(nbi_fte_keu: int = NBI_FTE_REFERENCE_KEU) -> str:
    """
    Retourne l'instruction d'ancrage financier à injecter dans le prompt.

    Args:
        nbi_fte_keu : ratio NBI/FTE en k€ (paramétrable pour mise à jour annuelle)

    Returns:
        str — instruction forçant le pont score humain → euros

    # TODO: formater l'instruction avec nbi_fte_keu
    # TODO: inclure exemple concret : "+0.01 V_HC × N FTE × nbi_fte_keu k€ = €X potentiel"
    """
    raise NotImplementedError
