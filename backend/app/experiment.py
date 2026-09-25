from fastapi import APIRouter


router = APIRouter(
    prefix="/api/experiment",
    tags=["Experiment"],
)


@router.post("/run")
async def run_experiment():
    return {
        "status": "ready",
        "message": "Experiment orchestration endpoint created",
    }