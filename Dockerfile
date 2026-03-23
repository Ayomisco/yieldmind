# YieldMind Agent Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY agent/requirements.txt .
COPY agent/ ./agent/
COPY .env.example .env.example

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Work from agent directory
WORKDIR /app/agent

# Run the agent
CMD ["python", "agent.py"]
