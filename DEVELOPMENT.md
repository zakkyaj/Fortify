# FORTIFY Development Guide

This document explains how to set up, run, develop, test, and integrate FORTIFY locally.

The goal is to make it possible for every team member to clone the repository and start working without manually guessing the project configuration.

---

# 1. Prerequisites

Install the following:

- Git
- Docker Desktop
- Docker Compose
- Node.js
- Python 3
- WSL 2 on Windows

Verify the installation:

```bash
git --version
docker --version
docker compose version
node --version
python --version
wsl --version
```

Docker Desktop must be running before starting the containerized parts of FORTIFY.

---

# 2. Clone the Repository

Clone the repository:

```bash
git clone <REPOSITORY_URL>
```

Enter the project:

```bash
cd FORTIFY
```

Check the remote:

```bash
git remote -v
```

---

# 3. Create the Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

On Windows PowerShell, if required:

```powershell
Copy-Item .env.example .env
```

Never commit the real `.env` file.

---

# 4. Project Structure

The main project structure is:

```text
FORTIFY/
│
├── frontend/
├── backend/
├── services/
├── infrastructure/
├── monitoring/
├── tests/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── README.md
├── CONTRIBUTING.md
├── API_CONTRACT.md
├── ARCHITECTURE.md
└── DEVELOPMENT.md
```

---

# 5. Frontend Development

The frontend uses React and Vite.

Enter the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend should normally be available at:

```text
http://localhost:5173
```

Build the frontend:

```bash
npm run build
```

Preview a production build:

```bash
npm run preview
```

---

# 6. Backend Development

The backend uses Python and FastAPI.

Enter the backend directory:

```bash
cd backend
```

Create a virtual environment if one does not already exist:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Activate it on Linux/WSL:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The backend should normally be available at:

```text
http://localhost:8000
```

FastAPI documentation should be available at:

```text
http://localhost:8000/docs
```

---

# 7. Running the Backend Without Docker

During backend development, the FastAPI server can be run directly:

```bash
uvicorn app.main:app --reload
```

This is useful when working only on:

- API endpoints
- Request validation
- Business logic
- AI integration
- Backend testing

Docker should be used when testing the complete FORTIFY environment.

---

# 8. Docker Development

Make sure Docker Desktop is running.

From the project root:

```bash
docker compose up --build
```

To run in detached mode:

```bash
docker compose up --build -d
```

View running containers:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs
```

View logs for one service:

```bash
docker compose logs <service-name>
```

Follow logs:

```bash
docker compose logs -f <service-name>
```

Stop the environment:

```bash
docker compose down
```

Stop and remove containers:

```bash
docker compose down
```

Rebuild a service:

```bash
docker compose build <service-name>
```

---

# 9. Initial Development Environment

The target local environment is:

```text
Developer Machine
│
├── React
│   └── localhost:5173
│
├── FastAPI
│   └── localhost:8000
│
└── Docker Desktop
    │
    ├── Gateway
    ├── Order Service
    ├── Payment Service
    ├── Database
    ├── Toxiproxy
    └── Prometheus
```

The exact service list may expand as FORTIFY develops.

---

# 10. Frontend ↔ Backend Connection

The frontend communicates with FastAPI through the API defined in:

```text
API_CONTRACT.md
```

Frontend environment variable:

```env
VITE_API_URL=http://localhost:8000/api
```

Example frontend request:

```javascript
const response = await axios.post(
  `${import.meta.env.VITE_API_URL}/attacks`,
  {
    architecture_id: "arch_001",
    target: "payment",
    type: "latency",
    value: 5000
  }
);
```

Do not hardcode backend URLs throughout the frontend code.

---

# 11. CORS

During local development, the backend must allow the frontend development origin.

Expected frontend origin:

```text
http://localhost:5173
```

FastAPI should configure CORS appropriately.

Example:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Do not use unrestricted CORS in a production deployment without understanding the security implications.

---

# 12. Infrastructure Development

Infrastructure contains the services being tested by FORTIFY.

Initial architecture:

```text
Gateway
   ↓
Order Service
   ↓
Payment Service
   ↓
Database
```

Each service should have a clear responsibility and stable service name.

The infrastructure configuration should be reproducible through Docker Compose.

---

# 13. Failure Injection

The initial MVP should prioritize one failure scenario:

```text
Target:
payment-service

Failure:
5 second latency
```

Example flow:

```text
Gateway
   ↓
Order
   ↓
Toxiproxy
   ↓
Payment
```

Toxiproxy introduces the controlled network failure.

After the basic latency experiment works, additional failure scenarios can be implemented.

---

# 14. Load Testing

k6 is used for controlled traffic generation.

Example:

```text
k6
 ↓
Gateway
 ↓
Order
 ↓
