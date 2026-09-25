# FORTIFY Infrastructure

Minimal Docker Compose environment for the FORTIFY architecture resilience
testing platform. Designed for a 2-day hackathon MVP.

---

## What it does

Runs a demo microservice architecture that the Fortify backend can attack
with controlled failures and observe with Prometheus:

```
External request
      ↓
  Gateway  (port 8080)
      ↓
Order Service  (port 5001)
      ↓
Toxiproxy  (port 20001 – internal payment proxy)
      ↓
Payment Service  (port 5002)
      ↓
SQLite database  (/data/payments.db inside the container)
```

Fault injection is done via the **Toxiproxy REST API** (port 8474).  
Metrics are collected by **Prometheus** (port 9090).

---

## Directory structure

```
infrastructure/
├── docker-compose.yml
├── services/
│   ├── gateway/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── order/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── payment/
│       ├── app.py
│       ├── Dockerfile
│       └── requirements.txt
├── prometheus/
│   └── prometheus.yml
└── toxiproxy/
    └── toxiproxy.json
```

---

## Start / Stop

```bash
# Start everything (builds images on first run)
docker compose up --build

# Start in the background
docker compose up --build -d

# Stop and remove containers
docker compose down

# Stop, remove containers AND the payment-data volume
docker compose down -v
```

All commands must be run from the `infrastructure/` directory.

---

## Service ports

| Service       | Host port | Purpose                        |
|---------------|-----------|--------------------------------|
| Gateway       | `8080`    | External entry point           |
| Order         | `5001`    | Direct testing / debug         |
| Payment       | `5002`    | Direct testing / debug         |
| Toxiproxy API | `8474`    | REST API for fault injection   |
| Prometheus    | `9090`    | Metrics UI & query API         |

Port `20001` (payment proxy listen) is **internal only** — it is not
exposed to the host. Only the Order Service communicates through it.

---

## Health endpoints

Every service exposes `GET /health`:

| Service  | URL                               |
|----------|-----------------------------------|
| Gateway  | http://localhost:8080/health      |
| Order    | http://localhost:5001/health      |
| Payment  | http://localhost:5002/health      |

Toxiproxy: `GET http://localhost:8474/version`  
Prometheus: `GET http://localhost:9090/-/healthy`

---

## Toxiproxy configuration

Toxiproxy is seeded at startup with one proxy:

| Field    | Value              |
|----------|--------------------|
| Name     | `payment`          |
| Listen   | `0.0.0.0:20001`   |
| Upstream | `payment:5002`     |

The proxy is pre-created by the seed file
[`toxiproxy/toxiproxy.json`](toxiproxy/toxiproxy.json) and is available
immediately after the container starts.

---

## How to inject 5000 ms latency (manual / curl)

### Step 1 — Add the latency toxic

```bash
curl -s -X POST http://localhost:8474/proxies/payment/toxics \
  -H "Content-Type: application/json" \
  -d '{
    "name": "payment-latency",
    "type": "latency",
    "stream": "downstream",
    "attributes": {
      "latency": 5000,
      "jitter": 0
    }
  }'
```

### Step 2 — Send a test request (should take ~5 s)

```bash
curl -s http://localhost:8080/order
```

### Step 3 — Remove the latency toxic

```bash
curl -s -X DELETE \
  http://localhost:8474/proxies/payment/toxics/payment-latency
```

After deletion the system returns to normal latency immediately.

---

## Prometheus

**URL:** http://localhost:9090

### Scrape targets

| Job       | Target          | Path       |
|-----------|-----------------|------------|
| `gateway` | `gateway:5000`  | `/metrics` |
| `order`   | `order:5001`    | `/metrics` |
| `payment` | `payment:5002`  | `/metrics` |

Scrape interval: **10 s**

### Metric names

#### Gateway

| Metric                              | Type      | Labels                       | Description                            |
|-------------------------------------|-----------|------------------------------|----------------------------------------|
| `gateway_requests_total`            | Counter   | `method`, `endpoint`, `status` | Total requests received by gateway   |
| `gateway_request_duration_seconds`  | Histogram | `endpoint`                   | End-to-end request latency at gateway  |

