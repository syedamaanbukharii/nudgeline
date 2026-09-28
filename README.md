# Nudgeline

Multi-tenant AI voice agent that calls leads, books meetings, sets callback reminders, drafts follow-up emails, and writes results back to your CRM.

Built with Llama.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Node.js](https://nodejs.org/) 22+ and [pnpm](https://pnpm.io/) 9+
- [mkcert](https://github.com/FiloSottile/mkcert) (for local TLS certificates)

## Quick start

```bash
# 1. Clone and set up git hooks
bash setup.sh

# 2. Generate local TLS certificates
mkcert -install
mkcert -cert-file infra/nginx/certs/local.pem -key-file infra/nginx/certs/local-key.pem localhost 127.0.0.1

# 3. Copy and fill environment variables
cp .env.example .env

# 4. Start all services
make up

# 5. Run database migrations
make migrate

# 6. Open the app
# API:  https://localhost/api/healthz
# Web:  https://localhost
# Docs: https://localhost/api/docs (when ENABLE_API_DOCS=true)
```

## Commands

| Command | Description |
|---------|-------------|
| `make up` | Start all services (dev profile) |
| `make down` | Stop all services |
| `make migrate` | Run Alembic migrations |
| `make lint` | Run ruff linter and formatter check |
| `make typecheck` | Run mypy type checking |
| `make test` | Run pytest test suite |
| `make web` | Start Next.js dev server |
| `make logs` | Follow Docker Compose logs |

## Architecture

Modular monolith with four application entry points:

- **apps/api** — FastAPI REST API
- **apps/job_worker** — arq background workers (dispatch, post-call, bulk)
- **apps/voice_worker** — LiveKit Agents voice pipeline
- **apps/web** — Next.js frontend

Business modules under `modules/` follow ports-and-adapters: `domain/` (pure logic), `application/` (use cases), `ports/` (interfaces), `adapters/` (implementations).

Speech services under `services/`:
- **services/stt** — faster-whisper speech-to-text
- **services/tts** — Kokoro text-to-speech

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, arq |
| Database | PostgreSQL 16 + pgvector, PgBouncer, Valkey |
| Auth | Keycloak (OIDC/SAML SSO) |
| Voice | LiveKit + SIP, faster-whisper, Kokoro, Silero VAD |
| LLMs | Groq (Llama), Ollama/vLLM (Qwen), Gemini (evals only) |
| Frontend | Next.js, TypeScript, Tailwind, shadcn/ui |
| Infra | Nginx, Docker Compose, Prometheus, Grafana, Loki |

## License

Proprietary. All rights reserved.
# nudgeline
