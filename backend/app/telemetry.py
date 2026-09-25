"""
Telemetry / metrics API.

Provides GET /api/metrics/{service_id} for current service metrics.
Also exports collect_gateway_metrics() for use by the experiment orchestrator.
"""
import logging

from fastapi import APIRouter, HTTPException

from app.services.prometheus import query_scalar

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/metrics",
    tags=["Telemetry"],
)

# ---------------------------------------------------------------------------
# Service metric definitions
# ---------------------------------------------------------------------------

_SERVICE_QUERIES = {
    "gateway": {
        "request_count_query": "gateway_request_duration_seconds_count",
        "latency_sum_query": "gateway_request_duration_seconds_sum",
        # P95 histogram quantile — available when the histogram has buckets
        "p95_query": "histogram_quantile(0.95, rate(gateway_request_duration_seconds_bucket[5m]))",
        # Error rate: fraction of non-200 responses (approximated via status label)
        "error_count_query": 'sum(gateway_requests_total{status!="200"})',
        "total_count_query": "sum(gateway_requests_total)",
    },
    "order": {
        "request_count_query": "order_request_duration_seconds_count",
        "latency_sum_query": "order_request_duration_seconds_sum",
        "p95_query": "histogram_quantile(0.95, rate(order_request_duration_seconds_bucket[5m]))",
        "error_count_query": 'sum(order_requests_total{status!="200"})',
        "total_count_query": "sum(order_requests_total)",
    },
    "payment": {
        "request_count_query": "order_payment_call_duration_seconds_count",
        "latency_sum_query": "order_payment_call_duration_seconds_sum",
        "p95_query": "histogram_quantile(0.95, rate(order_payment_call_duration_seconds_bucket[5m]))",
        "error_count_query": None,
        "total_count_query": None,
    },
}


async def _collect_metrics(service_id: str) -> dict:
    """
    Collect structured metrics for a service from Prometheus.

    Returns a dict with all available metrics.
    Missing/unavailable metrics are omitted rather than faked.
    """
    if service_id not in _SERVICE_QUERIES:
        raise HTTPException(
            status_code=404,
            detail=f"Metrics not configured for service: {service_id}",
        )

    q = _SERVICE_QUERIES[service_id]

    request_count = int(await query_scalar(q["request_count_query"], 0.0))
    latency_sum = await query_scalar(q["latency_sum_query"], 0.0)

    average_latency = latency_sum / request_count if request_count > 0 else 0.0

    metrics: dict = {
        "service": service_id,
        "request_count": request_count,
        "total_latency_seconds": round(latency_sum, 3),
        "average_latency_seconds": round(average_latency, 3),
        "average_latency_ms": round(average_latency * 1000, 1),
    }

    # P95 — only include if the query returns a meaningful value
    if q.get("p95_query"):
        try:
            p95 = await query_scalar(q["p95_query"], -1.0)
            if p95 >= 0:
                metrics["p95_latency_ms"] = round(p95 * 1000, 1)
        except Exception:
            pass  # P95 not available — skip rather than fail

    # Error rate
    if q.get("error_count_query") and q.get("total_count_query"):
        try:
            error_count = await query_scalar(q["error_count_query"], 0.0)
            total_count = await query_scalar(q["total_count_query"], 0.0)
            if total_count > 0:
                metrics["error_rate_percent"] = round(
                    (error_count / total_count) * 100, 2
                )
        except Exception:
            pass

    return metrics


async def collect_gateway_metrics() -> dict:
    """Convenience wrapper used by the experiment orchestrator."""
    return await _collect_metrics("gateway")


@router.get("/{service_id}")
async def get_service_metrics(service_id: str):
    return await _collect_metrics(service_id)
