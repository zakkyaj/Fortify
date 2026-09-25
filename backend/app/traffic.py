"""
Traffic generation utility.

Generates HTTP traffic to the gateway to produce meaningful Prometheus metrics.
Uses asyncio + httpx for concurrency — no extra dependencies required.

Deliberately safe for a local hackathon machine:
- capped at 20 RPS maximum
- configurable rate and duration
"""
import asyncio
import logging
from dataclasses import dataclass, field

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_MAX_RATE = 20  # requests per second hard cap


@dataclass
class TrafficResult:
    total_requests: int = 0
    success_count: int = 0
    error_count: int = 0
    errors: list[str] = field(default_factory=list)


async def generate_traffic(
    rate: int,
    duration_seconds: int,
) -> TrafficResult:
    """
    Send requests to the gateway at the requested rate for the given duration.

    Args:
        rate: target requests per second (capped at _MAX_RATE)
        duration_seconds: how long to run

    Returns:
        TrafficResult with counts of success/error.
    """
    rate = min(rate, _MAX_RATE)
    url = settings.target_url
    interval = 1.0 / rate if rate > 0 else 1.0
    total_requests = rate * duration_seconds
    result = TrafficResult()

    logger.info(
        "Traffic generation: %d req/s for %ds → %d requests → %s",
        rate,
        duration_seconds,
        total_requests,
        url,
    )

    async with httpx.AsyncClient(timeout=35.0) as client:
        tasks: list[asyncio.Task] = []
        deadline = asyncio.get_event_loop().time() + duration_seconds

        while asyncio.get_event_loop().time() < deadline:
            task = asyncio.create_task(_send_request(client, url, result))
            tasks.append(task)
            await asyncio.sleep(interval)

        # Wait for all in-flight requests to settle (with a generous timeout)
        remaining = max(0.0, deadline - asyncio.get_event_loop().time()) + 35.0
        await asyncio.wait(tasks, timeout=remaining)

    logger.info(
        "Traffic generation complete: %d ok / %d errors",
        result.success_count,
        result.error_count,
    )
    return result


async def _send_request(
    client: httpx.AsyncClient,
    url: str,
    result: TrafficResult,
) -> None:
    result.total_requests += 1
    try:
        response = await client.post(url, json={"source": "fortify-traffic-gen"})
        if response.status_code < 500:
            result.success_count += 1
        else:
            result.error_count += 1
    except Exception as exc:
        result.error_count += 1
        err = str(exc)
        if len(result.errors) < 5:
            result.errors.append(err)
