FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml .
RUN uv sync --no-install-project --no-dev
COPY services/stt/ services/stt/
RUN uv sync --no-dev

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app /app
RUN useradd -r -s /usr/sbin/nologin appuser && chown -R appuser:appuser /app
USER appuser
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 9000
CMD ["uvicorn", "services.stt.main:app", "--host", "0.0.0.0", "--port", "9000"]
