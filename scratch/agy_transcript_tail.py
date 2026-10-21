import json, os, sys, re

P = os.path.expanduser(
    r"~\.gemini\antigravity\brain\938a7972-5855-48bb-9ca6-6e3dbc56f13d\.system_generated\logs\transcript.jsonl"
)


def flat(v):
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return " ".join(flat(x) for x in v)
    if isinstance(v, dict):
        for k in ("text", "content", "body", "message", "summary", "value"):
            if k in v:
                return flat(v[k])
        return " ".join(flat(x) for x in v.values() if isinstance(x, (str, list, dict)))
    return ""


def main(n=25, width=300):
    with open(P, encoding="utf-8", errors="replace") as f:
        lines = [l for l in f if l.strip()]
    print("lines:", len(lines))
    for ln in lines[:1]:
        o = json.loads(ln)
        print("KEYS:", list(o.keys()))
    for ln in lines[-n:]:
        try:
            o = json.loads(ln)
        except Exception:
            continue
        src = o.get("source") or o.get("type") or o.get("role") or o.get("step_type") or "?"
        ts = o.get("timestamp") or o.get("created_at") or o.get("time") or ""
        body = re.sub(r"\s+", " ", flat(o))
        print(f"\n[{ts}] {str(src)[:40]}\n   {body[:width]}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 25)
