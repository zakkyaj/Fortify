import httpx

from app.config import settings


async def add_latency(
    latency_ms: int,
    jitter_ms: int = 0,
):
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

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()

    return response.json()


async def remove_latency():
    url = (
        f"{settings.toxiproxy_url}"
        "/proxies/payment/toxics/payment-latency"
    )

    async with httpx.AsyncClient() as client:
        response = await client.delete(url)
        response.raise_for_status()

    return {
        "status": "removed",
        "toxic": "payment-latency",
    }