#!/usr/bin/env python3
"""
Migration: ensure 'apes' table has all required columns matching the model.

This script is idempotent and adds all missing columns if they don't exist.
Columns to add:
- weight (FLOAT, nullable)
- mother (VARCHAR(90), nullable)
- image_filename (VARCHAR(255), nullable)
- image_data (BLOB, nullable)
- image_mime_type (VARCHAR(100), nullable)
- is_archived (BOOLEAN NOT NULL DEFAULT 0)
- archived_at (DATETIME, nullable)

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
    
    print("Starting apes complete schema migration...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Define all columns that need to be added
        columns_to_add = [
            ('weight', 'FLOAT', True),
            ('mother', 'VARCHAR(90)', True),
            ('image_filename', 'VARCHAR(255)', True),
            ('image_data', 'BLOB', True),
            ('image_mime_type', 'VARCHAR(100)', True),
            ('is_archived', 'BOOLEAN NOT NULL DEFAULT 0', False),
            ('archived_at', 'DATETIME', True),
        ]
        
        added_count = 0
        for column_name, column_type, nullable in columns_to_add:
            if column_exists(cursor, 'apes', column_name):
                print(f"  {column_name} column already exists. Skipping.")
                continue
            
            print(f"Adding {column_name} column to apes...")
            nullable_clause = "" if not nullable else ""
            cursor.execute(f"""
                ALTER TABLE apes
                ADD COLUMN {column_name} {column_type} {nullable_clause}
            """)
            conn.commit()
            print(f"  Added {column_name} column.")
            added_count += 1
        
        if added_count == 0:
            print("All columns already exist. Nothing to do.")
        else:
            print(f"Migration complete. Added {added_count} column(s).")
        
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

