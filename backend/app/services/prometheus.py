import httpx

from app.config import settings


async def query_prometheus(query: str):
    url = f"{settings.prometheus_url}/api/v1/query"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params={"query": query},
        )
        response.raise_for_status()

    data = response.json()

    if data.get("status") != "success":
        raise RuntimeError("Prometheus query failed")

    return data["data"]