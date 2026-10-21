# -*- coding: utf-8 -*-
"""graphify Steps B3-C-4-4.5 for the amazing-nobel corpus.

Run AFTER the three semantic chunk subagents have written
graphify-out/.graphify_chunk_0N.json. Uses the official graphify APIs only;
no custom graph logic.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(".").resolve()
OUT = ROOT / "graphify-out"
SPEC = ROOT / ".dsh/skills/graphify/skills/agents/references/extraction-spec.md"
IS_DIRECTED = False


def merge_chunks() -> dict:
    chunks = sorted(glob.glob(str(OUT / ".graphify_chunk_*.json")))
    all_nodes: list = []
    all_edges: list = []
    all_hyperedges: list = []
    tin = tout = 0
    for chunk in chunks:
        data = json.loads(Path(chunk).read_text(encoding="utf-8"))
        all_nodes += data.get("nodes", [])
        all_edges += data.get("edges", [])
        all_hyperedges += data.get("hyperedges", [])
        tin += data.get("input_tokens", 0)
        tout += data.get("output_tokens", 0)
    merged = {
        "nodes": all_nodes,
        "edges": all_edges,
        "hyperedges": all_hyperedges,
        "input_tokens": tin,
        "output_tokens": tout,
    }
    (OUT / ".graphify_semantic_new.json").write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Merged {len(chunks)} chunks: {len(all_nodes)} nodes, {len(all_edges)} edges, {tin:,} in / {tout:,} out tokens")
    return merged


def persist_cache() -> None:
    from graphify.cache import save_semantic_cache

    new = json.loads((OUT / ".graphify_semantic_new.json").read_text(encoding="utf-8"))
    uncached = [l for l in (OUT / ".graphify_uncached.txt").read_text(encoding="utf-8").splitlines() if l]
    saved = save_semantic_cache(
        new.get("nodes", []),
        new.get("edges", []),
        new.get("hyperedges", []),
        root=str(ROOT),
        allowed_source_files=uncached,
        prompt_file=str(SPEC),
    )
    print(f"Cached {saved} files")


def merge_semantic() -> dict:
    cached_path = OUT / ".graphify_cached.json"
    cached = json.loads(cached_path.read_text(encoding="utf-8")) if cached_path.exists() else {"nodes": [], "edges": [], "hyperedges": []}
    new = json.loads((OUT / ".graphify_semantic_new.json").read_text(encoding="utf-8"))
    all_nodes = cached["nodes"] + new.get("nodes", [])
    all_edges = cached["edges"] + new.get("edges", [])
    all_hyperedges = cached.get("hyperedges", []) + new.get("hyperedges", [])
    seen: set = set()
    deduped = []
    for n in all_nodes:
        if n["id"] not in seen:
            seen.add(n["id"])
            deduped.append(n)
    merged = {
        "nodes": deduped,
        "edges": all_edges,
        "hyperedges": all_hyperedges,
        "input_tokens": new.get("input_tokens", 0),
        "output_tokens": new.get("output_tokens", 0),
    }
    (OUT / ".graphify_semantic.json").write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Semantic: {len(deduped)} nodes, {len(all_edges)} edges")
    return merged


def merge_ast_semantic() -> dict:
    ast = json.loads((OUT / ".graphify_ast.json").read_text(encoding="utf-8"))
    sem = json.loads((OUT / ".graphify_semantic.json").read_text(encoding="utf-8"))

    for n in sem["nodes"]:
        n.setdefault("_origin", "semantic")
    for e in sem["edges"]:
        e.setdefault("_origin", "semantic")

    seen = {n["id"] for n in ast["nodes"]}
    merged_nodes = list(ast["nodes"])
    for n in sem["nodes"]:
        if n["id"] not in seen:
            merged_nodes.append(n)
            seen.add(n["id"])

    merged = {
        "nodes": merged_nodes,
        "edges": ast["edges"] + sem["edges"],
        "hyperedges": sem.get("hyperedges", []),
        "input_tokens": sem.get("input_tokens", 0),
        "output_tokens": sem.get("output_tokens", 0),
    }
    (OUT / ".graphify_extract.json").write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Merged: {len(merged_nodes)} nodes, {len(merged['edges'])} edges ({len(ast['nodes'])} AST + {len(sem['nodes'])} semantic)")
    return merged


def build() -> None:
    from graphify.build import build_from_json
    from graphify.cluster import cluster, score_all
    from graphify.analyze import god_nodes, surprising_connections, suggest_questions
    from graphify.report import generate
    from graphify.export import to_json

    extraction = json.loads((OUT / ".graphify_extract.json").read_text(encoding="utf-8"))
    detection = json.loads((OUT / ".graphify_detect.json").read_text(encoding="utf-8"))

    G = build_from_json(extraction, root=str(ROOT), directed=IS_DIRECTED)
    if G.number_of_nodes() == 0:
        print("ERROR: Graph is empty - extraction produced no nodes.")
        raise SystemExit(1)

    communities = cluster(G)
    cohesion = score_all(G, communities)
    tokens = {"input": extraction.get("input_tokens", 0), "output": extraction.get("output_tokens", 0)}
    gods = god_nodes(G)
    surprises = surprising_connections(G, communities)
    labels = {cid: "Community " + str(cid) for cid in communities}
    questions = suggest_questions(G, communities, labels)

    wrote = to_json(G, communities, str(OUT / "graph.json"))
    if not wrote:
        print("ERROR: refused to shrink graphify-out/graph.json (existing graph has more nodes; #479).")
        raise SystemExit(1)

    report = generate(
        G, communities, cohesion, labels, gods, surprises, detection, tokens, str(ROOT),
        suggested_questions=questions,
    )
    (OUT / "GRAPH_REPORT.md").write_text(report, encoding="utf-8")
    analysis = {
        "communities": {str(k): v for k, v in communities.items()},
        "cohesion": {str(k): v for k, v in cohesion.items()},
        "gods": gods,
        "surprises": surprises,
        "questions": questions,
    }
    (OUT / ".graphify_analysis.json").write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {len(communities)} communities")


def diagnose() -> None:
    from graphify.diagnostics import diagnose_extraction, format_diagnostic_report

    extraction = json.loads((OUT / ".graphify_extract.json").read_text(encoding="utf-8"))
    summary = diagnose_extraction(extraction, directed=IS_DIRECTED, root=str(ROOT))
    print(format_diagnostic_report(summary))
    flags = [
        f"{summary[k]} {label}"
        for k, label in (
            ("dangling_endpoint_edges", "dangling-endpoint edges"),
            ("missing_endpoint_edges", "missing-endpoint edges"),
            ("self_loop_edges", "self-loop edges"),
            ("directed_same_endpoint_collapsed_edges", "collapsed (directed) edges"),
            ("undirected_same_endpoint_collapsed_edges", "collapsed (undirected) edges"),
        )
        if summary.get(k, 0)
    ]
    print(
        "GRAPH HEALTH WARNING: " + "; ".join(flags) + " - graph may be incomplete/corrupt."
        if flags
        else "Graph health: OK (no dangling/missing/collapsed edges)."
    )


if __name__ == "__main__":
    merge_chunks()
    persist_cache()
    merge_semantic()
    merge_ast_semantic()
    build()
    diagnose()
