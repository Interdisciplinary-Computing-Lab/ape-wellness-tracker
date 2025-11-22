#!/usr/bin/env python3
"""
Migration script to add feeding_period field to meals table.
This script adds the new feeding_period column to the existing meals table.
"""

import sqlite3
import os
from datetime import datetime

def migrate_feeding_period():
    """Add feeding_period column to meals table"""
    
    # Database path
    db_path = os.path.join('instance', 'database.db')
    
    if not os.path.exists(db_path):
        print("Database not found. Please run the application first to create the database.")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(meals)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'feeding_period' in columns:
            print("feeding_period column already exists. Migration not needed.")
            return True
        
        # Add the new column
        print("Adding feeding_period column to meals table...")
        cursor.execute("""
            ALTER TABLE meals 
            ADD COLUMN feeding_period VARCHAR(20)
        """)
        
        # Commit changes
        conn.commit()
        print("Successfully added feeding_period column to meals table.")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(meals)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'feeding_period' in columns:
            print("Migration completed successfully!")
            return True
        else:
            print("Error: Column was not added successfully.")
            return False
            
    except Exception as e:
        print(f"Error during migration: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Starting feeding_period migration...")
    success = migrate_feeding_period()
    
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")
        exit(1)
