import sqlite3, os, sys, datetime, re

DB = os.path.expanduser(r"~\.gemini\antigravity\conversation_summaries.db")


def con():
    uri = "file:///" + os.path.abspath(DB).replace(os.sep, "/") + "?mode=ro&immutable=1"
    return sqlite3.connect(uri, uri=True)


def ts(v):
    try:
        v = float(v)
        if v > 1e11:
            v /= 1000.0
        return datetime.datetime.fromtimestamp(v).strftime("%m-%d %H:%M")
    except Exception:
        return str(v)[:19]


def recent(n=15):
    c = con()
    rows = c.execute(
        """SELECT conversation_id, title, preview, step_count, last_modified_time,
                  workspace_uris, agent_name, status
           FROM conversation_summaries ORDER BY last_modified_time DESC LIMIT ?""",
        (n,),
    ).fetchall()
    for cid, title, prev, steps, lmt, ws, agent, status in rows:
        ws = (ws or "").replace("file:///", "").replace("%20", " ")
        ws = ws.replace("\x00", " / ")[:90]
        print(f"{ts(lmt)} | {steps:>4} steps | {cid[:8]} | {status}")
        print(f"   title: {title}")
        print(f"   ws:    {ws}")
        print(f"   prev:  {re.sub(chr(10), ' ', (prev or ''))[:220]}")
        print()


if __name__ == "__main__":
    recent(int(sys.argv[1]) if len(sys.argv) > 1 else 15)
