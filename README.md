# FORTIFY

> **AI-Powered Architecture Resilience & Failure Testing Platform**

FORTIFY is a web-based platform for **designing, testing, and analyzing distributed system architectures under controlled failure conditions**.

Instead of discovering weaknesses after a production incident, FORTIFY lets engineering teams **intentionally break parts of an architecture, observe how the system reacts, identify failure propagation and likely root causes, and use AI-assisted analysis to improve resilience**.

### Core Workflow

**Architecture → Attack → Observe → Diagnose → Improve → Re-test**

---

## What FORTIFY Does

FORTIFY turns architecture resilience testing into a repeatable engineering workflow.

### 1. Design

Create or visualize a distributed system architecture using an interactive service graph.

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
                 ┌───────────────┐
                 │    Payment    │
                 │    Service    │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │   Database    │
                 └───────────────┘
```

Define services, dependencies, communication paths, and critical system components.

### 2. Attack

Introduce controlled failures into selected components.

Examples include:

- Service crashes
- Increased latency
- Network failures
- Dependency failures
- Database unavailability
- Resource exhaustion
- Intermittent failures

The objective is not to cause uncontrolled damage, but to create **repeatable failure scenarios** that reveal architectural weaknesses.

### 3. Observe

Monitor how the architecture behaves during the experiment.

FORTIFY can capture signals such as:

- Service health
- Request failures
- Latency changes
- Error propagation
- Dependency impact
- Recovery behavior
- Cascading failures

This creates an observable picture of how a localized failure affects the wider system.

### 4. Diagnose

Analyze the collected behavior to identify:

- The initial failure point
- Failure propagation paths
- Affected services
- Critical dependencies
- Potential bottlenecks
- Likely root causes
- Resilience gaps

FORTIFY focuses on connecting **what failed** with **why the failure spread**.

### 5. Improve

Use AI-assisted analysis to generate architecture improvement recommendations.

Recommendations may involve:

- Retry strategies
- Timeouts
- Circuit breakers
- Redundancy
- Failover mechanisms
- Load balancing
- Dependency isolation
- Caching
- Resource limits
- Graceful degradation

Recommendations are presented as engineering insights rather than replacing human architectural decisions.

### 6. Re-test

Apply the proposed improvements and run the failure scenario again.

The goal is to compare system behavior before and after the changes and determine whether the architecture became more resilient.

---

## Why FORTIFY?

Modern distributed systems are designed to remain available even when individual components fail.

But architectural resilience is difficult to validate through normal development and testing alone.

FORTIFY provides a controlled environment to answer questions such as:

> **What happens if this service goes down?**

> **How far does the failure propagate?**

> **Which dependency becomes the bottleneck?**

> **Can the system recover automatically?**

> **What architectural changes could reduce the impact?**

Instead of waiting for real-world incidents to expose these weaknesses, FORTIFY makes failure testing **intentional, observable, and repeatable**.

---

## Architecture Resilience Loop

```text
        ┌──────────────┐
        │   DESIGN     │
        │ Architecture │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │    ATTACK    │
        │   Failure    │
        │  Injection   │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │   OBSERVE    │
        │   Metrics &  │
        │    Events    │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │   DIAGNOSE   │
        │ Root Cause & │
        │ Propagation  │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │   IMPROVE    │
        │ AI-Assisted  │
        │ Recommendations│
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │   RE-TEST    │
        │ Validate the │
        │ Improvement  │
        └──────┬───────┘
               │
               └──────────────► DESIGN
```

---

## Key Capabilities

| Capability | Purpose |
|---|---|
| **Architecture Designer** | Model distributed services and dependencies |
| **Failure Injection** | Introduce controlled faults into components |
| **Experiment Runner** | Execute repeatable resilience experiments |
| **Live Observability** | Track system behavior during failures |
| **Failure Analysis** | Identify propagation paths and affected components |
| **Root Cause Analysis** | Connect observed symptoms to likely failure sources |
| **AI Diagnostics** | Generate context-aware engineering insights |
| **Resilience Recommendations** | Suggest architectural improvements |
| **Re-testing** | Validate whether changes improve resilience |
| **Experiment History** | Compare previous tests and results |

---

## Example Scenario

Consider an architecture:

```text
Client
  │
  ▼
API Gateway
  │
  ├──────────────► Order Service
  │                      │
  │                      ▼
  │                Payment Service
  │                      │
  │                      ▼
  │                  Database
  │
  └──────────────► Notification Service
```

FORTIFY can simulate a **Payment Service failure**.

The platform observes:

```text
Payment Service
      │
      ▼
Order Service
      │
      ▼
API Gateway
      │
      ▼
Client Requests
```

The system can then analyze whether:

- Requests fail immediately
- Retries amplify traffic
- Timeouts propagate upstream
- Other services remain available
- A circuit breaker prevents cascading failure
- The architecture supports graceful degradation

The experiment can then be repeated after applying an architectural improvement.

---

## AI-Assisted Analysis

FORTIFY uses AI to help transform raw experiment data into actionable engineering context.

A diagnostic flow can look like:

```text
Failure Event
     ↓
Affected Service
     ↓
Dependency Graph
     ↓
Observed Metrics
     ↓
Failure Propagation
     ↓
Likely Root Cause
     ↓
Resilience Gap
     ↓
Suggested Improvement
     ↓
Re-test
```

The AI layer is intended to **assist engineers**, not operate as an unquestionable authority. Recommendations should be validated against the actual architecture, workload, and operational requirements.

---

## Design Principles

FORTIFY is built around several principles:

- **Controlled failure** — experiments should be intentional and bounded.
- **Observability first** — failures are only useful when their effects can be measured.
- **Repeatability** — experiments should be reproducible under comparable conditions.
- **Evidence-driven diagnosis** — recommendations should be grounded in observed behavior.
- **Human-in-the-loop AI** — engineers remain responsible for architectural decisions.
- **Resilience over reaction** — identify weaknesses before they become production incidents.

---

## Project Vision

FORTIFY aims to make resilience engineering more accessible by bringing **architecture modeling, failure testing, observability, diagnosis, and AI-assisted improvement into a single workflow**.

The long-term goal is simple:

> **Don't wait for your architecture to fail. Test how it fails.**

---

## Status

FORTIFY is currently under active development.

The platform is being built around the idea of turning distributed-system failure testing into a practical, visual, and repeatable engineering workflow.

---

## License

This project is currently under development. License information will be added as the project matures.
