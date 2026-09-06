# Dockerfile — Telegram Bot (long polling)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for ChromaDB\nRUN apt-get update && apt-get install -y build-essential gcc && rm -rf /var/lib/apt/lists/*\n\n# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Data directory for SQLite
RUN mkdir -p /app/data

CMD ["python", "-m", "bot.main"]
