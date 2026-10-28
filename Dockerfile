# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Writing Pulse: Agentic AI Blogging Assistant
# Target: IBM Cloud Code Engine (containerised Streamlit app)
#
# Build:  docker build -t writing-pulse .
# Run:    docker run -p 8501:8501 --env-file .env writing-pulse
# ─────────────────────────────────────────────────────────────────────────────

# Use the official slim Python 3.11 image (compatible with IBM Cloud Code Engine)
FROM python:3.11-slim

# Metadata labels (IBM Cloud best practice)
LABEL maintainer="mdivate"
LABEL app="writing-pulse"
LABEL version="2.0.0"
LABEL description="Writing Pulse — Agentic AI Blogging Assistant powered by IBM Granite"

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# ── Create non-root user (IBM Cloud security best practice) ──────────────────
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app

# ── Copy dependency spec first (layer caching) ───────────────────────────────
COPY requirements.txt ./

# ── Install Python dependencies ───────────────────────────────────────────────
RUN pip install --upgrade pip --quiet \
    && pip install --no-cache-dir -r requirements.txt

# ── Copy application source ───────────────────────────────────────────────────
COPY . .

# ── Streamlit configuration directory ────────────────────────────────────────
RUN mkdir -p .streamlit

# ── Set ownership to non-root user ────────────────────────────────────────────
RUN chown -R appuser:appuser /app
USER appuser

# ── IBM Cloud Code Engine: port 8080 (required) / Streamlit default: 8501 ───
# Code Engine maps external HTTPS → internal container port.
# We configure Streamlit to listen on 8080 via .streamlit/config.toml.
EXPOSE 8080

# ── Health check ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# ── Entrypoint (port 8080 required by IBM Cloud Code Engine) ─────────────────
ENTRYPOINT ["streamlit", "run", "app.py", \
            "--server.port=8080", \
            "--server.address=0.0.0.0", \
            "--server.headless=true"]
