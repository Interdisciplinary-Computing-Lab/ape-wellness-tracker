#!/usr/bin/env python3
"""
Migration: remove the 'age' column from 'apes' table.

The 'age' column is not part of the current model - age is calculated
as a property from the birthday field. This script removes the legacy
age column from the database.

SQLite doesn't support DROP COLUMN directly, so we need to:
1. Create a new table without the age column
2. Copy data from old table to new table
3. Drop old table
4. Rename new table
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
    
    print("Starting migration to remove age column from apes table...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if age column exists
        if not column_exists(cursor, 'apes', 'age'):
            print("age column does not exist. Nothing to do.")
            conn.close()
            return True
        
        print("age column found. Removing it...")
        
        # SQLite doesn't support DROP COLUMN, so we need to recreate the table
        # Step 1: Create new table without age column
        print("  Creating new table structure...")
        cursor.execute("""
            CREATE TABLE apes_new (
                id INTEGER PRIMARY KEY,
                ape_name VARCHAR(90) NOT NULL UNIQUE,
                birthday DATE,
                weight FLOAT,
                mother VARCHAR(90),
                image_filename VARCHAR(255),
                image_data BLOB,
                image_mime_type VARCHAR(100),
                is_archived BOOLEAN NOT NULL DEFAULT 0,
                archived_at DATETIME
            )
        """)
        
        # Step 2: Copy data from old table to new table (excluding age)
        print("  Copying data to new table...")
        cursor.execute("""
            INSERT INTO apes_new (
                id, ape_name, birthday, weight, mother, 
                image_filename, image_data, image_mime_type, 
                is_archived, archived_at
            )
            SELECT 
                id, ape_name, birthday, weight, mother,
                image_filename, image_data, image_mime_type,
                is_archived, archived_at
            FROM apes
        """)
        
        # Step 3: Drop old table
        print("  Dropping old table...")
        cursor.execute("DROP TABLE apes")
        
        # Step 4: Rename new table
        print("  Renaming new table...")
        cursor.execute("ALTER TABLE apes_new RENAME TO apes")
        
        conn.commit()
        print("Migration complete. age column removed.")
        
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

