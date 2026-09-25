"""
Toxiproxy client helpers.

Provides add_latency, remove_latency, and toxic_exists.
Raises HTTPException(502) when Toxiproxy is unreachable.
"""
import logging

import httpx
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)


async def toxic_exists(proxy: str, toxic_name: str) -> bool:
    """Return True if the named toxic already exists on the given proxy."""
    url = f"{settings.toxiproxy_url}/proxies/{proxy}/toxics"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
        if response.status_code != 200:
            return False
        toxics = response.json()
        return any(t.get("name") == toxic_name for t in toxics)
    except Exception as exc:
        logger.warning("Could not check toxic existence: %s", exc)
        return False


async def add_latency(latency_ms: int, jitter_ms: int = 0):
    """Inject a latency toxic on the payment proxy."""
    url = f"{settings.toxiproxy_url}/proxies/payment/toxics"

    payload = {
        "name": "payment-latency",
        "type": "latency",
        "stream": "downstream",
        "attributes": {
            "latency": latency_ms,
            "jitter": jitter_ms,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Toxiproxy error: {exc.response.status_code} {exc.response.text}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Toxiproxy unreachable: {str(exc)}",
        ) from exc

    return response.json()


async def remove_latency():
    """Remove the payment-latency toxic from the payment proxy."""
    url = (
        f"{settings.toxiproxy_url}"
        "/proxies/payment/toxics/payment-latency"
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(url)
            if response.status_code == 404:
                # Already removed — treat as success
                return {"status": "not_found", "toxic": "payment-latency"}
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Toxiproxy error removing toxic: {exc.response.status_code} {exc.response.text}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Toxiproxy unreachable: {str(exc)}",
        ) from exc

    return {"status": "removed", "toxic": "payment-latency"}
