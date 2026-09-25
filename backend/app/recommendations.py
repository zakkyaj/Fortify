"""
Recommendation engine.

Deterministic rule-based recommendations for MVP.
Designed to be swappable with an LLM engine later.
"""
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/recommendations",
    tags=["Recommendations"],
)

# In-memory store: recommendation_id -> recommendation dict
recommendations: dict[str, dict] = {}


class RecommendationRequest(BaseModel):
    diagnosis_id: str


# ---------------------------------------------------------------------------
# Rule-based recommendation engine
# ---------------------------------------------------------------------------

_LATENCY_RULES = [
    {
        "title": "Introduce a timeout",
        "strategy": "timeout",
        "reason": (
            "Prevents a slow downstream service from blocking callers "
            "indefinitely. Set the timeout slightly above the expected "
            "P99 latency under normal conditions."
        ),
    },
    {
        "title": "Add a circuit breaker",
        "strategy": "circuit-breaker",
        "reason": (
            "Automatically stops requests to an unhealthy downstream service "
            "and allows the system to fail fast rather than accumulating "
            "latency under sustained degradation."
        ),
    },
    {
        "title": "Use asynchronous payment processing",
        "strategy": "async-processing",
        "reason": (
            "Decouples order acceptance from payment completion. "
            "Orders can be acknowledged immediately; payment is processed "
            "in the background and the customer is notified on completion."
        ),
    },
    {
        "title": "Add a retry with exponential back-off",
        "strategy": "retry",
        "reason": (
            "Transient latency spikes may resolve quickly. "
            "A bounded retry with back-off improves success rate without "
            "overloading the already-degraded service."
        ),
    },
]


def generate_recommendations(
    attack_type: str,
    target: str,
    severity: str,
    attack_value: Optional[int] = None,
    observed_latency_ms: Optional[float] = None,
) -> list[dict]:
    """
    Return a list of recommendation dicts based on the attack type.

    This function is intentionally stateless so that an LLM engine can
    replace it by implementing the same signature.
    """
    if attack_type == "latency":
        # For severe latency we recommend all four; medium → first three;
        # low → first two.
        if severity == "high":
            rules = _LATENCY_RULES
        elif severity == "medium":
            rules = _LATENCY_RULES[:3]
        else:
            rules = _LATENCY_RULES[:2]

        return [
            {
                "title": r["title"],
                "strategy": r["strategy"],
                "reason": r["reason"],
            }
            for r in rules
        ]

    return [
        {
            "title": "Review system architecture",
            "strategy": "general",
            "reason": (
                f"A '{attack_type}' failure was detected on '{target}'. "
                "Review the service dependency chain for resilience gaps."
            ),
        }
    ]


@router.post("")
async def create_recommendation(request: RecommendationRequest):
    """
    Generate a recommendation from a diagnosis ID.

    The diagnosis must have been stored by the diagnosis endpoint or by
    the experiment orchestrator.
    """
    from app.diagnosis import diagnoses  # local import to avoid circular

    diag = diagnoses.get(request.diagnosis_id)
    if diag is None:
        raise HTTPException(
            status_code=404,
            detail=f"Diagnosis not found: {request.diagnosis_id}",
        )

    recs = generate_recommendations(
        attack_type=diag.get("attack_type", "latency"),
        target=diag.get("target", "unknown"),
        severity=diag.get("severity", "medium"),
        attack_value=diag.get("evidence", {}).get("attack_latency_ms"),
        observed_latency_ms=diag.get("evidence", {}).get("observed_latency_ms"),
    )

    recommendation_id = f"rec_{uuid4().hex[:8]}"
    record = {
        "recommendation_id": recommendation_id,
        "diagnosis_id": request.diagnosis_id,
        "attack_type": diag.get("attack_type"),
        "target": diag.get("target"),
        "recommendations": recs,
        "expected_effect": {
            "latency": "lower",
            "resilience": "higher",
            "coupling": "lower",
        },
    }

    recommendations[recommendation_id] = record
    return record
