"""
FORTIFY Backend — main application entry point.
"""
import logging

from fastapi import FastAPI

from app.architecture import router as architecture_router
from app.attacks import router as attacks_router
from app.config import settings
from app.diagnosis import router as diagnosis_router
from app.experiment import router as experiment_router
from app.recommendations import router as recommendations_router
from app.telemetry import router as telemetry_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)

app = FastAPI(
    title="FORTIFY Backend",
    version="1.0.0",
    description=(
        "AI-powered architecture resilience testing platform. "
        "Attack → Observe → Diagnose → Improve → Compare."
    ),
)

app.include_router(architecture_router)
app.include_router(attacks_router)
app.include_router(telemetry_router)
app.include_router(diagnosis_router)
app.include_router(recommendations_router)
app.include_router(experiment_router)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "fortify-backend",
    }


@app.get("/api/config", tags=["Health"])
def get_config():
    return {
        "toxiproxy_url": settings.toxiproxy_url,
        "prometheus_url": settings.prometheus_url,
        "target_url": settings.target_url,
    }
