"""
Diagnosis module.

Implements a DiagnosisEngine abstraction so that the rule-based engine
can be swapped for an LLM engine later without touching the orchestrator.

Public API:
  - POST /api/diagnosis   — accepts attack_id or raw parameters
  - diagnoses             — in-memory store used by other modules
  - diagnose_from_context() — called by the experiment orchestrator
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/diagnosis",
    tags=["Diagnosis"],
)

# In-memory store: diagnosis_id -> diagnosis dict
diagnoses: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Diagnosis engine interface
# ---------------------------------------------------------------------------

class DiagnosisContext:
    """All data available to the diagnosis engine for a given experiment."""

    def __init__(
        self,
        attack_type: str,
        target: str,
        attack_value: int,
        observed_latency_ms: float,
        attack_id: Optional[str] = None,
        architecture_id: Optional[str] = None,
        baseline_latency_ms: Optional[float] = None,
        observed_p95_ms: Optional[float] = None,
        baseline_p95_ms: Optional[float] = None,
    ):
        self.attack_type = attack_type
        self.target = target
        self.attack_value = attack_value
        self.observed_latency_ms = observed_latency_ms
        self.attack_id = attack_id
        self.architecture_id = architecture_id
        self.baseline_latency_ms = baseline_latency_ms
        self.observed_p95_ms = observed_p95_ms
        self.baseline_p95_ms = baseline_p95_ms


class DiagnosisEngine(ABC):
    """Abstract diagnosis engine.  Implement diagnose() for each strategy."""

    @abstractmethod
    def diagnose(self, context: DiagnosisContext) -> dict:
        """Return a diagnosis dict."""


def _latency_severity(
    attack_value_ms: int,
    observed_ms: float,
    baseline_ms: Optional[float],
    observed_p95_ms: Optional[float],
    baseline_p95_ms: Optional[float],
) -> tuple[str, dict]:
    """
    Determine severity and build evidence dict from the available signals.

    Priority order:
      1. P95 uplift (most reliable end-user signal when available)
      2. Average uplift vs baseline
      3. Absolute attack magnitude (fallback when no baseline)

    Rules:
      high   – P95 > 2× baseline P95, OR avg uplift > 3× baseline, OR
                attack ≥ 5000 ms with any measurable uplift
      medium – P95 > 1.3× baseline P95, OR avg uplift > 1.5× baseline, OR
                attack ≥ 2000 ms with any measurable uplift
      low    – everything else (uplift present but minor, or no baseline data)
    """
    evidence: dict = {
        "attack_latency_ms": attack_value_ms,
        "observed_latency_ms": round(observed_ms, 1),
    }

    if baseline_ms is not None and baseline_ms > 0:
        evidence["baseline_latency_ms"] = round(baseline_ms, 1)
        avg_uplift_ratio = observed_ms / baseline_ms
        evidence["avg_uplift_ratio"] = round(avg_uplift_ratio, 2)
    else:
        avg_uplift_ratio = None

    if observed_p95_ms is not None:
        evidence["observed_p95_ms"] = round(observed_p95_ms, 1)
    if baseline_p95_ms is not None and baseline_p95_ms > 0:
        evidence["baseline_p95_ms"] = round(baseline_p95_ms, 1)
        p95_uplift_ratio = observed_p95_ms / baseline_p95_ms if observed_p95_ms else None
        if p95_uplift_ratio is not None:
            evidence["p95_uplift_ratio"] = round(p95_uplift_ratio, 2)
    else:
        p95_uplift_ratio = None

    # --- severity decision ---
    # Rule 1: P95 uplift (most reliable)
    if p95_uplift_ratio is not None:
        if p95_uplift_ratio > 2.0 or attack_value_ms >= 5000:
            severity = "high"
        elif p95_uplift_ratio > 1.3 or attack_value_ms >= 2000:
            severity = "medium"
        else:
            severity = "low"
    # Rule 2: average uplift vs baseline
    elif avg_uplift_ratio is not None:
        if avg_uplift_ratio > 3.0 or attack_value_ms >= 5000:
            severity = "high"
        elif avg_uplift_ratio > 1.5 or attack_value_ms >= 2000:
            severity = "medium"
        else:
            severity = "low"
    # Rule 3: no baseline at all — use absolute attack magnitude
    else:
        if attack_value_ms >= 5000:
            severity = "high"
        elif attack_value_ms >= 2000:
            severity = "medium"
        else:
            severity = "low"

    return severity, evidence


class RuleBasedDiagnosisEngine(DiagnosisEngine):
    """Deterministic rule-based diagnosis.  No external dependencies."""

    def diagnose(self, context: DiagnosisContext) -> dict:
        if context.attack_type != "latency":
            return {
                "problem": f"Unsupported attack type: {context.attack_type}",
                "severity": "unknown",
                "evidence": {},
                "recommendation": "No rule-based recommendation available.",
            }

        severity, evidence = _latency_severity(
            attack_value_ms=context.attack_value,
            observed_ms=context.observed_latency_ms,
            baseline_ms=context.baseline_latency_ms,
            observed_p95_ms=context.observed_p95_ms,
            baseline_p95_ms=context.baseline_p95_ms,
        )

        return {
            "problem": (
                f"{context.target.capitalize()} service latency ({context.attack_value} ms) "
                "is propagating through the request path and significantly "
                "increasing end-to-end latency."
            ),
            "severity": severity,
            "evidence": evidence,
            "recommendation": (
                "Introduce a timeout, circuit breaker, and/or asynchronous "
                "processing around the downstream dependency."
            ),
            "affected_services": [context.target, "order", "gateway"],
            "root_cause": (
                f"Synchronous call chain from gateway → order → {context.target}. "
                "A slow payment response blocks the entire upstream chain."
            ),
        }


# Default engine used by the application.
_engine: DiagnosisEngine = RuleBasedDiagnosisEngine()


def set_engine(engine: DiagnosisEngine) -> None:
    """Replace the active diagnosis engine (e.g., swap in an LLM engine)."""
    global _engine
    _engine = engine


def diagnose_from_context(context: DiagnosisContext) -> dict:
    """Run diagnosis and persist the result.  Returns the full diagnosis record."""
    result = _engine.diagnose(context)
    diagnosis_id = f"diag_{uuid4().hex[:8]}"
    record = {
        "diagnosis_id": diagnosis_id,
        "attack_id": context.attack_id,
        "attack_type": context.attack_type,
        "target": context.target,
        **result,
    }
    diagnoses[diagnosis_id] = record
    return record


# ---------------------------------------------------------------------------
# API endpoint
# ---------------------------------------------------------------------------

class DiagnosisRequest(BaseModel):
    # New style: reference an existing attack by ID
    attack_id: Optional[str] = None
    # Legacy / manual style: supply parameters directly
    attack_type: Optional[str] = None
    target: Optional[str] = None
    attack_value: Optional[int] = None
    average_latency_ms: Optional[float] = None


@router.post("")
async def diagnose(request: DiagnosisRequest):
    # --- resolve via attack_id ---
    if request.attack_id:
        from app.attacks import attacks  # local import to avoid circular

        attack = attacks.get(request.attack_id)
        if attack is None:
            raise HTTPException(
                status_code=404,
                detail=f"Attack not found: {request.attack_id}",
            )

        # Prefer metrics stored on the attack record; fall back to querying now.
        attack_metrics = attack.get("metrics") or {}
        latency_ms = (
            attack_metrics.get("average_latency_ms")
            or attack_metrics.get("observed_latency_ms")
            or 0.0
        )

        context = DiagnosisContext(
            attack_type=attack["type"],
            target=attack["target"],
            attack_value=int(attack["value"]),
            observed_latency_ms=float(latency_ms),
            attack_id=request.attack_id,
            architecture_id=attack.get("architecture_id"),
        )
        return diagnose_from_context(context)

    # --- legacy manual style ---
    if not all(
        [request.attack_type, request.target, request.attack_value is not None, request.average_latency_ms is not None]
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "Provide either 'attack_id' (preferred) or all of: "
                "attack_type, target, attack_value, average_latency_ms"
            ),
        )

    context = DiagnosisContext(
        attack_type=request.attack_type,
        target=request.target,
        attack_value=request.attack_value,
        observed_latency_ms=request.average_latency_ms,
    )
    return diagnose_from_context(context)
