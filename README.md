# Nudgeline

Automated call workflows for businesses in the Gulf. When an event happens, such as a new cash-on-delivery order, the platform calls the customer in Arabic or English. The customer presses 1 to confirm or 2 to cancel, and the result is written back to the store.

- **First template:** COD order confirmation, with WhatsApp first and a call if there's no reply.
- **Integrations:** Shopify, or any store through a signed webhook.
- **Compliance:** calling windows in the customer's local time, a do-not-call list, and a stored decision for every dial.
- **Multi-tenant SaaS:** row-level security, and roles each tenant defines from a fixed permission list.
- **Self-hosted speech:** Chatterbox Multilingual for TTS and faster-whisper for STT.

## Run it locally

You need Docker with Compose v2, plus [uv](https://docs.astral.sh/uv/) and Node.js 22+ for development outside Docker.

```bash
make setup   # creates .env from .env.example and a self-signed certificate
make up      # postgres, migrations, api, worker, speech, web, nginx
```

Fill in `SECRET_KEY`, `ENCRYPTION_MASTER_KEY`, `POSTGRES_PASSWORD` and `APP_DB_PASSWORD` in `.env` before the first `make up`.

Open https://localhost and create an account. Then:

1. Create a workflow from the Order confirmation template and activate it.
2. Place a test call to your own number.

The dev profile uses a simulated phone line, so nothing is actually dialed. The number's last digits pick the outcome: `…00` no answer, `…01` busy, `…99` cancel, anything else confirms.

### Real calls and voices

| Need | How to set it up |
|---|---|
| Arabic and English voices | Set `SPEECH_WITH_MODELS=true` and `TTS_BACKEND=chatterbox`. A GPU is recommended. |
| Phone calls | Run `docker compose --profile voice up -d`. Set `TELEPHONY_BACKEND=livekit` and configure an outbound SIP trunk in LiveKit (`LIVEKIT_SIP_TRUNK_ID`). |

## Commands

| Command | What it does |
|---|---|
| `make up` / `make down` | Start or stop the dev stack |
| `make migrate` | Apply database migrations |
| `make lint` | Run ruff lint and format checks |
| `make typecheck` | Run mypy |
| `make test` | Run the test suite against Postgres (`TEST_DATABASE_URL`, or a local `pgserver`) |
| `make web` | Start the Next.js dev server on :3000 (proxies `/api` to :8000) |

## Layout

- `apps/api`: FastAPI app (auth, workflows, runs, integrations, webhooks)
- `apps/worker`: Postgres-backed job runner that moves each order through its workflow
- `apps/web`: Next.js dashboard in English and Arabic (RTL)
- `modules/*`: business modules split into `domain/`, `application/`, `ports/` and `adapters/`
- `services/speech`: self-hosted TTS/STT service

## License

Proprietary. All rights reserved.
