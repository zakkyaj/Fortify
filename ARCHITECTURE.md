# FORTIFY Architecture

This document describes the system architecture, component responsibilities, communication flow, and deployment structure of FORTIFY.

---

# 1. System Overview

FORTIFY is a web-based architecture resilience testing platform.

It allows users to:

1. Design or visualize a distributed system.
2. Introduce controlled failures.
3. Observe system behavior.
4. Collect metrics and logs.
5. Analyze failures using AI.
6. Receive architecture improvement recommendations.
7. Re-test the architecture.
8. Compare before and after results.

The core workflow is:

```text
Architecture
     ↓
Attack
     ↓
Observe
     ↓
Diagnose
     ↓
Improve
     ↓
Re-test
```

---

# 2. High-Level Architecture

```text
                         ┌─────────────────────┐
                         │       Browser       │
                         │                     │
                         │  React Frontend     │
                         │  React Flow         │
                         └──────────┬──────────┘
                                    │
                              HTTP / JSON
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      FastAPI        │
                         │      Backend        │
                         │                     │
                         │   API + Orchestrator│
                         └──────────┬──────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
       ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
       │ Infrastructure │  │   Monitoring   │  │   AI Analyzer  │
       │                │  │                │  │                │
       │ Docker         │  │ Prometheus     │  │ LLM            │
       │ Toxiproxy      │  │ Metrics        │  │ Diagnosis      │
       │ k6             │  │ Logs           │  │ Recommendations│
       └───────┬────────┘  └───────┬────────┘  └────────────────┘
               │                   │
               ▼                   │
       ┌────────────────┐          │
       │ Test Services  │◄─────────┘
       │                │
       │ Gateway        │
       │ Order Service  │
       │ Payment        │
       │ Database       │
       └────────────────┘
```

---

# 3. Major Components

## 3.1 Frontend

Technology:

- React
- Vite
- React Flow
- Axios

The frontend is the main user interface.

Responsibilities:

```text
Architecture visualization
Architecture editing
Attack configuration
Experiment control
Live experiment status
Metrics visualization
AI diagnosis display
Recommendations
Before/after comparison
```

The frontend communicates with the backend through REST APIs.

It should not directly control Docker, Toxiproxy, Prometheus, or the AI provider.

---

# 3.2 Backend

Technology:

- Python
- FastAPI
- Pydantic

The backend is the central orchestrator of FORTIFY.

Responsibilities:

```text
API handling
Request validation
Architecture management
Experiment orchestration
Attack execution
Infrastructure communication
Metrics retrieval
AI communication
Result aggregation
```

The backend acts as the bridge between the frontend and the testing infrastructure.

---

# 3.3 Test Infrastructure

The infrastructure contains the system being tested.

Initial services:

```text
Gateway
   ↓
Order Service
   ↓
Payment Service
   ↓
Database
```

Each service should run as an isolated Docker container.

Example:

```text
┌───────────────┐
│    Gateway    │
└───────┬───────┘
        │
        ▼
┌───────────────┐
│ Order Service │
└───────┬───────┘
        │
        ▼
┌─────────────────┐
│ Payment Service │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Database     │
└─────────────────┘
```

---

# 3.4 Failure Injection

Technology:

- Toxiproxy
- Docker networking
- k6

Failure injection allows FORTIFY to intentionally create controlled failure conditions.

Initial failure scenarios:

```text
Latency
Service failure
Load / traffic spike
```

Example:

```text
Gateway
   ↓
Order Service
   ↓
Toxiproxy
   ↓
Payment Service

Toxiproxy introduces:

5 seconds latency
```

The goal is to reproduce realistic failure propagation in a controlled environment.

---

# 3.5 Monitoring

Technology:

- Prometheus

Monitoring collects information about the running system.

Important metrics:

```text
Request count
Requests per second
Average latency
P95 latency
Error rate
CPU usage
Memory usage
Service health
```

The backend retrieves the relevant metrics for an experiment.

---

# 3.6 AI Analyzer

The AI layer analyzes the architecture and experiment results.

Input:

```text
Architecture
+
Attack configuration
+
Metrics
+
Logs
+
Service relationships
```

Example input:

```json
{
  "target": "payment",
  "failure": {
    "type": "latency",
    "value": 5000
  },
  "metrics": {
    "order_latency_ms": 5800,
    "payment_latency_ms": 5200,
    "error_rate": 3.4
  }
}
```

Expected output:

```json
{
  "problem": "Payment latency is propagating to Order Service.",
  "severity": "high",
  "affected_services": [
    "payment",
    "order"
  ],
  "recommendation": "Introduce asynchronous processing."
}
```

The AI should return structured information that the backend can safely pass to the frontend.

---

# 4. Data Flow

## Normal Experiment

```text
User
 │
 │ Configure architecture
 ▼
Frontend
 │
 │ POST /api/architecture
 ▼
Backend
 │
 │ Create experiment environment
 ▼
Docker Services
```

---

## Failure Injection

```text
User
 │
 │ Select attack
 ▼
Frontend
 │
 │ POST /api/attacks
 ▼
Backend
 │
 │ Configure attack
 ▼
Toxiproxy / k6
 │
 ▼
Target Service
```

---

## Monitoring

```text
Test Services
      │
      ▼
Prometheus
      │
      ▼
Metrics
      │
      ▼
Backend
```

---

## AI Diagnosis

```text
Architecture
      +
Attack
      +
Metrics
      +
Logs
      │
      ▼
Backend
      │
      ▼
AI Analyzer
      │
      ▼
Diagnosis
      │
      ▼
Recommendation
      │
      ▼
Frontend
```

---

# 5. Complete End-to-End Flow

