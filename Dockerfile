# YieldMind Agent Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files first
COPY agent/requirements.txt .
COPY agent/ ./agent/

# Explicitly install setuptools and wheel FIRST
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir "setuptools>=65.0" "wheel"

# Install all requirements
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Work from agent directory
WORKDIR /app/agent

# Run the agent
CMD ["python", "agent.py"]
