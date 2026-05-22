"""
Lightweight SQLite schema updates applied at app startup (no Alembic).
"""

import sqlite3
import os


def _sqlite_db_path(db_uri, app_instance_path):
    if not db_uri.startswith('sqlite:///'):
        return None
    db_path = db_uri.replace('sqlite:///', '', 1)
    if not os.path.isabs(db_path):
        db_path = os.path.join(app_instance_path, os.path.basename(db_path))
    return db_path if os.path.exists(db_path) else None


def ensure_recipe_columns(db_uri, app_instance_path):
    """Add recipe quantity, unit, source, protein_g, fiber_g if missing."""
    db_path = _sqlite_db_path(db_uri, app_instance_path)
    if not db_path:
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('PRAGMA table_info(recipe)')
        columns = {row[1] for row in cursor.fetchall()}
        if not columns:
            return

        additions = [
            ('quantity', 'ALTER TABLE recipe ADD COLUMN quantity REAL DEFAULT 1.0 NOT NULL'),
            ('unit_of_measurement', 'ALTER TABLE recipe ADD COLUMN unit_of_measurement VARCHAR(50)'),
            ('source', 'ALTER TABLE recipe ADD COLUMN source VARCHAR(200)'),
            ('protein_g', 'ALTER TABLE recipe ADD COLUMN protein_g REAL DEFAULT 2.0'),
            ('fiber_g', 'ALTER TABLE recipe ADD COLUMN fiber_g REAL DEFAULT 1.0'),
        ]
        for name, sql in additions:
            if name not in columns:
                cursor.execute(sql)

        cursor.execute('UPDATE recipe SET quantity = 1.0 WHERE quantity IS NULL')
        cursor.execute('UPDATE recipe SET protein_g = 2.0 WHERE protein_g IS NULL')
        cursor.execute('UPDATE recipe SET fiber_g = 1.0 WHERE fiber_g IS NULL')
        conn.commit()
    finally:
        conn.close()


def ensure_meals_calories_logged(db_uri, app_instance_path):
    """
    Add meals.calories_logged if missing and backfill from recipe.calories.
    db_uri is like sqlite:///path/to/database.db
    """
    db_path = _sqlite_db_path(db_uri, app_instance_path)
    if not db_path:
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('PRAGMA table_info(meals)')
        columns = {row[1] for row in cursor.fetchall()}
        if 'calories_logged' not in columns:
            cursor.execute('ALTER TABLE meals ADD COLUMN calories_logged INTEGER')
            cursor.execute("""
                UPDATE meals
                SET calories_logged = (
                    SELECT calories FROM recipe WHERE recipe.id = meals.recipe_id
                )
                WHERE calories_logged IS NULL
            """)
            conn.commit()
    finally:
        conn.close()


def ensure_schema_updates(db_uri, app_instance_path):
    """Run all lightweight migrations before ORM queries."""
    ensure_recipe_columns(db_uri, app_instance_path)
    ensure_meals_calories_logged(db_uri, app_instance_path)