```text
┌──────────────────────────────────────────┐
│                 USER                     │
└────────────────────┬─────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────┐
│              React Frontend              │
│                                          │
│ Architecture → Attack → Results          │
└────────────────────┬─────────────────────┘
                     │
                     │ REST API
                     ▼
┌──────────────────────────────────────────┐
│             FastAPI Backend              │
│                                          │
│             Orchestrator                 │
└───────┬───────────────┬──────────────┬───┘
        │               │              │
        ▼               ▼              ▼
   Docker /         Monitoring       AI
   Toxiproxy        Prometheus      Analyzer
        │               │              │
        ▼               ▼              │
  Test Services      Metrics          │
        │               │              │
        └───────────────┴──────────────┘
                        │
                        ▼
                  Analysis Result
                        │
                        ▼
                 Recommendation
                        │
                        ▼
                    Re-test
                        │
                        ▼
                 Before / After
                        │
                        ▼
                     Frontend
```

---

# 6. Service Communication

## Frontend → Backend

Protocol:

```text
HTTP / REST
JSON
```

Example:

```text
POST /api/attacks
```

---

## Backend → Infrastructure

The backend controls the test environment through Docker and the relevant infrastructure interfaces.

Responsibilities include:

```text
Start services
Stop services
Configure failure
Run experiments
Collect results
```

---

## Infrastructure → Monitoring

Test services expose metrics that are collected by Prometheus.

```text
Services
   ↓
Metrics
   ↓
Prometheus
```

---

## Backend → AI

The backend sends a structured analysis request containing the required experiment information.

```text
Architecture
Attack
Metrics
Logs
     ↓
AI Analyzer
     ↓
Structured Diagnosis
```

---

# 7. Deployment Model

During development, FORTIFY can run locally:

```text
Developer Machine
│
├── React Development Server
│
├── FastAPI
│
└── Docker Desktop
    │
    ├── Gateway
    ├── Order Service
    ├── Payment Service
    ├── Database
    ├── Toxiproxy
    ├── Prometheus
    └── Other test components
```

Docker Compose should be used to simplify local environment setup.

Target command:

```bash
docker compose up --build
```

---

# 8. Network Model

The Docker environment should use an internal network for communication between services.

Example:

```text
fortify-network

Gateway
   │
   ▼
Order
   │
   ▼
Payment
   │
   ▼
Database
```

External access should be limited to the services that need to be accessed from the host machine.

---

# 9. Port Plan

Initial development ports:

| Component | Port |
|---|---:|
| Frontend | 5173 |
| Backend | 8000 |
| Prometheus | 9090 |
| Toxiproxy API | 8474 |

Additional service ports should be documented here when introduced.

Avoid unnecessary public port exposure for internal services.

---

# 10. Repository Mapping

```text
FORTIFY/
│
├── frontend/
│   └── React application
│
├── backend/
│   └── FastAPI application
│
├── services/
│   ├── gateway/
│   ├── order/
│   └── payment/
│
├── infrastructure/
│   └── Docker / Toxiproxy configuration
│
├── monitoring/
│   └── Prometheus configuration
│
├── tests/
│   └── k6 tests
│
├── docker-compose.yml
│
└── docs / markdown files
```

---

# 11. Separation of Responsibilities

The architecture intentionally separates responsibilities.

```text
Frontend
    ↓
Presentation + User Interaction

Backend
    ↓
Orchestration + API

Infrastructure
    ↓
System Under Test + Failure Injection

Monitoring
    ↓
System Measurements

AI
    ↓
Analysis + Recommendations
```

This separation allows the four team members to work independently while integrating through stable interfaces.

---

# 12. Integration Principle

The team should integrate continuously rather than waiting until the end.

The first integration milestone should be:

```text
React
  ↓
FastAPI
  ↓
Docker
  ↓
Gateway
  ↓
Order
  ↓
Payment
```

The second milestone:

```text
Payment
  ↓
Failure Injection
  ↓
Prometheus
  ↓
Metrics
```

The third milestone:

```text
Metrics
  ↓
AI
  ↓
Diagnosis
  ↓
Recommendation
```

The final milestone:

```text
Recommendation
  ↓
Re-test
  ↓
Before / After Comparison
  ↓
Frontend
```

---

# 13. MVP Architecture

For the hackathon MVP, prioritize one complete working path instead of many disconnected features.

```text
Architecture
     ↓
Payment Latency Attack
     ↓
Metrics Collection
     ↓
AI Diagnosis
     ↓
Architecture Recommendation
     ↓
Re-test
     ↓
Before / After Comparison
```

This vertical slice should work end-to-end before adding additional attack types.

---

# 14. Future Expansion

The architecture should allow additional components to be added later.

Potential additions:

```text
Additional failure types
Distributed tracing
Log aggregation
More microservices
Message queues
Caching
Circuit breakers
Authentication
Cloud deployment
Additional AI agents
Architecture simulation
Chaos experiments
```

These should be added without tightly coupling the frontend directly to infrastructure components.

---

# 15. Core Design Principle

FORTIFY follows this principle:

```text
                    ┌──────────────┐
                    │   Frontend   │
                    └──────┬───────┘
                           │
                     Stable API
                           │
                           ▼
                    ┌──────────────┐
                    │   Backend    │
                    └──────┬───────┘
                           │
                ┌──────────┼──────────┐
                ▼          ▼          ▼
          Infrastructure Monitoring   AI
```

The backend acts as the central integration layer.

The frontend should not directly control infrastructure.

Infrastructure should not depend on frontend implementation details.

AI should receive structured experiment data rather than directly controlling the user interface.

This separation keeps FORTIFY modular, testable, and easier for the team to develop collaboratively.
