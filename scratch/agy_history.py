import sqlite3, sys, os, glob, json, datetime, re

BASE = os.path.expanduser(r"~\.gemini\antigravity\conversations")


def connect(path):
    uri = "file:///" + os.path.abspath(path).replace(os.sep, "/") + "?mode=ro&immutable=1"
    return sqlite3.connect(uri, uri=True)


def types(con):
    for t, n in con.execute("SELECT step_type, COUNT(*) FROM steps GROUP BY step_type ORDER BY 2 DESC"):
        print(f"  {t:35} {n}")


def sample(con, stype, n=2):
    for idx, payload, fmt in con.execute(
        "SELECT idx, step_payload, step_format FROM steps WHERE step_type=? ORDER BY idx DESC LIMIT ?", (stype, n)
    ):
        print(f"--- idx={idx} fmt={fmt} ---")
        print((payload or "")[:800])


def texts(con, limit=15, width=400):
    q = """
    SELECT idx, step_type, metadata, step_payload
    FROM steps WHERE step_type IN ('USER_INPUT','PLANNER_RESPONSE','USER_MESSAGE','user_input','assistant_message')
    ORDER BY idx DESC LIMIT ?
    """
    rows = con.execute(q, (limit,)).fetchall()
    for idx, stype, meta, payload in reversed(rows):
        m = {}
        try:
            m = json.loads(meta) if meta else {}
        except Exception:
            pass
        ts = m.get("createTime") or m.get("timestamp") or m.get("createdAt") or ""
        body = re.sub(r"\s+", " ", (payload or ""))[:width]
        print(f"[{idx}] {stype} {ts}\n    {body}\n")


if __name__ == "__main__":
    path = sys.argv[2]
    con = connect(path)
    cmd = sys.argv[1]
    if cmd == "types":
        types(con)
    elif cmd == "sample":
        sample(con, sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 2)
    elif cmd == "texts":
        texts(con, int(sys.argv[3]) if len(sys.argv) > 3 else 15)