Payment
```

The initial test should use a small controlled workload.

Example parameters:

```text
Requests per second: 100
Duration: 30 seconds
```

Do not start with unnecessarily large workloads on a development laptop.

---

# 15. Monitoring

Prometheus collects metrics from the test environment.

Important metrics include:

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

The monitoring configuration belongs under:

```text
monitoring/
```

Prometheus is expected to run on:

```text
http://localhost:9090
```

---

# 16. AI Development

The AI analyzer should receive structured information from the backend.

Example:

```json
{
  "architecture": {},
  "attack": {
    "target": "payment",
    "type": "latency",
    "value": 5000
  },
  "metrics": {
    "average_latency_ms": 5200,
    "error_rate": 3.4
  }
}
```

The AI should return structured output.

Example:

```json
{
  "problem": "Payment latency is affecting Order Service.",
  "severity": "high",
  "recommendation": "Introduce asynchronous processing."
}
```

Keep the AI interface independent from the React UI.

---

# 17. Running Tests

Before creating a Pull Request, test the component you changed.

Frontend:

```bash
npm run build
```

Backend:

```bash
pytest
```

If tests have not yet been implemented, at minimum verify that the application starts correctly.

For the complete system:

```bash
docker compose up --build
```

Then verify the main FORTIFY workflow.

---

# 18. MVP Integration Test

The first complete test should follow:

```text
Create Architecture
        ↓
Start Test Services
        ↓
Inject Payment Latency
        ↓
Generate Traffic
        ↓
Collect Metrics
        ↓
Run AI Diagnosis
        ↓
Generate Recommendation
        ↓
Re-test
        ↓
Compare Results
```

This complete path is more important than having many partially implemented features.

---

# 19. Git Development Workflow

Before starting a new task:

```bash
git checkout main
git pull origin main
```

Create a feature branch:

```bash
git checkout -b feature/your-feature
```

Work on the feature.

Check changes:

```bash
git status
git diff
```

Commit:

```bash
git add .
git commit -m "feat: describe the change"
```

Push:

```bash
git push -u origin feature/your-feature
```

Then create a Pull Request on GitHub.

Follow:

```text
CONTRIBUTING.md
```

for the complete team workflow.

---

# 20. Recommended Branches

Initial team branches:

```text
main
│
├── feature/frontend
├── feature/backend
├── feature/infrastructure
└── feature/ai
```

For specific work, use more descriptive branches:

```text
feature/frontend-canvas
feature/backend-attack-api
feature/toxiproxy-latency
feature/ai-diagnosis
```

---

# 21. Environment Variables

Never commit secrets.

Use:

```text
.env.example
```

to document required variables.

Example:

```env
VITE_API_URL=http://localhost:8000/api
OPENAI_API_KEY=
PROMETHEUS_URL=http://localhost:9090
```

Actual values belong in the developer's local `.env`.

---

# 22. Common Problems

## Docker command fails

Make sure Docker Desktop is running:

```bash
docker info
```

If the command fails, start Docker Desktop and try again.

---

## Frontend cannot reach backend

Check:

```text
Frontend:
http://localhost:5173

Backend:
http://localhost:8000
```

Check the API:

```text
http://localhost:8000/docs
```

Then verify:

- Backend is running.
- `VITE_API_URL` is correct.
- CORS is configured.
- The endpoint matches `API_CONTRACT.md`.

---

## Port already in use

Check the process using the port.

Windows:

```powershell
netstat -ano | findstr :8000
```

Or change the development port if necessary.

Do not randomly change ports without updating the relevant configuration.

---

## Docker service is not starting

Check:

```bash
docker compose ps
```

Then:

```bash
docker compose logs <service-name>
```

---

# 23. Development Order

The recommended implementation order is:

### Phase 1 — Foundation

```text
Repository
   ↓
Frontend
   ↓
Backend
   ↓
Docker
```

### Phase 2 — Basic System

```text
Gateway
   ↓
Order
   ↓
Payment
   ↓
Database
```

### Phase 3 — Failure Testing

```text
Toxiproxy
   ↓
Latency Attack
```

### Phase 4 — Monitoring

```text
Prometheus
   ↓
Metrics
```

### Phase 5 — AI

```text
Metrics
+
Architecture
+
Attack
   ↓
AI Diagnosis
```

### Phase 6 — Improvement

```text
Recommendation
   ↓
Architecture Change
   ↓
Re-test
```

### Phase 7 — UI Polish

Only after the complete workflow works:

```text
Dashboard
Charts
Animations
Visual polish
Demo experience
```

---

# 24. First Integration Milestone

The team should first make this work:

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

Once this works, continue to failure injection and monitoring.

Do not wait until every individual feature is finished before integrating.

---

# 25. Definition of Done

A feature is considered complete when:

```text
Code implemented
      ↓
Locally tested
      ↓
No secrets committed
      ↓
Documentation updated if necessary
      ↓
Feature branch pushed
      ↓
Pull Request created
      ↓
Integration verified
```

A feature should not be considered complete simply because the code was written.

---

# 26. Hackathon Priority

If time becomes limited, prioritize in this order:

```text
1. End-to-end working flow
2. Failure injection
3. Metrics
4. AI diagnosis
5. Recommendation
6. Before/after comparison
7. UI polish
8. Additional attack types
```

A smaller working FORTIFY system is preferable to a large system with disconnected features.

---

# 27. Core Development Principle

Build and integrate continuously.

```text
Build
 ↓
Run
 ↓
Test
 ↓
Integrate
 ↓
Verify
 ↓
Improve
```

The goal is to keep `main` in a runnable state throughout development.
