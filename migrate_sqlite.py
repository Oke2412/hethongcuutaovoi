import sqlite3
import os

def migrate_db():
    db_path = "data/amazing_nobel.db"
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. No migration needed.")
        return

    print("Starting database migration...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    columns_to_add = [
        ("user", "credits", "FLOAT DEFAULT 0.0"),
        ("user", "titles", "VARCHAR DEFAULT ''"),
        ("user", "active_buff", "VARCHAR DEFAULT ''"),
        ("user", "buff_expires_at", "DATETIME")
    ]

    for table, column, definition in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            print(f"[OK] Added column '{column}' to table '{table}'.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"[SKIP] Column '{column}' already exists in '{table}'.")
            else:
                print(f"[ERROR] Failed to add '{column}': {e}")

    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate_db()
