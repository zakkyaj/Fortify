"""
Order Service
Receives requests from Gateway, calls Payment Service via Toxiproxy,
returns the result.
"""
import os
import time
import requests
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Payment calls go through Toxiproxy's payment proxy listen port
PAYMENT_PROXY_LISTEN = os.environ.get("PAYMENT_PROXY_LISTEN", "toxiproxy:20001")

REQUEST_COUNT = Counter(
    "order_requests_total",
    "Total number of requests received by order service",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "order_request_duration_seconds",
    "Request latency in seconds at order service",
    ["endpoint"],
)
PAYMENT_CALL_COUNT = Counter(
    "order_payment_calls_total",
    "Total payment upstream calls from order service",
    ["status"],
)
PAYMENT_CALL_LATENCY = Histogram(
    "order_payment_call_duration_seconds",
    "Latency of calls from order service to payment (via Toxiproxy)",
)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "order"}), 200


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/process", methods=["GET", "POST"])
def process():
    start = time.time()
    try:
        payment_start = time.time()
        resp = requests.get(
            f"http://{PAYMENT_PROXY_LISTEN}/pay",
            timeout=30,
        )
        payment_duration = time.time() - payment_start
        PAYMENT_CALL_LATENCY.observe(payment_duration)
        payment_status = resp.status_code
        payment_result = resp.json()
        PAYMENT_CALL_COUNT.labels(status=str(payment_status)).inc()
    except requests.exceptions.Timeout:
        payment_status = 504
        payment_result = {"error": "payment timeout"}
        PAYMENT_CALL_COUNT.labels(status="504").inc()
    except Exception as e:
        payment_status = 502
        payment_result = {"error": str(e)}
        PAYMENT_CALL_COUNT.labels(status="502").inc()

    duration = time.time() - start
    REQUEST_LATENCY.labels(endpoint="/process").observe(duration)
    REQUEST_COUNT.labels(
        method=request.method, endpoint="/process", status=str(payment_status)
    ).inc()

    return (
        jsonify(
            {
                "service": "order",
                "payment_status": payment_status,
                "payment_result": payment_result,
            }
        ),
        200 if payment_status == 200 else 502,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
