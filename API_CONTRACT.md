# FORTIFY API Contract

This document defines the communication contract between the FORTIFY frontend, backend, infrastructure, monitoring, and AI components.

The purpose of this document is to allow team members to develop components independently while ensuring that they integrate correctly.

---

# Base URL

During local development:

```text
http://localhost:8000/api
```

The frontend should use an environment variable instead of hardcoding the URL.

Example:

```env
VITE_API_URL=http://localhost:8000/api
```

---

# API Conventions

## Content Type

Requests containing JSON data must use:

```http
Content-Type: application/json
```

## Response Format

Successful responses should return JSON.

Errors should use a consistent structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```

---

# 1. Health Check

Used by the frontend and deployment environment to verify that the backend is available.

## Request

```http
GET /api/health
```

## Response

```json
{
  "status": "ok",
  "service": "fortify-backend"
}
```

---

# 2. Architecture

The frontend sends the architecture created by the user to the backend.

## Create Architecture

```http
POST /api/architecture
```

## Request

```json
{
  "name": "Order Processing System",
  "services": [
    {
      "id": "gateway",
      "name": "Gateway",
      "type": "gateway"
    },
    {
      "id": "order",
      "name": "Order Service",
      "type": "service"
    },
    {
      "id": "payment",
      "name": "Payment Service",
      "type": "service"
    },
    {
      "id": "database",
      "name": "Database",
      "type": "database"
    }
  ],
  "connections": [
    {
      "source": "gateway",
      "target": "order"
    },
    {
      "source": "order",
      "target": "payment"
    },
    {
      "source": "payment",
      "target": "database"
    }
  ]
}
```

## Response

```json
{
  "architecture_id": "arch_001",
  "status": "created"
}
```

---

# 3. Get Architecture

```http
GET /api/architecture/{architecture_id}
```

## Response

```json
{
  "architecture_id": "arch_001",
  "name": "Order Processing System",
  "services": [],
  "connections": []
}
```

---

# 4. Create Attack

This endpoint starts a controlled failure experiment.

```http
POST /api/attacks
```

## Request

```json
{
  "architecture_id": "arch_001",
  "target": "payment",
  "type": "latency",
  "value": 5000
}
```

## Supported Attack Types

Initial MVP:

```text
latency
service_failure
load
```

Additional attack types can be added later.

---

## Latency Attack

Example:

```json
{
  "architecture_id": "arch_001",
  "target": "payment",
  "type": "latency",
  "value": 5000
}
```

`value` represents milliseconds.

---

## Service Failure

```json
{
  "architecture_id": "arch_001",
  "target": "payment",
  "type": "service_failure",
  "value": true
}
```

---

## Load Attack

```json
{
  "architecture_id": "arch_001",
  "target": "gateway",
  "type": "load",
  "value": {
    "requests_per_second": 100,
    "duration": 30
  }
}
```

---

## Response

```json
{
  "attack_id": "atk_001",
  "status": "started",
  "target": "payment",
  "type": "latency"
}
```

---

# 5. Get Attack Status

```http
GET /api/attacks/{attack_id}
```

## Response

```json
{
  "attack_id": "atk_001",
  "status": "completed",
  "target": "payment",
  "type": "latency",
  "started_at": "2026-09-25T12:00:00Z",
  "completed_at": "2026-09-25T12:00:30Z"
}
```

Possible statuses:

```text
queued
running
completed
failed
cancelled
```

---

# 6. Get Metrics

Returns metrics collected during an experiment.

```http
GET /api/attacks/{attack_id}/metrics
```

## Response

```json
{
  "attack_id": "atk_001",
  "metrics": {
    "request_count": 1250,
    "requests_per_second": 41.6,
    "average_latency_ms": 5200,
    "p95_latency_ms": 6100,
    "error_rate": 3.4
  }
}
```

---

# 7. Get Service Metrics

For detailed service-level information:

```http
GET /api/metrics/{service_id}
```

## Response

```json
{
  "service": "payment",
  "cpu_usage": 72.4,
  "memory_usage": 64.2,
  "latency_ms": 5200,
  "error_rate": 3.4,
  "requests_per_second": 41.6
}
```

---

# 8. Run Diagnosis

Sends the experiment data to the AI analysis layer.

```http
POST /api/diagnosis
```

## Request

```json
{
  "attack_id": "atk_001"
}
```

The backend gathers:

```text
Architecture
+
Attack Configuration
+
Metrics
+
Logs
```

and sends the relevant information to the AI analyzer.

## Response

```json
{
  "diagnosis_id": "diag_001",
  "attack_id": "atk_001",
  "severity": "high",
  "problem": "Payment service latency is propagating to the Order Service.",
  "affected_services": [
    "payment",
    "order"
  ],
  "root_cause": "High latency introduced at the payment service."
}
```

---

# 9. Get Recommendation

Generate an architecture improvement recommendation.

```http
POST /api/recommendations
```

## Request

```json
{
  "diagnosis_id": "diag_001"
}
```

## Response

```json
{
  "recommendation_id": "rec_001",
  "strategy": "async-processing",
  "title": "Introduce asynchronous payment processing",
  "description": "Decouple order processing from payment response time by introducing asynchronous communication.",
  "expected_effect": {
    "latency": "lower",
    "resilience": "higher",
    "coupling": "lower"
  }
}
```

---

# 10. Re-test

Run the experiment again after applying or simulating an architectural improvement.

```http
POST /api/retest
```

## Request

```json
{
  "architecture_id": "arch_001",
  "previous_attack_id": "atk_001",
  "recommendation_id": "rec_001"
}
```

## Response

```json
{
  "retest_id": "retest_001",
  "status": "started"
}
```

---

# 11. Before / After Comparison

```http
GET /api/comparisons/{attack_id}
```

## Response

```json
{
  "before": {
    "average_latency_ms": 5200,
    "error_rate": 3.4
  },
  "after": {
    "average_latency_ms": 1400,
    "error_rate": 1.2
  },
  "metrics": {
    "latency_change_percent": -73.1,
    "error_rate_change_percent": -64.7
  }
}
```

---

# 12. Attack Lifecycle

The expected lifecycle is:

```text
Create Architecture
        ↓
