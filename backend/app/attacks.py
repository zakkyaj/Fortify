from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.toxiproxy import add_latency, remove_latency


router = APIRouter(
    prefix="/api/attacks",
    tags=["Attacks"],
)


# Temporary in-memory storage for the MVP.
# Later this can be replaced with a database or persistent store.
attacks: dict[str, dict[str, Any]] = {}


class AttackRequest(BaseModel):
    architecture_id: str
    target: str
    type: str
    value: Any


class LatencyAttack(BaseModel):
    duration_ms: int
    jitter_ms: int = 0


@router.post("")
async def create_attack(attack: AttackRequest):
    attack_id = f"atk_{uuid4().hex[:8]}"

    attack_record = {
        "attack_id": attack_id,
        "architecture_id": attack.architecture_id,
        "status": "running",
        "target": attack.target,
        "type": attack.type,
        "value": attack.value,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }

    attacks[attack_id] = attack_record

    try:
        if attack.type == "latency":
            if attack.target != "payment":
                raise HTTPException(
                    status_code=400,
                    detail="MVP latency attack currently supports target='payment' only",
                )

            if not isinstance(attack.value, int) or attack.value < 0:
                raise HTTPException(
                    status_code=400,
                    detail="Latency value must be a non-negative integer in milliseconds",
                )

            await add_latency(
                latency_ms=attack.value,
                jitter_ms=0,
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported attack type: {attack.type}",
            )

        attack_record["status"] = "completed"
        attack_record["completed_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        return {
            "attack_id": attack_id,
            "status": "started",
            "target": attack.target,
            "type": attack.type,
        }

    except HTTPException:
        attack_record["status"] = "failed"
        raise

    except Exception as exc:
        attack_record["status"] = "failed"

        raise HTTPException(
            status_code=502,
            detail=f"Attack execution failed: {str(exc)}",
        )


@router.get("/{attack_id}")
async def get_attack(attack_id: str):
    attack = attacks.get(attack_id)

    if attack is None:
        raise HTTPException(
            status_code=404,
            detail="Attack not found",
        )

    return attack


# Existing low-level latency endpoint.
# Keep this for direct Toxiproxy testing.
@router.post("/latency")
async def inject_latency(attack: LatencyAttack):
    result = await add_latency(
        latency_ms=attack.duration_ms,
        jitter_ms=attack.jitter_ms,
    )

    return {
        "attack": "latency",
        "duration_ms": attack.duration_ms,
        "jitter_ms": attack.jitter_ms,
        "result": result,
    }


@router.delete("/latency")
async def remove_latency_attack():
    return await remove_latency()