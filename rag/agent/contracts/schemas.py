"""
schemas.py — Dataclasses / Pydantic : tous les types d'échange entre sous-modules.

Source unique de vérité pour les interfaces. Toute modification ici
doit être répercutée dans contracts/INTERFACES.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Literal


# ── Enums ─────────────────────────────────────────────────────────────────────

class PersonalizationMode(str, Enum):
    """
    Toggle global du mode de personnalisation de Julien.

    ON  : push recommandations + apprentissage de session actif
    OFF : réponses neutres, pas de push, pas d'apprentissage
    """
    ON  = "on"
    OFF = "off"


class SuggestionStatus(str, Enum):
    """Statut d'une suggestion dans la file d'attente."""
    PENDING   = "pending"    # En attente de validation humaine
    VALIDATED = "validated"  # Approuvée par RH + Gouvernance
    REJECTED  = "rejected"   # Rejetée


# ── KPI Push ──────────────────────────────────────────────────────────────────

@dataclass
class KpiPush:
    """
    Un KPI à pousser proactivement au CFAO dans la réponse.

    Attributes:
        kpi         : identifiant KPI ("Y", "lambda", "beta", "rho", "P")
        value       : valeur courante pour la BU
        group_mean  : moyenne groupe de référence
        gap         : écart à la moyenne (positif = au-dessus)
        alert_level : "critical" | "warning" | "ok"
        euro_impact : estimation d'impact financier en k€ (optionnel)
        board_level : True si KPI prioritaire pour le CFAO
    """
    kpi: str
    value: float
    group_mean: float
    gap: float
    alert_level: Literal["critical", "warning", "ok"]
    board_level: bool
    euro_impact: Optional[str] = None  # ex: "280–650 k€"


# ── Questions de relance ──────────────────────────────────────────────────────

@dataclass
class PushedQuestion:
    """
    Une question de relance sélectionnée pour ce tour de conversation.

    Attributes:
        question_id : ID dans QUESTION_POOL (ex: "Q_Y_01")
        text        : texte de la question
        kpi_target  : KPI concerné
        trigger     : contexte déclencheur
    """
    question_id: str
    text: str
    kpi_target: str
    trigger: str


# ── Tour de conversation ──────────────────────────────────────────────────────

@dataclass
class ConversationTurn:
    """
    Un tour complet de la conversation CFAO ↔ Julien.

    Attributes:
        user_message      : message brut du CFAO
        agent_response    : réponse texte de Julien
        bu_id             : BU du contexte (optionnel)
        kpi_pushes        : KPIs mis en avant dans ce tour
        pushed_questions  : questions de relance poussées
        arbitrage         : proposition d'arbitrage si applicable
        mode              : PersonalizationMode actif lors de ce tour
        timestamp         : horodatage du tour
    """
    user_message: str
    agent_response: str
    bu_id: Optional[str] = None
    kpi_pushes: list[KpiPush] = field(default_factory=list)
    pushed_questions: list[PushedQuestion] = field(default_factory=list)
    arbitrage: Optional["ArbitrageProposal"] = None
    mode: PersonalizationMode = PersonalizationMode.ON
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ── Arbitrage budgétaire ──────────────────────────────────────────────────────

@dataclass
class ArbitrageProposal:
    """
    Proposition d'arbitrage budgétaire inter-BUs.

    Attributes:
        recommended_bus   : BUs recommandées pour renforcement (par rang de priorité)
        deprioritized_bus : BUs où réduire l'investissement (optionnel)
        rationale         : justification en 2-3 phrases (KPI + euros)
        action_ids        : IDs ActionStore supportant la recommandation
        total_impact_keu  : impact total estimé (borne médiane, k€)
        impact_range_keu  : (low, high) bornes de l'impact
        assumptions       : hypothèses de calcul (NBI/FTE, sensibilité)
        budget_constraint : enveloppe disponible si fournie (k€)
    """
    recommended_bus: list[str]
    rationale: str
    action_ids: list[str]
    total_impact_keu: float
    impact_range_keu: tuple[float, float]
    assumptions: str
    deprioritized_bus: list[str] = field(default_factory=list)
    budget_constraint: Optional[float] = None


# ── Feedback & Suggestions ────────────────────────────────────────────────────

@dataclass
class FeedbackSignal:
    """
    Signal d'usage anonyme journalisé par SignalLogger.

    PÉRIMÈTRE STRICT : identifiants (KPI keys, question IDs, action IDs) et compteurs.
    JAMAIS de données nominatives, jamais de contenu libre utilisateur.

    Attributes:
        signal_type  : type de signal (voir SignalType dans signal_logger.py)
        target_id    : identifiant de l'élément (ex: "Y", "Q_Y_01", "ACT_001")
        context_bu   : ID BU agrégé du contexte (jamais nominatif)
        timestamp    : horodatage
    """
    signal_type: str
    target_id: str
    context_bu: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserSuggestion:
    """
    Suggestion de recommandation écrite par Julien, en attente de gate humaine.

    RÈGLE ABSOLUE : statut "pending" → jamais présentée comme action officielle.
    Entrée dans ActionStore uniquement si statut == "validated" + décision humaine.

    Attributes:
        suggestion_id : ID unique généré (ex: "SUG_001")
        text          : description de la reco suggérée (action RH générique)
        kpi_target    : KPI concerné
        context_bu_id : BU du contexte (ID agrégé — jamais nominatif)
        status        : SuggestionStatus
        created_at    : date de création
        validated_at  : date de validation (None si pending/rejected)
        rejected_at   : date de rejet (None si pending/validated)
    """
    suggestion_id: str
    text: str
    kpi_target: str
    status: SuggestionStatus = SuggestionStatus.PENDING
    context_bu_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    validated_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
