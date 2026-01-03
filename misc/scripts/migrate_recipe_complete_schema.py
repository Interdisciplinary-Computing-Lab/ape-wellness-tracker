#!/usr/bin/env python3
"""
Migration: ensure 'recipe' table has all required columns matching the model.

This script is idempotent and adds all missing columns if they don't exist.
Columns to add:
- quantity (FLOAT NOT NULL DEFAULT 1.0)
- unit_of_measurement (VARCHAR(50), nullable)
- source (VARCHAR(200), nullable)
- food_category (VARCHAR(50), nullable, default 'Other')
- category_id (INTEGER, nullable, foreign key to food_categories)
- protein_g (FLOAT, nullable, default 2.0)
- fiber_g (FLOAT, nullable, default 1.0)

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
    
    print("Starting recipe complete schema migration...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Define all columns that need to be added
        # Format: (column_name, column_type, nullable, default_value)
        columns_to_add = [
            ('quantity', 'FLOAT NOT NULL DEFAULT 1.0', False, None),
            ('unit_of_measurement', 'VARCHAR(50)', True, None),
            ('source', 'VARCHAR(200)', True, None),
            ('food_category', "VARCHAR(50) DEFAULT 'Other'", True, None),
            ('category_id', 'INTEGER', True, None),
            ('protein_g', 'FLOAT DEFAULT 2.0', True, None),
            ('fiber_g', 'FLOAT DEFAULT 1.0', True, None),
        ]
        
        added_count = 0
        for column_name, column_type, nullable, default_value in columns_to_add:
            if column_exists(cursor, 'recipe', column_name):
                print(f"  {column_name} column already exists. Skipping.")
                continue
            
            print(f"Adding {column_name} column to recipe...")
            cursor.execute(f"""
                ALTER TABLE recipe
                ADD COLUMN {column_name} {column_type}
            """)
            conn.commit()
            print(f"  Added {column_name} column.")
            added_count += 1
        
        # Update existing records with default values for NOT NULL columns
        if added_count > 0:
            print("Setting default values for existing records...")
            # Set quantity to 1.0 for existing records that might have NULL
            cursor.execute("""
                UPDATE recipe
                SET quantity = 1.0
                WHERE quantity IS NULL
            """)
            conn.commit()
            print("  Updated existing records with default values.")
        
        # Add foreign key constraint for category_id if it doesn't exist
        # Note: SQLite doesn't support adding foreign key constraints via ALTER TABLE
        # The constraint is enforced at the application level by SQLAlchemy
        
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

