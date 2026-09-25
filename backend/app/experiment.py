"""
Experiment orchestration.

POST /api/experiment/run
POST /api/retest
GET  /api/comparisons/{attack_id}

Lifecycle per experiment run:
  1. Validate architecture
  2. Collect baseline metrics  (clean traffic, no toxic)
  3. Inject attack
  4. Generate traffic under attack
  5. Collect attack metrics
  6. Remove attack (cleanup)
  7. Diagnose  (uses baseline + attack metrics for accurate severity)
  8. Generate recommendations
  9. Store result

Retest workflow:
  - Accepts an optional ResilienceConfig (timeout_ms / circuit_breaker_threshold_ms)
  - When a resilience config is supplied, the effective latency seen by the
    system is capped to simulate a timeout or circuit breaker.
    simulation_mode = true is returned to make the limitation explicit.
  - Without a resilience config the same attack is replayed unchanged.
    simulation_mode = false.

Comparison:
  - "before" = baseline metrics from the ORIGINAL experiment
  - "after"  = attack metrics from the RETEST experiment
  - improvement = delta between those two windows
"""
import asyncio
import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.architecture import architectures
from app.attacks import attacks, _now, _set_status
from app.diagnosis import DiagnosisContext, diagnose_from_context
from app.recommendations import generate_recommendations
from app.telemetry import collect_gateway_metrics
from app.toxiproxy import add_latency, remove_latency, toxic_exists
from app.traffic import generate_traffic

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Experiment"],
)

# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

experiments: dict[str, dict] = {}     # experiment_id -> result
comparisons: dict[str, dict] = {}     # original_attack_id -> comparison


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class AttackConfig(BaseModel):
    target: str
    type: str
    value: int


class TrafficConfig(BaseModel):
    rate: int = 5
    duration_seconds: int = 10


class ResilienceConfig(BaseModel):
    """
    Optional resilience improvement to simulate during a retest.

    At most ONE of these should be set.  The one that is set determines
    how the effective attack latency is capped.

    timeout_ms:
        Simulate a timeout at this many milliseconds.  Any request to the
        payment service that would take longer than timeout_ms is failed
        fast at timeout_ms instead of waiting the full attack_value ms.
        The injected toxic latency is replaced with timeout_ms so Toxiproxy
        still exercises real infrastructure – just with a shorter delay.

    circuit_breaker_threshold_ms:
        Simulate a circuit breaker that opens when latency exceeds this
        threshold.  Once open, payment calls fail immediately (0 ms latency)
        instead of waiting.  Implemented as 0 ms latency in Toxiproxy.

    Both options are simulated by adjusting the Toxiproxy toxic value.
    simulation_mode = True is always returned when this config is used so
    the frontend can display the limitation honestly.
    """
    strategy: str                             # "timeout" | "circuit_breaker"
    timeout_ms: Optional[int] = None          # used when strategy = "timeout"
    circuit_breaker_threshold_ms: Optional[int] = None  # strategy = "circuit_breaker"


class ExperimentRequest(BaseModel):
    architecture_id: str
    attack: AttackConfig
    traffic: TrafficConfig = TrafficConfig()


class RetestRequest(BaseModel):
    architecture_id: str
    previous_attack_id: str
    recommendation_id: Optional[str] = None
    resilience: Optional[ResilienceConfig] = None
    traffic: TrafficConfig = TrafficConfig()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _safe_metrics(label: str) -> dict:
    """Collect gateway metrics; return {} on any failure."""
    try:
        m = await collect_gateway_metrics()
        logger.info("Metrics [%s]: %s", label, m)
        return m
    except Exception as exc:
        logger.warning("Could not collect %s metrics: %s", label, exc)
        return {}


async def _ensure_clean() -> None:
    """Remove payment-latency toxic if present."""
    if await toxic_exists("payment", "payment-latency"):
        try:
            await remove_latency()
        except Exception as exc:
            logger.warning("Cleanup of existing toxic failed: %s", exc)


