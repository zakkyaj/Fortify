# FORTIFY Environment Variables

Copy this file to `.env` for local development:

```bash
cp .env.example .env
```

> Never commit `.env` or real API keys/secrets to GitHub.

## Frontend

```env
VITE_API_URL=http://localhost:8000/api
```

## Backend

```env
BACKEND_URL=http://localhost:8000
```

## Monitoring

```env
PROMETHEUS_URL=http://localhost:9090
```

## Failure Injection

```env
TOXIPROXY_URL=http://localhost:8474
```

## AI

Add your AI provider key only in your local `.env`:

```env
OPENAI_API_KEY=
```

Leave the value empty in `.env.example`.

## Local Services

| Service | Default URL |
|---|---|
| React / Vite | `http://localhost:5173` |
| FastAPI | `http://localhost:8000` |
| Prometheus | `http://localhost:9090` |
| Toxiproxy | `http://localhost:8474` |

## Important

- `.env.example` is safe to commit.
- `.env` is local-only and ignored by Git.
- Never put passwords, API keys, tokens, or other secrets in this file.
- If a new environment variable is required, add its placeholder to `.env.example` and document it here.
