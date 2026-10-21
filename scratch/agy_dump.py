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
        return (datetime.datetime.utcfromtimestamp(v) + datetime.timedelta(hours=7)).strftime("%m-%d %H:%M")
    except Exception:
        return str(v)[:19]


def dump(cid_prefix, nchunks=3, width=600):
    c = con()
    (cid,) = c.execute(
        "SELECT conversation_id FROM conversation_summaries WHERE conversation_id LIKE ?", (cid_prefix + "%",)
    ).fetchone()
    rows = c.execute(
        """SELECT chunk_index, chunk_first_step, chunk_last_step, last_step_created_at, user_body, agent_body
           FROM conversations_fts WHERE conversation_id=? ORDER BY chunk_index DESC LIMIT ?""",
        (cid, nchunks),
    ).fetchall()
    for ci, f, l, ca, ub, ab in reversed(rows):
        print(f"\n########## chunk {ci} (steps {f}..{l}) @ {ts(ca)} ##########")
        print("\n--- USER ---\n" + re.sub(r"\n{3,}", "\n\n", (ub or "").strip())[-6000:])
        print("\n--- AGENT ---\n" + re.sub(r"\n{3,}", "\n\n", (ab or "").strip())[-8000:])


if __name__ == "__main__":
    dump(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3)
