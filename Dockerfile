# YieldMind Agent Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY agent/requirements.txt .
COPY agent/ ./agent/

# Pin setuptools<70 — v71+ removed pkg_resources
RUN pip install --no-cache-dir --upgrade pip "setuptools<70" wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    python -c "import pkg_resources; print('pkg_resources OK')"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/agent

CMD ["python", "agent.py"]
