---
name: docker-homelab-devops
description: >-
  DevOps procedures, live-reload volume strategies, container healthcheck recovery,
  and network diagnostics for Docker Compose multi-service stacks (FastAPI, Telegram Bot,
  Neo4j, ChromaDB). Use this skill when deploying local containers, fixing slow Docker builds,
  configuring live-reload without image rebuilds, or troubleshooting container restarts.
---

# Docker Homelab & Stack DevOps Expert

This skill establishes best practices for running low-latency, self-healing Docker Compose stacks for AI agents, specifically preventing unnecessary Docker image rebuilds and diagnosing container networking.

---

## 1. Zero-Rebuild Live Reload Pattern (Volume Mounts)

> [!WARNING]
> Running `docker compose build` after every Python edit triggers `COPY requirements.txt` cache invalidation, forcing PyTorch (550MB+) and CUDA dependencies (>1.5GB) to re-download over the internet, wasting 10-20 minutes.

### The Solution: Direct Host-to-Container Volume Mounting
Mount active Python source directories directly into the container in `docker-compose.yml`:

```yaml
services:
  bot:
    build: .
    volumes:
      - ./data:/app/data                # Persist SQLite DB
      - ./data/chroma:/app/chroma_db    # Persist Vector Storage
      - ./core:/app/core                # Live code reload
      - ./bot:/app/bot                  # Live code reload
      - ./db:/app/db                    # Live code reload
      - ./config.py:/app/config.py      # Live config reload
```
**Result**: Any code edits in `./core`, `./bot`, or `./db` take effect immediately without building or restarting the container.

---

## 2. Service Dependency & Healthcheck Synchronization

Neo4j and vector databases take 15-30 seconds to initialize plugins (APOC, GDS). Never start bot or API services before the database is ready:

```yaml
services:
  neo4j:
    image: neo4j:5.12
    healthcheck:
      test: ["CMD-SHELL", "cypher-shell -u neo4j -p password 'RETURN 1'"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  api:
    depends_on:
      neo4j:
        condition: service_healthy
```

---

## 3. Network URI Resolution (Host vs Docker Internal)

| Context | Neo4j Bolt URI | FastAPI Host Port |
|---|---|---|
| **Inside Docker Containers** (`bot`, `api`) | `bolt://neo4j:7687` | `http://api:8000` |
| **Outside Docker (Host Windows, Tests)** | `bolt://localhost:7687` | `http://localhost:8000` |
| **Tailscale Remote Client** | N/A (firewalled) | `http://<tailscale-ip>:8000` |

---

## 4. Rapid Troubleshooting Runbook

1. **Check container status and health**:
   ```bash
   docker compose ps
   ```

2. **Inspect live crash logs**:
   ```bash
   docker compose logs --tail=100 bot
   docker compose logs --tail=100 api
   ```

3. **Restart single service without rebuilding**:
   ```bash
   docker compose restart bot
   ```
