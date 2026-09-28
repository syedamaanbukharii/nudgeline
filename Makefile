.PHONY: up down migrate lint typecheck test evals web logs reset-db shell

up:
	docker compose --profile dev up -d --build

down:
	docker compose --profile dev down

migrate:
	docker compose exec api alembic upgrade head

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy apps modules services

test:
	uv run pytest --cov

evals:
	@echo "Run evals locally: uv run pytest evals/"

web:
	cd apps/web && pnpm dev

logs:
	docker compose logs -f

reset-db:
	docker compose exec postgres dropdb -U nudgeline nudgeline || true
	docker compose exec postgres createdb -U nudgeline nudgeline

shell:
	docker compose exec api bash
