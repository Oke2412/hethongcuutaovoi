---
name: web-search
description: >-
  Real-time web search, URL content extraction, technical documentation lookup, and multi-provider
  research (Tavily, Exa, Brave, DuckDuckGo) for the Tensura Raphael desktop companion and agentic
  ecosystem. Use this skill when verifying technical documentation, evaluating MCP servers,
  searching open-source skills, investigating API updates, or retrieving external web intelligence.
allowed-tools: Bash(*)
---

# Web Search & Intelligence Gathering Skill

This skill equips agents in the **Tensura Raphael OS** ecosystem (Desktop Companion & Server Backend) with real-time web search, technical research, and content extraction capabilities across multiple search engines and Model Context Protocol (MCP) servers.

---

## 1. Quick Start & Execution Modes

### Mode A: Built-in Python Search Utility (Zero External Dependency)
Execute direct web queries without installing third-party CLIs or extra pip packages:
```bash
python D:/project/tensurafrontend/.agents/skills/web-search/scripts/search.py "Tauri v2 window state management" --max-results 5
```
* **DuckDuckGo Lite Engine**: Default zero-config fallback via `lite.duckduckgo.com` with URL redirect unquoting and safe UTF-8 terminal handling on Windows. Completely free, no API key required, no CAPTCHA blockage.
* **Tavily AI Engine**: Activated automatically if `TAVILY_API_KEY` is present in the environment for advanced neural search and direct synthesis.

### Mode B: Inference.sh CLI (`belt`)
If `belt` CLI is installed (`npx.cmd skills add belt-sh/cli` on Windows):
```bash
# Search using Tavily Search Assistant
belt app run tavily/search-assistant --input '{"query": "latest DeepSeek V4.1 Flash updates"}'

# Deep neural search using Exa
belt app run exa/search --input '{"query": "best MCP servers for Windows desktop automation"}'

# Direct factual answer
belt app run exa/answer --input '{"question": "What are the breaking changes in Tauri v2 stable?"}'

# Extract webpage markdown content
belt app run tavily/extract --input '{"urls": ["https://modelcontextprotocol.io/introduction"]}'
```

---

## 2. Recommended MCP Servers for the Tensura Desktop Ecosystem

Under the **"Thin Backend - Thick Frontend"** architecture, the desktop companion (Tauri v2 + React) acts as an **Inverted MCP Host**, giving Raphael the power to interact with the Master's local OS while the backend focuses on causal memory and telemetry.

### 🌟 Tier 1: Desktop OS & Application Automation (Essential)
| MCP Server | Repository / Package | Description & Capabilities |
|---|---|---|
| **Windows-MCP** | `CursorTouch/Windows-MCP` | Native Windows UI Automation (UIA). Controls open windows, launches apps, simulates mouse & keyboard input, manages clipboard, and captures screenshots without heavy vision models. |
| **MCP Windows Automation** | `mukul975/mcp-windows-automation` | 80+ Windows system tools: app control, system settings, command-line execution, and workspace management. |
| **WinRemote MCP** | `winremote-mcp` | 40+ system administration tools: Windows Services, Registry read/write, scheduled tasks, process tree inspection, network socket status. |
| **Native Computer Use** | `quolu/Mcp.ComputerUse` | .NET/C# based native Windows desktop automation bridge with screen capturing, UIA perception, and input injection. |

### 🎵 Tier 2: Media, Audio & Environment Control (Raphael Voice & Ambience)
| MCP Server | Repository / Package | Description & Capabilities |
|---|---|---|
| **Spotify MCP (FastMCP)** | `PeterAkande/spotify_mcp` | 36 production tools: playback control (play, pause, skip, seek, shuffle), volume adjustment (0-100%), playlist management, user library queries, and track recommendations. Requires Spotify Premium + Developer Client ID/Secret. |
| **Spotify MCP (Node)** | `marcelmarais/spotify-mcp-server` / `imprvhub/mcp-claude-spotify` | Lightweight Node.js server for `getNowPlaying`, playback manipulation, and Spotify catalog search. |
| **Windows Audio Control** | Local Inverted MCP Tool | Adjusts system master volume, toggles microphone mute, and switches audio endpoints (speakers/headphones). |

