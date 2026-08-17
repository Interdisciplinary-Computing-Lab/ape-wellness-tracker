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


def apply_catalog_data_migrations(db_uri, app_instance_path):
    """Apply versioned catalog corrections once without undoing later staff edits."""
    db_path = _sqlite_db_path(db_uri, app_instance_path)
    if not db_path:
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_data_migrations (
                name VARCHAR(100) PRIMARY KEY,
                applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        migration_name = 'correct_cheerios_calories_to_93'
        already_applied = cursor.execute(
            'SELECT 1 FROM app_data_migrations WHERE name = ?',
            (migration_name,),
        ).fetchone()
        if not already_applied:
            cursor.execute(
                """
                UPDATE recipe
                SET calories = 93
                WHERE meal_name = 'Cheerios'
                  AND calories = 100
                  AND source = 'Kitchen cheat sheet'
                """
            )
            cursor.execute(
                'INSERT INTO app_data_migrations (name) VALUES (?)',
                (migration_name,),
            )
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


def ensure_recipe_is_favorite(db_uri, app_instance_path):
    """Add recipe.is_favorite for staff-shared favorite foods."""
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
        if 'is_favorite' not in columns:
            cursor.execute(
                'ALTER TABLE recipe ADD COLUMN is_favorite BOOLEAN NOT NULL DEFAULT 0'
            )
        conn.commit()
    finally:
        conn.close()


def ensure_recipe_gram_weight(db_uri, app_instance_path):
    """Add recipe.gram_weight for FDC portion-based unit conversions."""
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
        if 'gram_weight' not in columns:
            cursor.execute('ALTER TABLE recipe ADD COLUMN gram_weight REAL')
        conn.commit()
    finally:
        conn.close()


def ensure_recipe_fdc_id(db_uri, app_instance_path):
    """Add recipe.fdc_id for USDA Foundation Foods linkage."""
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
        if 'fdc_id' not in columns:
            cursor.execute('ALTER TABLE recipe ADD COLUMN fdc_id VARCHAR(20)')
            cursor.execute(
                'CREATE UNIQUE INDEX IF NOT EXISTS ix_recipe_fdc_id ON recipe (fdc_id)'
            )
        conn.commit()
    finally:
        conn.close()


def ensure_apes_archive_columns(db_uri, app_instance_path):
    """Add apes.is_archived and apes.archived_at if missing (older databases)."""
    db_path = _sqlite_db_path(db_uri, app_instance_path)
    if not db_path:
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('PRAGMA table_info(apes)')
        columns = {row[1] for row in cursor.fetchall()}
        if not columns:
            return
        if 'is_archived' not in columns:
            cursor.execute(
                'ALTER TABLE apes ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0'
            )
        if 'archived_at' not in columns:
            cursor.execute('ALTER TABLE apes ADD COLUMN archived_at DATETIME')
        conn.commit()
    finally:
        conn.close()


def ensure_meals_logged_at(db_uri, app_instance_path):
    """Add meals.logged_at for recent-activity ordering (when entry was saved)."""
    db_path = _sqlite_db_path(db_uri, app_instance_path)
    if not db_path:
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('PRAGMA table_info(meals)')
        columns = {row[1] for row in cursor.fetchall()}
        if not columns:
            return
        if 'logged_at' not in columns:
            cursor.execute('ALTER TABLE meals ADD COLUMN logged_at DATETIME')
        cursor.execute(
            "UPDATE meals SET logged_at = datetime('2000-01-01', '+' || id || ' seconds') "
            "WHERE logged_at IS NULL"
        )
        conn.commit()
    finally:
        conn.close()


def ensure_meals_logged_at_save_order(db_uri, app_instance_path):
    """
    Legacy DBs copied feeding date into logged_at; restore save order from entry id.
    Rows saved after the fix keep a real logged_at and are not matched.
    """
    db_path = _sqlite_db_path(db_uri, app_instance_path)
    if not db_path:
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('PRAGMA table_info(meals)')
        columns = {row[1] for row in cursor.fetchall()}
        if 'logged_at' not in columns:
            return
        cursor.execute(
            "UPDATE meals SET logged_at = datetime('2000-01-01', '+' || id || ' seconds') "
            "WHERE logged_at = date"
        )
        if cursor.rowcount:
            conn.commit()
    finally:
        conn.close()


def ensure_meals_meal_type(db_uri, app_instance_path):
    """Add meals.meal_type for Breakfast/Lunch/Dinner overrides."""
    db_path = _sqlite_db_path(db_uri, app_instance_path)
    if not db_path:
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('PRAGMA table_info(meals)')
        columns = {row[1] for row in cursor.fetchall()}
        if not columns:
            return
        if 'meal_type' not in columns:
            cursor.execute('ALTER TABLE meals ADD COLUMN meal_type VARCHAR(20)')
            conn.commit()
    finally:
        conn.close()


def ensure_schema_updates(db_uri, app_instance_path):
    """Run all lightweight migrations before ORM queries."""
    ensure_recipe_columns(db_uri, app_instance_path)
    apply_catalog_data_migrations(db_uri, app_instance_path)
    ensure_recipe_fdc_id(db_uri, app_instance_path)
    ensure_recipe_gram_weight(db_uri, app_instance_path)
    ensure_recipe_is_favorite(db_uri, app_instance_path)
    ensure_meals_calories_logged(db_uri, app_instance_path)
    ensure_meals_logged_at(db_uri, app_instance_path)
    ensure_meals_logged_at_save_order(db_uri, app_instance_path)
    ensure_meals_meal_type(db_uri, app_instance_path)
    ensure_apes_archive_columns(db_uri, app_instance_path)
