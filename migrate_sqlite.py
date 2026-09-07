"""
migrate_sqlite.py
Safe migration: adds missing columns to the `user` table without touching existing data.
Run once: python migrate_sqlite.py
"""
import sqlite3
import pathlib
import sys

# ── Config ────────────────────────────────────────────────────────────────
# Adjust path if your SQLite file lives elsewhere
DB_CANDIDATES = [
    pathlib.Path("data/amazing_nobel.db"),
    pathlib.Path("amazing_nobel.db"),
]

REQUIRED_COLUMNS = [
    # (column_name, sql_type, default_value_sql)
    ("credits",         "REAL",     "0.0"),
    ("titles",          "TEXT",     "''"),
    ("active_buff",     "TEXT",     "''"),
    ("buff_expires_at", "DATETIME", "NULL"),
]

MESSAGELOG_COLUMNS = [
    ("timestamp", "DATETIME", "CURRENT_TIMESTAMP"),
]

# ── Helpers ───────────────────────────────────────────────────────────────
def get_existing_columns(cursor: sqlite3.Cursor, table: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}

def migrate_table(conn: sqlite3.Connection, table: str, required: list) -> None:
    cursor = conn.cursor()
    # Check if table exists first
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    if not cursor.fetchone():
        print(f"  Table `{table}` does not exist yet — skipping (will be created by SQLModel on first run).")
        return

    existing = get_existing_columns(cursor, table)
    for col_name, col_type, default in required:
        if col_name in existing:
            print(f"  [{table}] Column `{col_name}` already exists — skipping.")
        else:
            sql = f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type} DEFAULT {default}"
            cursor.execute(sql)
            print(f"  [{table}] Added column `{col_name}` ({col_type} DEFAULT {default}).")
    conn.commit()

# ── Main ──────────────────────────────────────────────────────────────────
def main():
    db_path = None
    for candidate in DB_CANDIDATES:
        if candidate.exists():
            db_path = candidate
            break

    if db_path is None:
        print("ERROR: SQLite database file not found.")
        print("Searched:", [str(c) for c in DB_CANDIDATES])
        print("Hint: run this script from the project root, or adjust DB_CANDIDATES.")
        sys.exit(1)

    print(f"Database found: {db_path.resolve()}")
    conn = sqlite3.connect(db_path)

    print("\nMigrating table `user`...")
    migrate_table(conn, "user", REQUIRED_COLUMNS)

    print("\nMigrating table `messagelog` (if exists)...")
    migrate_table(conn, "messagelog", MESSAGELOG_COLUMNS)

    conn.close()
    print("\nMigration complete. Restart the bot container.")

if __name__ == "__main__":
    main()
