"""
Attack management.

Lifecycle states:
  queued → running → failure_injected → metrics_collected → completed
                                                           → failed

Handles duplicate-toxic gracefully (409 from Toxiproxy is treated as
idempotent for latency attacks).
"""
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.toxiproxy import add_latency, remove_latency, toxic_exists

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/attacks",
    tags=["Attacks"],
)

# In-memory store: attack_id -> attack dict
attacks: dict[str, dict[str, Any]] = {}


class AttackRequest(BaseModel):
    architecture_id: str
    target: str
    type: str
    value: Any


class LatencyAttack(BaseModel):
    duration_ms: int
    jitter_ms: int = 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _set_status(record: dict, status: str) -> None:
    record["status"] = status
    if status in ("completed", "failed"):
        record["completed_at"] = _now()


@router.post("")
async def create_attack(attack: AttackRequest):
    attack_id = f"atk_{uuid4().hex[:8]}"

    record: dict[str, Any] = {
        "attack_id": attack_id,
        "architecture_id": attack.architecture_id,
        "status": "queued",
        "target": attack.target,
        "type": attack.type,
        "value": attack.value,
        "started_at": _now(),
        "completed_at": None,
        "metrics": None,
    }
    attacks[attack_id] = record

    try:
        if attack.type != "latency":
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported attack type: {attack.type}. MVP supports: latency",
            )

        if attack.target != "payment":
            raise HTTPException(
                status_code=400,
                detail="MVP latency attack currently supports target='payment' only",
            )

        if not isinstance(attack.value, (int, float)) or attack.value < 0:
            raise HTTPException(
                status_code=400,
                detail="Latency value must be a non-negative integer (milliseconds)",
            )

        _set_status(record, "running")

        # If the toxic already exists, remove it first so we can re-apply cleanly.
        if await toxic_exists("payment", "payment-latency"):
            logger.info("Existing payment-latency toxic found — removing before re-injection")
            try:
                await remove_latency()
            except Exception as exc:
                logger.warning("Could not remove existing toxic: %s", exc)

        await add_latency(latency_ms=int(attack.value), jitter_ms=0)
        _set_status(record, "failure_injected")

        return {
            "attack_id": attack_id,
            "status": "failure_injected",
            "target": attack.target,
            "type": attack.type,
            "value": attack.value,
        }

    except HTTPException:
        _set_status(record, "failed")
        raise

    except Exception as exc:
        _set_status(record, "failed")
        logger.exception("Attack execution failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=f"Attack execution failed: {str(exc)}",
        )


@router.get("/{attack_id}")
async def get_attack(attack_id: str):
    record = attacks.get(attack_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Attack not found: {attack_id}")
    return record


@router.get("/{attack_id}/metrics")
async def get_attack_metrics(attack_id: str):
    record = attacks.get(attack_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Attack not found: {attack_id}")

    if record.get("metrics") is None:
        raise HTTPException(
            status_code=404,
            detail="Metrics not yet collected for this attack. Run the experiment first.",
        )

    return {
        "attack_id": attack_id,
        "metrics": record["metrics"],
    }


# ---------------------------------------------------------------------------
# Low-level helpers — kept for direct Toxiproxy testing
# ---------------------------------------------------------------------------

@router.post("/latency")
async def inject_latency(attack: LatencyAttack):
    result = await add_latency(latency_ms=attack.duration_ms, jitter_ms=attack.jitter_ms)
    return {
        "attack": "latency",
        "duration_ms": attack.duration_ms,
        "jitter_ms": attack.jitter_ms,
        "result": result,
    }


@router.delete("/latency")
async def remove_latency_attack():
    return await remove_latency()
