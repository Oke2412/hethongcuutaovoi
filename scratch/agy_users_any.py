import json, os, re, sys

CID = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 5


def flat(v):
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return " ".join(flat(x) for x in v)
    if isinstance(v, dict):
        return " ".join(flat(x) for x in v.values())
    return ""


p = os.path.expanduser(rf"~\.gemini\antigravity\brain\{CID}\.system_generated\logs\transcript.jsonl")
if not os.path.exists(p):
    print("no transcript:", p)
    raise SystemExit(0)
rows = [json.loads(l) for l in open(p, encoding="utf-8", errors="replace") if l.strip()]
u = [r for r in rows if r.get("source") == "USER_EXPLICIT"]
print("msgs:", len(rows), "| user:", len(u))
for r in u[-N:]:
    b = re.sub(r"\s+", " ", flat(r.get("content"))).split("<ADDITIONAL_METADATA>")[0]
    b = b.replace("<USER_REQUEST>", "").replace("</USER_REQUEST>", "").strip()
    print(f"\n[{r.get('created_at','')}] {b[:320]}")
last = rows[-1]
print("\nLAST:", last.get("created_at"), last.get("source"), last.get("type"), "|",
      re.sub(r"\s+", " ", flat(last.get("content")))[:220])
