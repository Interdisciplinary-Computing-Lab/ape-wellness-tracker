#!/usr/bin/env python3
"""
Migration: ensure 'meals' table has all required columns matching the model.

This script is idempotent and adds all missing columns if they don't exist.
Columns to add:
- feeding_period (VARCHAR(20), nullable)
- user_id (INTEGER NOT NULL, foreign key to user)

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
    
    print("Starting meals complete schema migration...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Define all columns that need to be added
        columns_to_add = [
            ('feeding_period', 'VARCHAR(20)', True),
            ('user_id', 'INTEGER NOT NULL', False),
        ]
        
        added_count = 0
        for column_name, column_type, nullable in columns_to_add:
            if column_exists(cursor, 'meals', column_name):
                print(f"  {column_name} column already exists. Skipping.")
                continue
            
            print(f"Adding {column_name} column to meals...")
            cursor.execute(f"""
                ALTER TABLE meals
                ADD COLUMN {column_name} {column_type}
            """)
            conn.commit()
            print(f"  Added {column_name} column.")
            added_count += 1
        
        # For user_id, we need to set a default value for existing records
        # Get the first user ID to use as default
        if added_count > 0 and 'user_id' in [col[0] for col in columns_to_add if not col[2]]:
            cursor.execute("SELECT id FROM user LIMIT 1")
            first_user = cursor.fetchone()
            if first_user:
                user_id = first_user[0]
                print(f"Setting default user_id ({user_id}) for existing meal records...")
                cursor.execute("""
                    UPDATE meals
                    SET user_id = ?
                    WHERE user_id IS NULL
                """, (user_id,))
                conn.commit()
                print(f"  Updated existing records with user_id {user_id}.")
            else:
                print("  WARNING: No users found in database. Existing meals will have NULL user_id.")
        
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

