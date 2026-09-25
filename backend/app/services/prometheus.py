"""
Prometheus query helpers.

Wraps all raw Prometheus API calls. Callers get clean Python values;
they never see the raw Prometheus JSON envelope.
"""
import logging

import httpx
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)


async def query_prometheus(query: str) -> dict:
    """
    Execute a Prometheus instant query.

    Returns the raw ``data`` dict from the Prometheus API
    (i.e. ``{"resultType": ..., "result": [...]}``)
    or raises HTTPException(503) if Prometheus is unavailable.
    """
    url = f"{settings.prometheus_url}/api/v1/query"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params={"query": query})
            response.raise_for_status()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Prometheus unreachable: {str(exc)}",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Prometheus returned {exc.response.status_code}",
        ) from exc

    data = response.json()

    if data.get("status") != "success":
        raise HTTPException(
            status_code=503,
            detail=f"Prometheus query failed: {data.get('error', 'unknown')}",
        )

    return data["data"]


async def query_scalar(query: str, default: float = 0.0) -> float:
    """
    Execute a Prometheus instant query and return the first scalar value.

    Returns ``default`` when the query produces no results.
    """
    data = await query_prometheus(query)
    result = data.get("result", [])
    if not result:
        return default
    try:
        return float(result[0]["value"][1])
    except (KeyError, IndexError, ValueError):
        return default
