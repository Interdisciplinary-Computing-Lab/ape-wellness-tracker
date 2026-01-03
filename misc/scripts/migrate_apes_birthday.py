#!/usr/bin/env python3
"""
Migration: ensure 'apes' table has 'birthday' (DATE NOT NULL).

This script is idempotent and adds the birthday column if it doesn't exist.
For existing records without a birthday, it sets a default date (2000-01-01).

This script uses raw SQL to avoid triggering ORM model queries during app initialization.
"""

from pathlib import Path
import sys
import os
import sqlite3

# Add project root to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def column_exists(cursor, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table using PRAGMA table_info"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def run():
    # Find database path
    db_path = os.path.join(project_root, 'instance', 'database.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}. Please run the application first to create the database.")
        return False
    
    print("Starting apes birthday column migration...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if column_exists(cursor, 'apes', 'birthday'):
            print("birthday column already exists. Nothing to do.")
            conn.close()
            return True
        
        print("Adding birthday column to apes...")
        # Add column as nullable first
        cursor.execute("""
            ALTER TABLE apes
            ADD COLUMN birthday DATE
        """)
        conn.commit()
        print("Added birthday column.")

        # Update existing records with a default birthday if they don't have one
        print("Setting default birthdays for existing records...")
        default_birthday = "2000-01-01"  # Use string format for SQLite
        cursor.execute("""
            UPDATE apes
            SET birthday = ?
            WHERE birthday IS NULL
        """, (default_birthday,))
        conn.commit()
        updated_count = cursor.rowcount
        print(f"Updated {updated_count} existing records with default birthday.")

        # Note: SQLite doesn't support ALTER COLUMN to change nullability
        # The model enforces NOT NULL at the application level
        # For new records, the application will require birthday
        
        print("Migration complete.")
        conn.close()
        return True
        
    except Exception as e:
        print("Migration failed:", str(e))
        if conn:
            conn.rollback()
            conn.close()
        raise


if __name__ == '__main__':
    success = run()
    sys.exit(0 if success else 1)

