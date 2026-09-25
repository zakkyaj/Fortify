"""
Payment Service
Handles payment requests, talks to the SQLite database,
returns a success response.
Traffic reaches this service through Toxiproxy.
"""
import os
import sqlite3
import time
from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "/data/payments.db")

REQUEST_COUNT = Counter(
    "payment_requests_total",
    "Total number of requests received by payment service",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "payment_request_duration_seconds",
    "Request latency in seconds at payment service",
    ["endpoint"],
)


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS payments "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, amount REAL, ts TEXT)"
    )
    conn.commit()
    return conn


@app.route("/health")
def health():
    try:
        conn = get_db()
        conn.execute("SELECT 1")
        conn.close()
        db_status = "ok"
    except Exception as e:
        db_status = str(e)
    return jsonify({"status": "ok", "service": "payment", "db": db_status}), 200


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/pay", methods=["GET", "POST"])
def pay():
    start = time.time()
    try:
        conn = get_db()
        conn.execute("INSERT INTO payments (amount, ts) VALUES (?, datetime('now'))", (100.0,))
        conn.commit()
        row = conn.execute("SELECT COUNT(*) FROM payments").fetchone()
        conn.close()
        result = {"status": "ok", "service": "payment", "total_payments": row[0]}
        status = 200
    except Exception as e:
        result = {"error": str(e)}
        status = 500

    duration = time.time() - start
    REQUEST_LATENCY.labels(endpoint="/pay").observe(duration)
    REQUEST_COUNT.labels(method="GET", endpoint="/pay", status=str(status)).inc()

    return jsonify(result), status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
