#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/graph_doctor.py — post-merge graph hygiene check.

`graphify update` re-extracts code and drops nodes whose file disappeared, but
the shrink guard, an interrupted run or a scan that ignored `.gitignore` can
still leave the graph describing files that are gone. This answers one
question: does every node in `graphify-out/graph.json` still have a source
file on disk?

    python scripts/graph_doctor.py              # report only; exit 1 if stale
    python scripts/graph_doctor.py --fix        # run `graphify update . --force`
    python scripts/graph_doctor.py --graph path/to/graph.json

Exit codes: 0 clean, 1 stale (or graph missing), 2 graphify not installed.
"""

import argparse
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GRAPH = REPO_ROOT / "graphify-out" / "graph.json"


def load_graph(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def audit(graph: dict, root: Path) -> tuple[Counter, int]:
    """Return (missing source files by repo-relative path, dangling link count)."""
    nodes = graph.get("nodes", [])
    node_ids = {node.get("id") for node in nodes}
    missing: Counter = Counter()
    for node in nodes:
        source_file = node.get("source_file") or ""
        if not source_file:
            continue
        if not (root / source_file).exists():
            missing[source_file] += 1
    dangling = sum(
        1
        for link in graph.get("links", [])
        if link.get("source") not in node_ids or link.get("target") not in node_ids
    )
    return missing, dangling


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", default=str(DEFAULT_GRAPH), help="path to graph.json")
    parser.add_argument("--fix", action="store_true", help="run `graphify update . --force`")
    parser.add_argument("--limit", type=int, default=10, help="how many stale paths to print")
    args = parser.parse_args()

    graph_path = Path(args.graph).resolve()
    if not graph_path.exists():
        print(f"graph not found: {graph_path}\nbuild it once with: graphify update . --force")
        return 1

    graph = load_graph(graph_path)
    missing, dangling = audit(graph, REPO_ROOT)
    node_count = len(graph.get("nodes", []))
    edge_count = len(graph.get("links", []))

    print(f"graph: {graph_path}")
    print(f"nodes: {node_count}  edges: {edge_count}  built at: {graph.get('built_at_commit', '?')}")
    print(f"dangling edges: {dangling}")

    if not missing:
        print("stale files: 0 — every node resolves to a file on disk")
        return 0

    print(f"stale files: {len(missing)} ({sum(missing.values())} nodes)")
    for path, count in missing.most_common(args.limit):
        print(f"  {count:5d} nodes  {path}")
    if len(missing) > args.limit:
        print(f"  ... {len(missing) - args.limit} more")

    if not args.fix:
        print("fix: graphify update . --force   (or rerun with --fix)")
        return 1

    if shutil.which("graphify") is None:
        print("graphify not on PATH; cannot --fix")
        return 2

    print("running: graphify update . --force")
    result = subprocess.run(
        ["graphify", "update", ".", "--force"],
        cwd=REPO_ROOT,
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