#### Order Service

| Metric                                    | Type      | Labels                       | Description                                         |
|-------------------------------------------|-----------|------------------------------|-----------------------------------------------------|
| `order_requests_total`                    | Counter   | `method`, `endpoint`, `status` | Total requests received by order service          |
| `order_request_duration_seconds`          | Histogram | `endpoint`                   | End-to-end request latency at order service         |
| `order_payment_calls_total`               | Counter   | `status`                     | Total calls from order to payment (via Toxiproxy)   |
| `order_payment_call_duration_seconds`     | Histogram | —                            | Latency of order → Toxiproxy → payment calls        |

#### Payment Service

| Metric                               | Type      | Labels                       | Description                             |
|--------------------------------------|-----------|------------------------------|-----------------------------------------|
| `payment_requests_total`             | Counter   | `method`, `endpoint`, `status` | Total requests received by payment    |
| `payment_request_duration_seconds`   | Histogram | `endpoint`                   | Request latency at payment service      |

**Key metric for latency detection:**
`order_payment_call_duration_seconds` — this directly measures the
latency of the Order → Toxiproxy → Payment leg, making the injected
5000 ms immediately visible.

---

## Backend integration reference

```
Gateway URL:
  http://localhost:8080

Toxiproxy API URL:
  http://localhost:8474

Prometheus URL:
  http://localhost:9090

Toxiproxy payment proxy name:
  payment

Payment proxy listen address (internal, used by Order Service):
  toxiproxy:20001

Payment proxy upstream address:
  payment:5002

Docker service names:
  gateway, order, payment, toxiproxy, prometheus

Docker container names:
  fortify-gateway, fortify-order, fortify-payment,
  fortify-toxiproxy, fortify-prometheus

Prometheus scrape targets:
  gateway:5000/metrics
  order:5001/metrics
  payment:5002/metrics

Prometheus metric names (most useful for experiment analysis):
  order_payment_call_duration_seconds   ← latency of the injected leg
  order_payment_calls_total             ← call count + status codes
  gateway_request_duration_seconds      ← end-to-end latency at gateway
  gateway_requests_total                ← total request count at gateway
  payment_requests_total                ← payment service request count
  payment_request_duration_seconds      ← latency inside payment service

Toxiproxy add-latency API call:
  POST http://localhost:8474/proxies/payment/toxics
  Body: {"name":"payment-latency","type":"latency","stream":"downstream",
         "attributes":{"latency":5000,"jitter":0}}

Toxiproxy remove-latency API call:
  DELETE http://localhost:8474/proxies/payment/toxics/payment-latency
```

---

## Testing the three scenarios

### TEST 1 — Normal request

```bash
curl -s http://localhost:8080/order
# Expected: fast response, payment_status: 200
```

### TEST 2 — Failure injection

```bash
# Inject 5000 ms latency
curl -s -X POST http://localhost:8474/proxies/payment/toxics \
  -H "Content-Type: application/json" \
  -d '{"name":"payment-latency","type":"latency","stream":"downstream",
       "attributes":{"latency":5000,"jitter":0}}'

# Send request — should take ~5 seconds
curl -s http://localhost:8080/order

# Observe in Prometheus:
# order_payment_call_duration_seconds_bucket should show values in the 5s bucket
```

### TEST 3 — Recovery

```bash
# Remove the toxic
curl -s -X DELETE \
  http://localhost:8474/proxies/payment/toxics/payment-latency

# Send request — should be fast again
curl -s http://localhost:8080/order
```

---

## Design decisions

- **SQLite** is used as the "database" — it is the simplest possible
  persistent store, requires no extra container, and is sufficient to
  demonstrate that Payment communicates with a database.
- **Toxiproxy** is seeded via a JSON config file so the `payment` proxy
  exists immediately on startup without any manual API call.
- The **payment proxy listen port (20001)** is not exposed to the host
  because it should only be reached through the internal Docker network.
- Services use **Flask + prometheus_client** — minimal, well-understood
  stack with zero configuration overhead.
