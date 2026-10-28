# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.12
ARG DENO_VERSION=2.1.4

# ---------------------------------------------------------------------------------------------------
# Builder: resolve and install Python dependencies into an isolated virtualenv.
# ---------------------------------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /src
# Dependencies only (resolved from pyproject metadata with stub packages), so this layer is cached
# across source changes. The application itself runs from /app, not from site-packages.
COPY pyproject.toml README.md ./
RUN mkdir -p core bots && touch core/__init__.py bots/__init__.py \
    && pip install --upgrade pip \
    && pip install . \
    && pip uninstall -y "$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['name'])")"

# ---------------------------------------------------------------------------------------------------
# Deno binary (JavaScript runtime used by yt-dlp's YouTube challenge solver), pinned.
# ---------------------------------------------------------------------------------------------------
FROM denoland/deno:bin-${DENO_VERSION} AS deno

# ---------------------------------------------------------------------------------------------------
# Runtime image
# ---------------------------------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg tini ca-certificates \
        fonts-noto-core fonts-dejavu-core tesseract-ocr tesseract-ocr-eng tesseract-ocr-ara \
    && rm -rf /var/lib/apt/lists/*

COPY --from=deno /deno /usr/local/bin/deno
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATA_DIR=/app/data

WORKDIR /app
COPY --chown=1000:1000 core/ core/
COPY --chown=1000:1000 bots/ bots/
COPY --chown=1000:1000 alembic.ini ./

# Non-root user owning every writable path (named volumes inherit this ownership on first mount).
RUN useradd -u 1000 -m -s /usr/sbin/nologin appuser \
    && for bot in bots/*/; do \
         slug="$(basename "$bot")"; \
         case "$slug" in _*|.*) continue;; esac; \
         mkdir -p "/app/data/$slug/downloads" "/app/data/$slug/public" "/app/data/$slug/cookies"; \
       done \
    && chown -R appuser:appuser /app/data

USER appuser

# tini reaps zombies (ffmpeg/yt-dlp children) and forwards SIGTERM so shutdown is graceful.
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "core", "gateway"]
