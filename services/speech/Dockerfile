# Self-hosted TTS/STT. Build with --build-arg WITH_MODELS=false for a light dev image
# that only serves the "tone" TTS backend (no model download, no torch).
FROM python:3.11-slim
ARG WITH_MODELS=true
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HF_HOME=/models
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY services/speech/requirements-base.txt services/speech/requirements-models.txt ./
RUN pip install --no-cache-dir -r requirements-base.txt \
 && if [ "$WITH_MODELS" = "true" ]; then pip install --no-cache-dir -r requirements-models.txt; fi
COPY services/speech/main.py ./main.py
RUN useradd -r -m -s /usr/sbin/nologin speech && mkdir -p /models && chown speech /models
USER speech
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