### 🔍 Tier 3: Web Search & Knowledge Ingestion (Live Intelligence)
| MCP Server | Repository / Package | Description & Capabilities |
|---|---|---|
| **Tavily MCP** | `tavily-ai/tavily-mcp` | Real-time web search (`tavily-search`), clean markdown page extraction (`tavily-extract`), and site mapping (`tavily-crawl`). Hosted endpoint: `https://mcp.tavily.com/mcp/`. |
| **Brave Search MCP** | `brave/brave-search-mcp-server` | Privacy-focused web, news, local point-of-interest, and image search via Brave Search API. |
| **Exa Search MCP** | `exa-labs/exa-mcp-server` | Neural search engine optimized for AI agents and research workflows. Hosted endpoint: `https://mcp.exa.ai/mcp`. |
| **Omnisearch MCP** | `spences10/mcp-omnisearch` | Unified search aggregator routing queries across Tavily, Brave, Exa, and Kagi with fallback redundancy. |

### 💻 Tier 4: Developer, Workspace & Automation
| MCP Server | Repository / Package | Description & Capabilities |
|---|---|---|
| **Filesystem MCP** | `@modelcontextprotocol/server-filesystem` | Scoped read/write access to project directories with strict path sandbox enforcement. |
| **Playwright MCP** | `@modelcontextprotocol/server-playwright` | Headless/headed Chromium browser automation for dynamic single-page web scraping and UI verification. |
| **Git MCP** | `mcp-server-git` / `@modelcontextprotocol/server-git` | Inspect git log, diffs, branches, and commit status. |

---

## 3. Windows MCP Runner Configuration Pattern

To prevent PowerShell execution policy issues on Windows (e.g. `.ps1` restrictions per `GEMINI.md` Rule 8), Node/npx-based MCP servers in client configurations (such as `claude_desktop_config.json` or Tauri Inverted MCP runner) must wrap calls using `cmd /c`:

```json
{
  "mcpServers": {
    "windows-mcp": {
      "command": "cmd",
      "args": ["/c", "npx", "-y", "@cursortouch/windows-mcp"]
    },
    "spotify-mcp": {
      "command": "python",
      "args": ["-m", "spotify_mcp"],
      "env": {
        "SPOTIFY_CLIENT_ID": "your_client_id",
        "SPOTIFY_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

---

## 4. Recommended Agent Skills Ecosystem

In addition to MCP servers, agents should leverage curated open-source **Agent Skills** (following the progressive disclosure standard):

1. **`awesome-agent-skills` (`VoltAgent/awesome-agent-skills`)**: Over 1,000 community-contributed skills for engineering stacks, database migrations, and cloud ops.
2. **`anthropics/skills`**: Foundational reference skills for code evaluation, sandbox management, and reasoning benchmarks.
3. **Tensura Raphael Core Skills**:
   - **`web-search`** (This skill): Real-time external intelligence and technical documentation verification.
   - **`fastapi-sse-streaming`**: Real-time token streaming for low-latency Voice TTS and 3D Cosmos graph synchronization.
   - **`neo4j-gds-expert`**: Graph Data Science, in-memory projection, and 3-Tier causal GraphRAG algorithms.
   - **`deepseek-token-budgeter`**: Selective reasoning effort control (0 token pass-1, 1k-3k token deep psychological analysis pass-2).
   - **`docker-homelab-devops`**: Container volume live-reload, healthchecks, and Tailscale multi-machine networking.

---

## 5. Best Practices for Desktop Agent Search

1. **Query Formulation**: Include precise technology keywords (e.g. `Tauri v2`, `FastAPI SSE`, `Neo4j GDS 2.x`). Avoid vague single-word queries.
2. **Token Economy**: When extracting web pages, always convert HTML to clean markdown to minimize context window consumption.
3. **Fallback Strategy**:
   - First attempt: Semantic search (Tavily/Exa).
   - Second attempt: Keyword search (DuckDuckGo Lite / Brave).
   - Fallback: Local offline documentation or cached vector store.
4. **Safety & Privacy**: Never send private tokens, Master context, or sensitive server credentials in public search queries.
