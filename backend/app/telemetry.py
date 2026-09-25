"""
Telemetry / metrics API.

Provides GET /api/metrics/{service_id} for current service metrics.
Also exports:
  - collect_raw_counters()   — snapshot of raw cumulative Prometheus counters
  - collect_metrics_from_delta() — derive request_count / avg_latency_ms from
                                   two snapshots, avoiding the scrape-timing
                                   problem with instant queries.
  - collect_gateway_metrics()    — backward-compatible wrapper used by the
                                   experiment orchestrator.

Root cause of the baseline=0 bug (fixed here):
  The original code issued instant queries for gateway_request_duration_seconds_count
  and _sum immediately after baseline traffic completed, with only a 2-second
  sleep.  Prometheus scrapes every 10 seconds.  If the scrape hadn't fired yet,
  the counters still reflected pre-traffic values (often 0 on first run).

Fix:
  The experiment orchestrator now takes a raw counter snapshot BEFORE each
  traffic window starts, waits for at least one Prometheus scrape cycle
  (12 seconds), then takes a snapshot AFTER.  The *delta* between the two
  snapshots is used to compute request_count and average_latency_ms, so the
  measurement is independent of what happened before the window.

  The GET /api/metrics/{service_id} endpoint still uses instant queries (as
  before) because it is a live/point-in-time view, not a window measurement.
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
# Metric query definitions per service
# ---------------------------------------------------------------------------

# Each entry:
#   count_query  — raw cumulative counter for request count
#   sum_query    — raw cumulative counter for latency sum (seconds)
#   p95_query    — pre-built P95 rate query (string)
#   error_count_query / total_count_query — for error-rate calc (optional)

_SERVICE_QUERIES = {
    "gateway": {
        "count_query": "gateway_request_duration_seconds_count",
        "sum_query":   "gateway_request_duration_seconds_sum",
        "p95_query":   "histogram_quantile(0.95, rate(gateway_request_duration_seconds_bucket[1m]))",
        "error_count_query": 'sum(gateway_requests_total{status!="200"})',
        "total_count_query": "sum(gateway_requests_total)",
    },
    "order": {
        "count_query": "order_request_duration_seconds_count",
        "sum_query":   "order_request_duration_seconds_sum",
        "p95_query":   "histogram_quantile(0.95, rate(order_request_duration_seconds_bucket[1m]))",
        "error_count_query": 'sum(order_requests_total{status!="200"})',
        "total_count_query": "sum(order_requests_total)",
    },
    "payment": {
        "count_query": "order_payment_call_duration_seconds_count",
        "sum_query":   "order_payment_call_duration_seconds_sum",
        "p95_query":   "histogram_quantile(0.95, rate(order_payment_call_duration_seconds_bucket[1m]))",
        "error_count_query": None,
        "total_count_query": None,
    },
}

# Keep the old key names alive for backward compatibility (GET /metrics endpoint)
_COMPAT_QUERIES = {
    svc: {
        "request_count_query": v["count_query"],
        "latency_sum_query":   v["sum_query"],
        "p95_query":           v["p95_query"],
        "error_count_query":   v.get("error_count_query"),
        "total_count_query":   v.get("total_count_query"),
    }
    for svc, v in _SERVICE_QUERIES.items()
}


# ---------------------------------------------------------------------------
# Raw counter snapshot (used by the experiment orchestrator)
# ---------------------------------------------------------------------------

async def collect_raw_counters(service_id: str = "gateway") -> dict:
    """
    Return current cumulative counter values for the service.

    Keys: count, latency_sum
    These are monotonically increasing since the service started.
    Subtract a previous snapshot to get the delta for a traffic window.
    """
    if service_id not in _SERVICE_QUERIES:
        logger.warning("collect_raw_counters: unknown service '%s'", service_id)
        return {"count": 0.0, "latency_sum": 0.0}

    q = _SERVICE_QUERIES[service_id]
    try:
        count = await query_scalar(q["count_query"], 0.0)
        latency_sum = await query_scalar(q["sum_query"], 0.0)
        return {"count": count, "latency_sum": latency_sum}
    except Exception as exc:
        logger.warning("collect_raw_counters failed: %s", exc)
        return {"count": 0.0, "latency_sum": 0.0}


# ---------------------------------------------------------------------------
# Delta-based metrics (used by the experiment orchestrator for each window)
# ---------------------------------------------------------------------------

def compute_metrics_from_delta(
    before: dict,
    after: dict,
    service_id: str,
    p95_latency_ms: float | None = None,
    error_rate_percent: float | None = None,
) -> dict:
    """
    Compute request_count and average_latency_ms from two raw counter
    snapshots.  Both ``before`` and ``after`` should come from
    ``collect_raw_counters()``.

    ``p95_latency_ms`` and ``error_rate_percent`` are passed in from
    a separate Prometheus query (they are rate-based and don't need deltas).

    Returns a dict compatible with the existing experiment result schema.
    """
    delta_count       = max(0.0, after.get("count", 0.0)       - before.get("count", 0.0))
    delta_latency_sum = max(0.0, after.get("latency_sum", 0.0) - before.get("latency_sum", 0.0))

    average_latency_s  = delta_latency_sum / delta_count if delta_count > 0 else 0.0
    average_latency_ms = round(average_latency_s * 1000, 1)

    metrics: dict = {
        "service":                 service_id,
        "request_count":           int(delta_count),
        "total_latency_seconds":   round(delta_latency_sum, 3),
        "average_latency_seconds": round(average_latency_s, 3),
        "average_latency_ms":      average_latency_ms,
    }

    if p95_latency_ms is not None and p95_latency_ms >= 0:
        metrics["p95_latency_ms"] = round(p95_latency_ms, 1)

    if error_rate_percent is not None:
        metrics["error_rate_percent"] = round(error_rate_percent, 2)

    return metrics


async def collect_metrics_from_delta(
    before: dict,
    after: dict,
    service_id: str = "gateway",
) -> dict:
    """
    Async wrapper: queries P95 and error rate from Prometheus (rate-based,
    so they don't need delta treatment), then combines with the counter delta.

    ``before`` / ``after`` must be dicts returned by ``collect_raw_counters()``.
    """
    if service_id not in _SERVICE_QUERIES:
        logger.warning("collect_metrics_from_delta: unknown service '%s'", service_id)
        return {}

    q = _SERVICE_QUERIES[service_id]

    p95_ms: float | None = None
    if q.get("p95_query"):
        try:
            p95 = await query_scalar(q["p95_query"], -1.0)
            if p95 >= 0:
                p95_ms = p95 * 1000
        except Exception:
            pass

    error_rate: float | None = None
    if q.get("error_count_query") and q.get("total_count_query"):
        try:
            error_count = await query_scalar(q["error_count_query"], 0.0)
            total_count = await query_scalar(q["total_count_query"], 0.0)
            if total_count > 0:
                error_rate = (error_count / total_count) * 100
        except Exception:
            pass

    return compute_metrics_from_delta(before, after, service_id, p95_ms, error_rate)


# ---------------------------------------------------------------------------
# Backward-compatible instant-query collector (used by GET /metrics endpoint)
# ---------------------------------------------------------------------------

async def _collect_metrics(service_id: str) -> dict:
    """
    Collect structured metrics for a service from Prometheus using instant
    (cumulative) queries.

    This is used only by GET /api/metrics/{service_id} for live/point-in-time
    views.  The experiment orchestrator uses collect_metrics_from_delta() instead.
    """
    if service_id not in _COMPAT_QUERIES:
        raise HTTPException(
            status_code=404,
            detail=f"Metrics not configured for service: {service_id}",
        )

    q = _COMPAT_QUERIES[service_id]

    request_count = int(await query_scalar(q["request_count_query"], 0.0))
    latency_sum   = await query_scalar(q["latency_sum_query"], 0.0)
    average_latency = latency_sum / request_count if request_count > 0 else 0.0

    metrics: dict = {
        "service":                 service_id,
        "request_count":           request_count,
        "total_latency_seconds":   round(latency_sum, 3),
        "average_latency_seconds": round(average_latency, 3),
        "average_latency_ms":      round(average_latency * 1000, 1),
    }

    if q.get("p95_query"):
        try:
            p95 = await query_scalar(q["p95_query"], -1.0)
            if p95 >= 0:
                metrics["p95_latency_ms"] = round(p95 * 1000, 1)
        except Exception:
            pass

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


# Convenience alias kept for backward compatibility
async def collect_gateway_metrics() -> dict:
    """Instant-query snapshot of gateway metrics (backward-compatible)."""
    return await _collect_metrics("gateway")


@router.get("/{service_id}")
async def get_service_metrics(service_id: str):
    return await _collect_metrics(service_id)
