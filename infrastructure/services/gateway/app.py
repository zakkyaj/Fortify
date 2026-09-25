"""
Gateway Service
Accepts requests and forwards them to Order Service.
Exposes /health and /order endpoints.
"""
import os
import time
import requests
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://order:5001")

# Prometheus metrics
REQUEST_COUNT = Counter(
    "gateway_requests_total",
    "Total number of requests received by gateway",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "gateway_request_duration_seconds",
    "Request latency in seconds at gateway",
    ["endpoint"],
)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "gateway"}), 200


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/order", methods=["POST", "GET"])
def order():
    start = time.time()
    try:
        if request.method == "POST":
            payload = request.get_json(silent=True) or {}
        else:
            payload = {}

        resp = requests.get(f"{ORDER_SERVICE_URL}/process", json=payload, timeout=30)
        status = resp.status_code
        result = resp.json()
    except requests.exceptions.Timeout:
        status = 504
        result = {"error": "upstream timeout"}
    except Exception as e:
        status = 502
        result = {"error": str(e)}

    duration = time.time() - start
    REQUEST_LATENCY.labels(endpoint="/order").observe(duration)
    REQUEST_COUNT.labels(method=request.method, endpoint="/order", status=str(status)).inc()

    return jsonify(result), status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
