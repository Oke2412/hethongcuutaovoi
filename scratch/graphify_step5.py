# -*- coding: utf-8 -*-
"""graphify Step 5 — apply curated community labels, regenerate report, re-export."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(".").resolve()
OUT = ROOT / "graphify-out"

LABELS = {
    0: "Telegram Bot Handlers",
    1: "Agent Turn Execution",
    2: "FastAPI Service Shell",
    3: "Async Runtime & MCP Stub",
    4: "LLM Core & Mem0 Incidents",
    5: "Docker Compose Topology",
    6: "Core Brain Orchestrator",
    7: "Scheduler & Bot Wiring",
    8: "Telegram Location Handler",
    9: "Project Overview & Memory",
    10: "Persona Rules & HUD",
    11: "Retrieval & Embedding Stack",
    12: "Chronicle Import & Snapshots",
    13: "Query Expansion & Neo4j Checks",
    14: "GDS Verification Scripts",
    15: "Gemini API Reference",
    16: "Pipeline Evaluation Harness",
    17: "Desktop Adapter Tests",
    18: "Location Tracking & SSE",
    19: "Skills Catalog & Bridge",
    20: "Neo4j GDS Analytics",
    21: "System Architecture Overview",
    22: "DuckDuckGo Search Parser",
    23: "API Route Tests",
    24: "Inverted MCP Design",
    25: "Reset Command Handlers",
    26: "SQLite Migration Script",
    27: "Working Rules & Search Skill",
    28: "SSE Probe Utility",
    29: "Data Wipe Script",
    30: "Neo4j Schema Rules",
    31: "Desktop Client & DevOps Notes",
    32: "DeepSeek Model Migration",
    33: "Model Router & Quotas",
    34: "Test Report Helper",
    35: "DB Session Helper",
    36: "Architecture Roadmap & Debt",
    37: "google-genai Namespace Conflict",
    38: "Dual Pipeline Split",
    39: "Core Value Graph Schema",
    40: "Rule File Migration",
    41: "Package Init Placeholders",
    42: "Package Init Placeholders",
    43: "Package Init Placeholders",
    44: "Package Init Placeholders",
    45: "Package Init Placeholders",
    46: "Package Init Placeholders",
}


def main() -> None:
    from graphify.build import build_from_json
    from graphify.analyze import suggest_questions
    from graphify.report import generate
    from graphify.export import to_json

    extraction = json.loads((OUT / ".graphify_extract.json").read_text(encoding="utf-8"))
    detection = json.loads((OUT / ".graphify_detect.json").read_text(encoding="utf-8"))
    analysis = json.loads((OUT / ".graphify_analysis.json").read_text(encoding="utf-8"))

    G = build_from_json(extraction, root=str(ROOT), directed=False)
    communities = {int(k): v for k, v in analysis["communities"].items()}
    cohesion = {int(k): v for k, v in analysis["cohesion"].items()}
    tokens = {"input": extraction.get("input_tokens", 0), "output": extraction.get("output_tokens", 0)}

    missing = sorted(set(communities) - set(LABELS))
    assert not missing, f"unlabelled communities: {missing}"

    questions = suggest_questions(G, communities, LABELS)
    report = generate(
        G, communities, cohesion, LABELS, analysis["gods"], analysis["surprises"],
        detection, tokens, str(ROOT), suggested_questions=questions,
    )
    (OUT / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    (OUT / ".graphify_labels.json").write_text(
        json.dumps({str(k): v for k, v in LABELS.items()}, ensure_ascii=False), encoding="utf-8"
    )
    wrote = to_json(G, communities, str(OUT / "graph.json"), community_labels=LABELS)
    if not wrote:
        print("ERROR: refused to shrink graphify-out/graph.json (#479).")
        raise SystemExit(1)
    print(f"Report updated with {len(LABELS)} community labels; graph re-exported")


if __name__ == "__main__":
    main()
