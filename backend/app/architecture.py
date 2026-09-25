"""
Architecture management.

In-memory storage for MVP — no database required.
"""
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/architecture",
    tags=["Architecture"],
)

# In-memory store: architecture_id -> architecture dict
architectures: dict[str, dict] = {}


class ServiceDefinition(BaseModel):
    id: str
    name: str
    type: Optional[str] = "service"


class Connection(BaseModel):
    source: str
    target: str


class ArchitectureRequest(BaseModel):
    architecture_id: Optional[str] = None
    name: str
    services: list[ServiceDefinition]
    connections: list[Connection]


@router.post("")
async def create_architecture(request: ArchitectureRequest):
    architecture_id = request.architecture_id or f"arch_{uuid4().hex[:8]}"

    record = {
        "architecture_id": architecture_id,
        "name": request.name,
        "services": [s.model_dump() for s in request.services],
        "connections": [c.model_dump() for c in request.connections],
    }

    architectures[architecture_id] = record

    return {
        "architecture_id": architecture_id,
        "status": "created",
    }


@router.get("/{architecture_id}")
async def get_architecture(architecture_id: str):
    arch = architectures.get(architecture_id)

    if arch is None:
        raise HTTPException(
            status_code=404,
            detail=f"Architecture not found: {architecture_id}",
        )

    return arch
