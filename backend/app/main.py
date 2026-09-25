from fastapi import FastAPI
from app.diagnosis import router as diagnosis_router

from app.attacks import router as attacks_router
from app.config import settings
from app.telemetry import router as telemetry_router


app = FastAPI(
    title="FORTIFY Backend",
    version="1.0.0",
)

app.include_router(attacks_router)
app.include_router(telemetry_router)
app.include_router(diagnosis_router)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "fortify-backend",
    }


@app.get("/api/config")
def get_config():
    return {
        "toxiproxy_url": settings.toxiproxy_url,
        "prometheus_url": settings.prometheus_url,
        "target_url": settings.target_url,
    }