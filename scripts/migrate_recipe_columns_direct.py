#!/usr/bin/env python3
"""
Direct database migration script to add quantity, unit_of_measurement, and source columns to the recipe table.
This script directly modifies the database without going through Flask app initialization.
"""

import os
import sys
import sqlite3

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def migrate_recipe_table_direct():
    """Add quantity, unit_of_measurement, and source columns to recipe table using direct SQLite connection"""
    print("Starting direct Recipe table migration...")
    
    # Find the database file
    instance_path = os.path.join(project_root, 'instance')
    db_path = os.path.join(instance_path, 'database.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found at: {db_path}")
        print("   The database will be created when you first run the app.")
        return False
    
    try:
        # Connect directly to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(recipe)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        if not columns:
            print("❌ Recipe table does not exist. Please run the app first to create the tables.")
            conn.close()
            return False
        
        # Add quantity column if it doesn't exist
        if 'quantity' not in columns:
            print("Adding quantity column to recipe table...")
            cursor.execute("""
                ALTER TABLE recipe 
                ADD COLUMN quantity REAL DEFAULT 1.0 NOT NULL
            """)
            print("✓ Successfully added quantity column")
        else:
            print("✓ quantity column already exists")
        
        # Add unit_of_measurement column if it doesn't exist
        if 'unit_of_measurement' not in columns:
            print("Adding unit_of_measurement column to recipe table...")
            cursor.execute("""
                ALTER TABLE recipe 
                ADD COLUMN unit_of_measurement VARCHAR(50)
            """)
            print("✓ Successfully added unit_of_measurement column")
        else:
            print("✓ unit_of_measurement column already exists")
        
        # Add source column if it doesn't exist
        if 'source' not in columns:
            print("Adding source column to recipe table...")
            cursor.execute("""
                ALTER TABLE recipe 
                ADD COLUMN source VARCHAR(200)
            """)
            print("✓ Successfully added source column")
        else:
            print("✓ source column already exists")
        
        # Update existing records to have quantity = 1.0 if it's NULL (shouldn't happen, but just in case)
        cursor.execute("""
            UPDATE recipe 
            SET quantity = 1.0 
            WHERE quantity IS NULL
        """)
        
        conn.commit()
        
        # Verify the columns were added
        cursor.execute("PRAGMA table_info(recipe)")
        new_columns = {row[1]: row for row in cursor.fetchall()}
        
        required_columns = ['quantity', 'unit_of_measurement', 'source']
        all_present = all(col in new_columns for col in required_columns)
        
        if all_present:
            print("✓ Column verification successful")
            print("\nNew columns in recipe table:")
            for col in required_columns:
                print(f"  - {col}")
            conn.close()
            return True
        else:
            print("❌ Column verification failed")
            missing = [col for col in required_columns if col not in new_columns]
            print(f"Missing columns: {', '.join(missing)}")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main migration function"""
    success = migrate_recipe_table_direct()
    
    if success:
        print("\n✓ Recipe table migration completed successfully!")
        print("The application now supports:")
        print("  - Partial quantities (e.g., 0.5 cups)")
        print("  - Unit of measurement tracking (e.g., '1 cup', '1 piece', '100g')")
        print("  - Data source attribution (e.g., 'USDA Foundation Foods')")
        print("\nYou can now run the app with: python run.py")
    else:
        print("\n❌ Recipe table migration failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()

