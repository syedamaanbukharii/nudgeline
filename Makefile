.PHONY: setup certs up down logs migrate lint typecheck test web web-build

setup: certs
	cp -n .env.example .env || true

certs:
	python generate_cert.py

up:
	docker compose --profile dev up -d --build

down:
	docker compose --profile dev down

logs:
	docker compose --profile dev logs -f

migrate:
	docker compose --profile dev run --rm migrate

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy apps modules services

test:
	uv run pytest --cov=apps --cov=modules

web:
	cd apps/web && npm run dev

web-build:
	cd apps/web && npm ci && npm run build
