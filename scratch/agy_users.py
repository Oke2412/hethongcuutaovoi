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
        return " ".join(flat(x) for x in v.values())
    return ""


def main(n=12, width=420):
    with open(P, encoding="utf-8", errors="replace") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    users = [r for r in rows if r.get("source") == "USER_EXPLICIT"]
    print("total user msgs:", len(users))
    for r in users[-n:]:
        ts = r.get("created_at", "")
        body = re.sub(r"\s+", " ", flat(r.get("content"))).replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "")
        body = body.split("<ADDITIONAL_METADATA>")[0]
        print(f"\n[{ts}] {body.strip()[:width]}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 12)
