# Contributing to FORTIFY

This document defines the development and Git workflow for the FORTIFY team.

The goal is to allow all team members to work independently while keeping the `main` branch stable and ensuring that all components integrate correctly.

---

# 👥 Team Structure

FORTIFY is developed by four team members.

Suggested ownership:

| Area | Responsibility |
|---|---|
| Frontend | React UI, React Flow, dashboard |
| Backend | FastAPI, API endpoints, orchestration |
| Infrastructure | Docker, services, failure injection, k6 |
| AI & Monitoring | AI analysis, Prometheus, metrics |

Ownership does not prevent team members from helping each other.

---

# 🌿 Branch Strategy

The `main` branch contains the integrated version of FORTIFY.

Do not directly develop on `main`.

Recommended branches:

```text
main
│
├── feature/frontend
├── feature/backend
├── feature/infrastructure
└── feature/ai
```

For larger tasks, create more specific branches:

```text
feature/frontend-dashboard
feature/backend-attack-api
feature/infrastructure-toxiproxy
feature/ai-diagnosis
```

---

# 🔄 Development Workflow

Before starting work:

```bash
git checkout main
git pull origin main
```

Create a feature branch:

```bash
git checkout -b feature/your-feature
```

Work on your changes, then:

```bash
git add .
git commit -m "feat: describe your change"
git push -u origin feature/your-feature
```

Open a Pull Request on GitHub.

After review and approval, merge the Pull Request into `main`.

---

# 🔀 Pull Requests

Every significant change should go through a Pull Request.

A Pull Request should:

- Have a clear title
- Explain what was changed
- Mention related issues when applicable
- Be tested before submission
- Avoid unrelated changes

Example:

```text
feat: add latency attack endpoint
```

---

# 📝 Commit Convention

Use clear commit prefixes:

| Prefix | Usage |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation |
| `refactor:` | Code restructuring |
| `test:` | Tests |
| `chore:` | Configuration or maintenance |

Examples:

```bash
git commit -m "feat: add architecture upload API"
git commit -m "fix: resolve attack status error"
git commit -m "docs: update API contract"
```

---

# ⚠️ Main Branch Rules

Do not:

```bash
git push origin main
```

for normal development work.

Do not use:

```bash
git push --force
```

on shared branches unless the team explicitly agrees.

The `main` branch should always represent a working integrated version.

---

# 🔐 Secrets

Never commit:

```text
.env
API keys
passwords
tokens
private keys
credentials
```

Use `.env.example` to document required environment variables without exposing real secrets.

---

# 🧩 API Contract

Frontend and backend must follow `API_CONTRACT.md`.

If an endpoint changes:

1. Update the API implementation.
2. Update `API_CONTRACT.md`.
3. Inform the frontend/backend team member.
4. Test the integration.

Do not silently change request or response formats.

---

# 🏗️ File Ownership

Recommended ownership:

```text
frontend/          → Frontend developer
backend/           → Backend developer
infrastructure/    → Infrastructure developer
monitoring/        → AI & Monitoring developer
```

Team members may modify another area when required, but should communicate major cross-component changes.

---

# 🔧 Integration

FORTIFY components should be integrated progressively.

Recommended order:

```text
React Frontend
      ↓
FastAPI Backend
      ↓
Docker Test Services
      ↓
Failure Injection
      ↓
Prometheus Metrics
      ↓
AI Diagnosis
      ↓
Retest & Comparison
```

Do not wait until the end of the hackathon to integrate all components.

---

# 🧪 Testing

Before opening a Pull Request:

```bash
# Backend
pytest

# Frontend
npm run build
```

Also verify that the affected feature works with the rest of the system.

---

# 🌳 Keeping Your Branch Updated

Before starting new work, update your local `main`:

```bash
git checkout main
git pull origin main
```

Then update your feature branch:

```bash
git checkout feature/your-feature
git merge main
```

Resolve conflicts carefully if they occur.

---

# ⚔️ Merge Conflicts

If Git reports conflicts:

1. Open the conflicted files.
2. Decide which changes should remain.
3. Remove conflict markers.
4. Test the project.
5. Stage the resolved files.

```bash
git add .
git commit
```

Never blindly choose one side of a conflict without understanding the changes.

---

# 🚀 Definition of Done

A feature is considered complete when:

- Code is implemented
- Relevant tests pass
- API contracts are updated if necessary
- Documentation is updated if necessary
- The feature works with related components
- Pull Request is reviewed
- Pull Request is merged into `main`

---

# 🏁 Hackathon Priority

During the hackathon, prioritize the working MVP over unnecessary complexity.

Core FORTIFY flow:

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

Build and integrate this flow before adding advanced features.
