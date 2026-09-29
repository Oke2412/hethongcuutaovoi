# Dockerfile - Telegram Bot (long polling)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for ChromaDB and build tools
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Data directory for SQLite and scratch
RUN mkdir -p /app/data /app/scratch

CMD ["python", "-m", "bot.main"]
