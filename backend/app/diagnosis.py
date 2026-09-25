from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/diagnosis",
    tags=["Diagnosis"],
)


class DiagnosisRequest(BaseModel):
    attack_type: str
    target: str
    attack_value: int
    average_latency_ms: float


@router.post("")
async def diagnose(request: DiagnosisRequest):
    if request.attack_type == "latency":
        if request.average_latency_ms > request.attack_value * 1.5:
            severity = "high"
        elif request.average_latency_ms > request.attack_value:
            severity = "medium"
        else:
            severity = "low"

        return {
            "problem": (
                f"{request.target} latency is affecting the request path."
            ),
            "severity": severity,
            "evidence": {
                "attack_latency_ms": request.attack_value,
                "observed_latency_ms": request.average_latency_ms,
            },
            "recommendation": (
                "Introduce timeout and asynchronous processing "
                "around the dependency."
            ),
        }

    return {
        "problem": "Unsupported attack type.",
        "severity": "unknown",
        "evidence": {},
        "recommendation": "No recommendation available.",
    }