def _effective_latency(
    attack_value: int,
    resilience: Optional[ResilienceConfig],
) -> tuple[int, bool, Optional[str]]:
    """
    Return (effective_latency_ms, simulation_mode, applied_strategy).

    If resilience is None → original attack unchanged, simulation_mode False.
    """
    if resilience is None:
        return attack_value, False, None

    if resilience.strategy == "timeout" and resilience.timeout_ms is not None:
        capped = min(attack_value, resilience.timeout_ms)
        return capped, True, "timeout"

    if resilience.strategy == "circuit_breaker":
        # Circuit breaker open: calls fail immediately → 0 ms wait
        return 0, True, "circuit_breaker"

    # Unknown strategy — fall back to original
    logger.warning("Unknown resilience strategy '%s', using original attack", resilience.strategy)
    return attack_value, False, None


# ---------------------------------------------------------------------------
# Core experiment runner
# ---------------------------------------------------------------------------

async def _run_experiment_core(
    architecture_id: str,
    attack_config: AttackConfig,
    traffic_config: TrafficConfig,
    retest_of: Optional[str] = None,
    resilience: Optional[ResilienceConfig] = None,
) -> dict:
    """
    Execute one full experiment cycle and return the result dict.

    When resilience is provided the toxic is injected with the effective
    (capped) latency rather than the raw attack value, and simulation_mode
    is set to True in the result.
    """
    # 1. Validate
    arch = architectures.get(architecture_id)
    if arch is None:
        raise HTTPException(
            status_code=404,
            detail=f"Architecture not found: {architecture_id}. Register it first via POST /api/architecture",
        )
    if attack_config.type != "latency":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported attack type: {attack_config.type}. MVP supports: latency",
        )
    if attack_config.target != "payment":
        raise HTTPException(
            status_code=400,
            detail="MVP latency attack supports target='payment' only",
        )

    experiment_id = f"exp_{uuid4().hex[:8]}"
    attack_id = f"atk_{uuid4().hex[:8]}"
    started_at = _now()

    effective_ms, simulation_mode, applied_strategy = _effective_latency(
        attack_config.value, resilience
    )

    logger.info(
        "Starting experiment %s | attack %s | effective_latency=%d ms | sim=%s",
        experiment_id, attack_id, effective_ms, simulation_mode,
    )

    # Register attack record
    attack_record: dict = {
        "attack_id": attack_id,
        "architecture_id": architecture_id,
        "status": "queued",
        "target": attack_config.target,
        "type": attack_config.type,
        "value": attack_config.value,
        "effective_value": effective_ms,
        "simulation_mode": simulation_mode,
        "applied_strategy": applied_strategy,
        "started_at": started_at,
        "completed_at": None,
        "metrics": None,
    }
    attacks[attack_id] = attack_record

    # 2. Baseline — clean traffic, no toxic
    logger.info("[%s] Collecting baseline…", experiment_id)
    await _ensure_clean()
    await generate_traffic(
        rate=min(traffic_config.rate, 3),
        duration_seconds=min(traffic_config.duration_seconds, 5),
    )
    await asyncio.sleep(2)
    baseline_metrics = await _safe_metrics("baseline")

    # 3. Inject attack (effective latency)
    logger.info("[%s] Injecting latency %d ms…", experiment_id, effective_ms)
    _set_status(attack_record, "running")
    try:
        await add_latency(latency_ms=effective_ms, jitter_ms=0)
        _set_status(attack_record, "failure_injected")
    except Exception as exc:
        _set_status(attack_record, "failed")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to inject attack: {str(exc)}",
        ) from exc

    # 4. Traffic under attack
    logger.info("[%s] Generating traffic under attack…", experiment_id)
    traffic_result = await generate_traffic(
        rate=traffic_config.rate,
        duration_seconds=traffic_config.duration_seconds,
    )
    await asyncio.sleep(3)

    # 5. Collect attack metrics
    logger.info("[%s] Collecting attack metrics…", experiment_id)
    attack_metrics = await _safe_metrics("attack")
    attack_record["metrics"] = attack_metrics
    _set_status(attack_record, "metrics_collected")

    # 6. Cleanup
    logger.info("[%s] Removing attack…", experiment_id)
    try:
        await remove_latency()
    except Exception as exc:
        logger.warning("[%s] Cleanup failed (non-fatal): %s", experiment_id, exc)
    _set_status(attack_record, "completed")

    # 7. Diagnose — pass both baseline and attack P95 so severity is accurate
    logger.info("[%s] Diagnosing…", experiment_id)
    context = DiagnosisContext(
        attack_type=attack_config.type,
        target=attack_config.target,
        attack_value=attack_config.value,
        observed_latency_ms=attack_metrics.get("average_latency_ms", 0.0),
        attack_id=attack_id,
        architecture_id=architecture_id,
        baseline_latency_ms=baseline_metrics.get("average_latency_ms"),
        observed_p95_ms=attack_metrics.get("p95_latency_ms"),
        baseline_p95_ms=baseline_metrics.get("p95_latency_ms"),
    )
    diagnosis = diagnose_from_context(context)

    # 8. Recommendations
    logger.info("[%s] Generating recommendations…", experiment_id)
    recs = generate_recommendations(
        attack_type=attack_config.type,
        target=attack_config.target,
        severity=diagnosis.get("severity", "medium"),
        attack_value=attack_config.value,
        observed_latency_ms=attack_metrics.get("average_latency_ms", 0.0),
    )

    # 9. Build and store result
    result = {
        "experiment_id": experiment_id,
        "attack_id": attack_id,
        "diagnosis_id": diagnosis.get("diagnosis_id"),
        "architecture_id": architecture_id,
        "retest_of": retest_of,
        "status": "completed",
        "simulation_mode": simulation_mode,
        "applied_strategy": applied_strategy,
        "started_at": started_at,
        "completed_at": _now(),
        "attack": {
            "target": attack_config.target,
            "type": attack_config.type,
            "value": attack_config.value,
            "effective_value": effective_ms,
        },
        "traffic": {
            "requested_rate": traffic_config.rate,
            "duration_seconds": traffic_config.duration_seconds,
            "total_requests": traffic_result.total_requests,
            "success_count": traffic_result.success_count,
            "error_count": traffic_result.error_count,
        },
        "baseline_metrics": baseline_metrics,
        "attack_metrics": attack_metrics,
        "diagnosis": diagnosis,
        "recommendations": recs,
    }
    experiments[experiment_id] = result
    return result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/experiment/run")
