---
name: inverted-mcp-builder
description: >-
  Architecture, implementation patterns, and security sandboxing for Model Context Protocol
  (MCP) servers (Stdio and SSE). Use this skill when creating custom MCP servers, exposing
  local host tools to cloud AI models safely, preventing path traversal vulnerabilities,
  or integrating tools into desktop overlays and agentic IDEs.
---

# Inverted MCP Builder & Security Sandbox

This skill guides the construction, deployment, and security hardening of Model Context Protocol (MCP) servers, specifically the **Inverted MCP pattern** where a remote/cloud AI agent operates local desktop tools safely.

---

## 1. The Inverted MCP Pattern Explained

Traditional MCP servers typically run locally where the model runs.
In **Inverted MCP**:
- The cognitive model runs remotely (e.g. DeepSeek on SiliconFlow / Cloud).
- The desktop client (Tauri/Electron) or terminal hosts the MCP server on the user's physical machine.
- Tools (like filesystem access, window management, audio controls) execute locally via Stdio or SSE.

---

## 2. Mandatory Path Security Sandbox

> [!CAUTION]
> Any file-access MCP tool MUST enforce strict path containment. Never allow relative paths or symlinks to escape the designated project workspace.

```python
import os

def validate_safe_path(filepath: str, allowed_root: str = None) -> str:
    """Ensures filepath cannot escape the project sandbox."""
    if not allowed_root:
        allowed_root = os.path.abspath(os.getcwd())
    else:
        allowed_root = os.path.abspath(allowed_root)

    target_path = os.path.abspath(os.path.join(allowed_root, filepath))
    
    if not target_path.startswith(allowed_root):
        raise PermissionError(f"Security Alert: Attempted path escape: {filepath}")
    
    return target_path
```

---

## 3. Minimal Stdio MCP Server Template

```python
import asyncio
import os
import logging
from mcp.server import Server
import mcp.server.stdio

logging.basicConfig(level=logging.INFO)
app = Server("raphael-local-tools")

@app.tool()
async def read_local_file(filepath: str) -> str:
    """Safely reads a file within the project directory."""
    allowed_dir = os.path.abspath(os.getcwd())
    target_path = os.path.abspath(filepath)
    
    if not target_path.startswith(allowed_dir):
        return f"《Báo Động》 Truy cập ngoài vùng an toàn bị từ chối: {filepath}"
    
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"《Lỗi》 {str(e)}"

async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```