Create Attack
        ↓
Attack Queued
        ↓
Attack Running
        ↓
Failure Injected
        ↓
Metrics Collected
        ↓
Attack Completed
        ↓
Diagnosis
        ↓
Recommendation
        ↓
Re-test
        ↓
Comparison
```

---

# 13. Frontend ↔ Backend Flow

The frontend should follow this sequence:

```text
User
 ↓
Create Architecture
 ↓
POST /architecture
 ↓
Receive architecture_id
 ↓
Configure Attack
 ↓
POST /attacks
 ↓
Receive attack_id
 ↓
Poll GET /attacks/{id}
 ↓
Attack completed
 ↓
GET /attacks/{id}/metrics
 ↓
POST /diagnosis
 ↓
POST /recommendations
 ↓
POST /retest
 ↓
GET /comparisons/{id}
 ↓
Display Results
```

---

# 14. Component Responsibilities

## Frontend

Responsible for:

```text
User interaction
Architecture visualization
Attack configuration
Metrics visualization
Diagnosis display
Recommendation display
Before/after comparison
```

The frontend communicates with the backend API.

---

## Backend

Responsible for:

```text
API
Request validation
Experiment orchestration
Docker communication
Attack execution
Metrics collection
AI communication
Result aggregation
```

---

## Infrastructure

Responsible for:

```text
Docker containers
Test services
Toxiproxy
k6
Service networking
Failure injection
```

---

## Monitoring

Responsible for:

```text
Metrics collection
Service health
Latency
Error rate
Throughput
Resource usage
```

---

## AI Analyzer

Responsible for:

```text
Architecture analysis
Failure analysis
Metric interpretation
Root-cause reasoning
Architecture recommendations
```

---

# 15. API Versioning

The initial version uses:

```text
/api
```

If breaking API changes are required in the future, use:

```text
/api/v2
```

Do not silently break existing endpoints used by the frontend.

---

# 16. Contract Change Rules

If an endpoint changes, the developer must:

1. Update this document.
2. Inform the affected team member.
3. Update the backend.
4. Update the frontend/client.
5. Test the integration.

Example:

```text
Backend changes:
POST /api/attacks
        ↓
Update API_CONTRACT.md
        ↓
Notify Frontend
        ↓
Update React API call
        ↓
Integration test
```

---

# 17. MVP API

For the initial hackathon version, prioritize these endpoints:

```text
GET  /api/health

POST /api/architecture
GET  /api/architecture/{id}

POST /api/attacks
GET  /api/attacks/{id}

GET  /api/attacks/{id}/metrics

POST /api/diagnosis
POST /api/recommendations

POST /api/retest

GET  /api/comparisons/{id}
```

Additional endpoints should only be added when required.

---

# ⚠️ Important

This document is the shared agreement between the frontend and backend teams.

If the implementation differs from this contract, update the contract and communicate the change before merging.

The goal is:

```text
Frontend
   ↓
Stable API Contract
   ↓
Backend
   ↓
Infrastructure
   ↓
Monitoring / AI
```

All components must follow the same contract.