async def run_experiment(request: ExperimentRequest):
    """
    Run a full experiment:
    baseline → attack → traffic → metrics → diagnosis → recommendations → cleanup
    """
    result = await _run_experiment_core(
        architecture_id=request.architecture_id,
        attack_config=request.attack,
        traffic_config=request.traffic,
    )
    # Store the comparison skeleton keyed on the attack_id
    comparisons[result["attack_id"]] = {
        "attack_id": result["attack_id"],
        "experiment_id": result["experiment_id"],
        "before": result["baseline_metrics"],
        "after": None,
        "improvement": None,
    }
    return result


@router.post("/retest")
async def retest(request: RetestRequest):
    """
    Re-run the same attack on the same architecture, optionally with a
    resilience improvement applied.

    resilience field (optional):
      {
        "strategy": "timeout",
        "timeout_ms": 1000
      }
      or
      {
        "strategy": "circuit_breaker",
        "circuit_breaker_threshold_ms": 500
      }

    When resilience is supplied:
      - The Toxiproxy toxic is injected with an effective latency that
        reflects the resilience mechanism (capped or zeroed).
      - simulation_mode = true is returned explicitly.
      - The applied_strategy field describes what was applied.

    When resilience is omitted:
      - The original attack is replayed unchanged.
      - simulation_mode = false.

    In both cases the "after" slot of the original comparison is populated
    with the retest attack_metrics so GET /api/comparisons/{original_attack_id}
    shows a real before/after delta.
    """
    original_attack = attacks.get(request.previous_attack_id)
    if original_attack is None:
        raise HTTPException(
            status_code=404,
            detail=f"Original attack not found: {request.previous_attack_id}",
        )
    if architectures.get(request.architecture_id) is None:
        raise HTTPException(
            status_code=404,
            detail=f"Architecture not found: {request.architecture_id}",
        )

    attack_config = AttackConfig(
        target=original_attack["target"],
        type=original_attack["type"],
        value=original_attack["value"],
    )

    result = await _run_experiment_core(
        architecture_id=request.architecture_id,
        attack_config=attack_config,
        traffic_config=request.traffic,
        retest_of=request.previous_attack_id,
        resilience=request.resilience,
    )

    # Populate the comparison for the ORIGINAL attack_id
    original_comparison = comparisons.get(request.previous_attack_id)
    if original_comparison is None:
        # Create a skeleton if the original experiment was run before this
        # endpoint existed in the session
        original_comparison = {
            "attack_id": request.previous_attack_id,
            "experiment_id": None,
            "before": original_attack.get("metrics"),
            "after": None,
            "improvement": None,
        }
        comparisons[request.previous_attack_id] = original_comparison

    original_comparison["after"] = result["attack_metrics"]
    original_comparison["retest_experiment_id"] = result["experiment_id"]
    original_comparison["simulation_mode"] = result["simulation_mode"]
    original_comparison["applied_strategy"] = result["applied_strategy"]
    original_comparison["improvement"] = _calculate_improvement(
        original_comparison.get("before") or {},
        result["attack_metrics"],
    )

    # Return a flat response — every field the frontend needs is at the top level
    return {
        "retest_id": result["experiment_id"],
        "previous_attack_id": request.previous_attack_id,
        "new_attack_id": result["attack_id"],
        "architecture_id": request.architecture_id,
        "status": result["status"],
        "simulation_mode": result["simulation_mode"],
        "applied_strategy": result["applied_strategy"],
        "attack": result["attack"],
        "traffic": result["traffic"],
        "baseline_metrics": result["baseline_metrics"],
        "attack_metrics": result["attack_metrics"],
        "diagnosis": result["diagnosis"],
        "recommendations": result["recommendations"],
        "comparison": original_comparison,
    }


