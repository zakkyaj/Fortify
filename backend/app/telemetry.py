from fastapi import APIRouter, HTTPException

from app.services.prometheus import query_prometheus

router = APIRouter(
    prefix="/api/metrics",
    tags=["Telemetry"],
)


@router.get("/{service_id}")
async def get_service_metrics(service_id: str):
    queries = {
        "gateway": {
            "request_count": "gateway_request_duration_seconds_count",
            "request_latency_sum": "gateway_request_duration_seconds_sum",
        }
    }

    if service_id not in queries:
        raise HTTPException(
            status_code=404,
            detail=f"Metrics not configured for service: {service_id}",
        )

    results = {}

    for name, query in queries[service_id].items():
        results[name] = await query_prometheus(query)

    # Extract Prometheus values
    request_count = 0
    latency_sum = 0.0

    count_result = results["request_count"]["result"]
    sum_result = results["request_latency_sum"]["result"]

    if count_result:
        request_count = int(float(count_result[0]["value"][1]))

    if sum_result:
        latency_sum = float(sum_result[0]["value"][1])

    average_latency = (
        latency_sum / request_count
        if request_count > 0
        else 0
    )

    return {
        "service": service_id,
        "request_count": request_count,
        "total_latency_seconds": round(latency_sum, 3),
        "average_latency_seconds": round(average_latency, 3),
        "average_latency_ms": round(average_latency * 1000, 1),
    }