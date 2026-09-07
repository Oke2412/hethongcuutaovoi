"""
migrate_sqlite.py
Safe migration: adds ALL missing columns across all tables without touching existing data.
Idempotent — safe to run multiple times.
Run: python migrate_sqlite.py
"""
import sqlite3
import pathlib
import sys

# ── Config ────────────────────────────────────────────────────────────────
DB_CANDIDATES = [
    pathlib.Path("data/amazing_nobel.db"),
    pathlib.Path("amazing_nobel.db"),
]

# Schema: { table_name: [(col_name, sql_type, default_sql)] }
MIGRATIONS: dict[str, list[tuple[str, str, str]]] = {
    "user": [
        ("credits",         "REAL",     "0.0"),
        ("titles",          "TEXT",     "''"),
        ("active_buff",     "TEXT",     "''"),
        ("buff_expires_at", "DATETIME", "NULL"),
    ],
    "capabilitylog": [
        ("exp", "REAL", "0.0"),
    ],
    "systemquest": [
        ("parent_quest_id", "INTEGER", "NULL"),
    ],
    "messagelog": [
        # messagelog may not exist yet — SQLModel will create it on first run
        ("timestamp", "DATETIME", "CURRENT_TIMESTAMP"),
    ],
}

# ── Helpers ───────────────────────────────────────────────────────────────
def get_existing_columns(cursor: sqlite3.Cursor, table: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def migrate_table(conn: sqlite3.Connection, table: str, columns: list) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    if not cursor.fetchone():
        print(f"  [{table}] Table does not exist yet — skipping (SQLModel will create it).")
        return

    existing = get_existing_columns(cursor, table)
    changed = False
    for col_name, col_type, default in columns:
        if col_name in existing:
            print(f"  [{table}] `{col_name}` already exists — skipping.")
        else:
            sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type} DEFAULT {default}"
            cursor.execute(sql)
            print(f"  [{table}] Added `{col_name}` ({col_type} DEFAULT {default}).")
            changed = True
    if changed:
        conn.commit()


# ── Main ──────────────────────────────────────────────────────────────────
def main() -> None:
    db_path = None
    for candidate in DB_CANDIDATES:
        if candidate.exists():
            db_path = candidate
            break

    if db_path is None:
        print("ERROR: SQLite database file not found.")
        print("Searched:", [str(c) for c in DB_CANDIDATES])
        sys.exit(1)

    print(f"Database: {db_path.resolve()}\n")
    conn = sqlite3.connect(db_path)

    for table, columns in MIGRATIONS.items():
        print(f"Migrating `{table}`...")
        migrate_table(conn, table, columns)

    conn.close()
    print("\nAll migrations complete. Restart the bot: docker compose restart bot")


if __name__ == "__main__":
    main()