@router.get("/comparisons/{attack_id}")
async def get_comparison(attack_id: str):
    """Return before/after comparison for the given original attack ID."""
    comparison = comparisons.get(attack_id)
    if comparison is None:
        if attack_id not in attacks:
            raise HTTPException(
                status_code=404,
                detail=f"Attack not found: {attack_id}",
            )
        raise HTTPException(
            status_code=404,
            detail="No comparison data yet. Run a retest first via POST /api/retest.",
        )
    return comparison


# ---------------------------------------------------------------------------
# Comparison calculation
# ---------------------------------------------------------------------------

def _calculate_improvement(before: dict, after: dict) -> dict:
    """
    Calculate the measurable change between two metric snapshots.

    Positive latency_change_percent = degraded (latency went up).
    Negative latency_change_percent = improved (latency went down).
    """
    improvement: dict = {}
    if not before or not after:
        return improvement

    b_avg = before.get("average_latency_ms")
    a_avg = after.get("average_latency_ms")
    if b_avg and a_avg and b_avg > 0:
        pct = ((a_avg - b_avg) / b_avg) * 100
        improvement["latency_change_percent"] = round(pct, 1)
        improvement["latency_direction"] = "improved" if pct < 0 else "degraded"
        improvement["before_avg_latency_ms"] = round(b_avg, 1)
        improvement["after_avg_latency_ms"] = round(a_avg, 1)

    b_p95 = before.get("p95_latency_ms")
    a_p95 = after.get("p95_latency_ms")
    if b_p95 and a_p95 and b_p95 > 0:
        p95_pct = ((a_p95 - b_p95) / b_p95) * 100
        improvement["p95_change_percent"] = round(p95_pct, 1)
        improvement["before_p95_ms"] = round(b_p95, 1)
        improvement["after_p95_ms"] = round(a_p95, 1)

    b_err = before.get("error_rate_percent")
    a_err = after.get("error_rate_percent")
    if b_err is not None and a_err is not None and b_err > 0:
        improvement["error_rate_change_percent"] = round(
            ((a_err - b_err) / b_err) * 100, 1
        )

    return improvement
