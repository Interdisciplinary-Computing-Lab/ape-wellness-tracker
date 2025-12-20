#!/usr/bin/env python3
"""
Migration: ensure 'apes' table has 'is_archived' (BOOLEAN NOT NULL DEFAULT 0)
and 'archived_at' (DATETIME NULL).

This script is idempotent and prints ASCII-only logs for Windows consoles.
"""

from pathlib import Path
import sys

# Add project root to sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend import create_app
from backend.extensions import db
from sqlalchemy import text


def column_exists(inspector, table_name: str, column_name: str) -> bool:
    try:
        cols = [c['name'] for c in inspector.get_columns(table_name)]
        return column_name in cols
    except Exception:
        return False


def run():
    app = create_app()
    with app.app_context():
        print("Starting apes archive columns migration...")
        inspector = db.inspect(db.engine)

        needs_is_archived = not column_exists(inspector, 'apes', 'is_archived')
        needs_archived_at = not column_exists(inspector, 'apes', 'archived_at')

        if not needs_is_archived and not needs_archived_at:
            print("Columns already exist. Nothing to do.")
            return

        try:
            if needs_is_archived:
                print("Adding is_archived column to apes...")
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        ALTER TABLE apes
                        ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0
                    """))
                    conn.commit()
                print("Added is_archived.")

            if needs_archived_at:
                print("Adding archived_at column to apes...")
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        ALTER TABLE apes
                        ADD COLUMN archived_at DATETIME NULL
                    """))
                    conn.commit()
                print("Added archived_at.")

            print("Migration complete.")
        except Exception as e:
            print("Migration failed:", str(e))
            raise


if __name__ == '__main__':
    run()


