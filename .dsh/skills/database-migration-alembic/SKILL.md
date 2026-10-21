---
name: database-migration-alembic
description: >-
  Database schema migration, Alembic autogeneration, SQLite constraint preservation,
  and FTS5 full-text search trigger synchronization for SQLAlchemy and SQLModel apps.
  Use this skill when modifying database models, altering SQLite tables without data loss,
  adding new tables, or maintaining FTS5 virtual search tables.
---

# SQLite & FTS5 Database Migration Guide

This skill governs safe database evolution for SQLite and PostgreSQL under SQLAlchemy / SQLModel, ensuring zero data loss and automated FTS5 full-text synchronization.

---

## 1. The SQLite Batch Migration Invariant

> [!CRITICAL]
> Standard SQLite lacks native support for `ALTER TABLE DROP COLUMN` or altering column constraints.
> You MUST configure `render_as_batch=True` in Alembic's `env.py`, which re-creates tables and copies data safely behind the scenes.

In `alembic/env.py`:
```python
with context.begin_transaction():
    context.run_migrations(render_as_batch=True)
```

---

## 2. Maintaining FTS5 Virtual Tables & Sync Triggers

Whenever adding a searchable text table (e.g. `MessageLog`, `AmbientTranscript`), always create a companion FTS5 table and 3 SQLite triggers:

```sql
-- 1. Create FTS5 Virtual Table
CREATE VIRTUAL TABLE IF NOT EXISTS messagelog_fts USING fts5(
    id UNINDEXED,
    content,
    tokenize='unicode61'
);

-- 2. Insert Trigger
CREATE TRIGGER IF NOT EXISTS messagelog_ai AFTER INSERT ON messagelog BEGIN
    INSERT INTO messagelog_fts(id, content) VALUES (new.id, new.content);
END;

-- 3. Delete Trigger
CREATE TRIGGER IF NOT EXISTS messagelog_ad AFTER DELETE ON messagelog BEGIN
    DELETE FROM messagelog_fts WHERE id = old.id;
END;

-- 4. Update Trigger
CREATE TRIGGER IF NOT EXISTS messagelog_au AFTER UPDATE ON messagelog BEGIN
    UPDATE messagelog_fts SET content = new.content WHERE id = new.id;
END;
```

---

## 3. Migration Workflow

1. **Modify models** in `db/models.py`.
2. **Generate migration script**:
   ```bash
   alembic revision --autogenerate -m "add_column_name"
   ```
3. **Inspect generated migration** for safety before applying.
4. **Upgrade database**:
   ```bash
   alembic upgrade head
   ```
