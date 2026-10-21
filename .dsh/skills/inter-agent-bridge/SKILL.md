---
name: inter-agent-bridge
description: >-
  Asynchronous technical coordination workflow between the Frontend Antigravity Agent
  and the Backend Antigravity Agent via bridge/agent_chat.log. Use when checking for updates
  from the backend agent, requesting new sensor endpoints, or registering cronjob requirements.
---

# Inter-Agent Bridge Coordination Workflow

This skill guides the Frontend Antigravity Agent in asynchronously collaborating with the peer Backend Antigravity Agent working on the server repository.

## 1. Bridge File Location & Invariants

- **Path**: `D:\project\tensurafrontend\bridge\agent_chat.log`
- **Rule**: **Append-Only**. Never overwrite or truncate previous lines.
- **Line Format**:
  ```text
  [YYYY-MM-DD HH:mm:ss][SENDER][TAG][#ID] Message content
  ```

---

## 2. Standard Message Protocol

### Senders:
- `[AGENT_FRONTEND]`: This agent (responsible for UI, Desktop app, Audio pipeline, MCP tools).
- `[AGENT_BACKEND]`: The peer agent (responsible for server, Docker, hardware sensors, cronjobs).

### Tags:
| Tag | Purpose | Example |
|---|---|---|
| `[SPEC_REQ]` | Request an API schema, sensor field, or cronjob | `[SPEC_REQ][#SEN-01] Requesting GPU temp & VRAM telemetry schema` |
| `[SPEC_RESP]` | Acknowledge and provide the requested implementation | `[SPEC_RESP][#SEN-01] Telemetry endpoint ready on port 8000 /api/metrics` |
| `[SYNC_NOTE]` | Announce architectural updates or changes | `[SYNC_NOTE][#ARCH-02] Switched TTS from VieNeu to Edge-TTS HoaiMy` |
| `[QUESTION]` | Clarify technical questions with the backend agent | `[QUESTION][#Q-01] Is the Redis cache container exposed on port 6379?` |

---

## 3. Standard Operational Procedure

### Step 1: Scan for Inbound Backend Messages
At the start of relevant tasks or before designing new telemetry integrations, inspect the tail of `bridge/agent_chat.log` for recent messages with `[AGENT_BACKEND]`:
```powershell
Get-Content -Path "bridge/agent_chat.log" -Tail 20
```

### Step 2: Post Inbound Technical Specification Requests
When the Frontend requires backend capabilities (e.g., a new sensor stream, a scheduled database vacuum, or a cron trigger):
1. Assign a correlation ID: `#REQ-YYYYMMDD-XX`
2. Append the request with specific payload requirements:
   ```text
   [YYYY-MM-DD HH:mm:ss][AGENT_FRONTEND][SPEC_REQ][#REQ-YYYYMMDD-01] Cần cung cấp định dạng JSON cho sensor: { cpu_usage, ram_mb, gpu_temp }.
   ```

### Step 3: Handle Backend Responses
When the backend agent replies with `[SPEC_RESP]` referencing the same ID:
1. Parse the schema details provided by the backend agent.
2. Implement the frontend consumer logic (UI gauge, state badge, or notification).
3. Post a closing acknowledgment:
   ```text
   [YYYY-MM-DD HH:mm:ss][AGENT_FRONTEND][SYNC_NOTE][#REQ-YYYYMMDD-01] Đã kết nối thành công dữ liệu sensor vào UI component.
   ```
