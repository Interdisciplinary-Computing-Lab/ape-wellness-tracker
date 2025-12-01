#!/usr/bin/env python3
"""
Migration script to add quantity, unit_of_measurement, and source columns to the recipe table.
This script implements the food items data management enhancements:
- quantity (float): Base quantity for which calories are calculated (default: 1.0)
- unit_of_measurement (string): Unit indicating what quantity=1 means (e.g., "1 cup", "1 piece", "100g")
- source (string): Data source for the nutritional information (e.g., "USDA Foundation Foods")
"""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend import create_app
from backend.extensions import db

def migrate_recipe_table():
    """Add quantity, unit_of_measurement, and source columns to recipe table"""
    print("Starting Recipe table migration for food items data management...")
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            from sqlalchemy import text
            
            # Check existing columns
            result = db.session.execute(text("PRAGMA table_info(recipe)"))
            columns = {row[1]: row for row in result.fetchall()}
            
            # Add quantity column if it doesn't exist
            if 'quantity' not in columns:
                print("Adding quantity column to recipe table...")
                db.session.execute(text("""
                    ALTER TABLE recipe 
                    ADD COLUMN quantity REAL DEFAULT 1.0 NOT NULL
                """))
                print("✓ Successfully added quantity column")
            else:
                print("✓ quantity column already exists")
            
            # Add unit_of_measurement column if it doesn't exist
            if 'unit_of_measurement' not in columns:
                print("Adding unit_of_measurement column to recipe table...")
                db.session.execute(text("""
                    ALTER TABLE recipe 
                    ADD COLUMN unit_of_measurement VARCHAR(50)
                """))
                print("✓ Successfully added unit_of_measurement column")
            else:
                print("✓ unit_of_measurement column already exists")
            
            # Add source column if it doesn't exist
            if 'source' not in columns:
                print("Adding source column to recipe table...")
                db.session.execute(text("""
                    ALTER TABLE recipe 
                    ADD COLUMN source VARCHAR(200)
                """))
                print("✓ Successfully added source column")
            else:
                print("✓ source column already exists")
            
            # Update existing records to have quantity = 1.0 if it's NULL (shouldn't happen, but just in case)
            db.session.execute(text("""
                UPDATE recipe 
                SET quantity = 1.0 
                WHERE quantity IS NULL
            """))
            
            db.session.commit()
            print("\n✓ Successfully migrated recipe table")
            
            # Verify the columns were added
            result = db.session.execute(text("PRAGMA table_info(recipe)"))
            new_columns = {row[1]: row for row in result.fetchall()}
            
            required_columns = ['quantity', 'unit_of_measurement', 'source']
            all_present = all(col in new_columns for col in required_columns)
            
            if all_present:
                print("✓ Column verification successful")
                print("\nNew columns in recipe table:")
                for col in required_columns:
                    print(f"  - {col}")
                return True
            else:
                print("❌ Column verification failed")
                missing = [col for col in required_columns if col not in new_columns]
                print(f"Missing columns: {', '.join(missing)}")
                return False
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main migration function"""
    success = migrate_recipe_table()
    
    if success:
        print("\n✓ Recipe table migration completed successfully!")
        print("The application now supports:")
        print("  - Partial quantities (e.g., 0.5 cups)")
        print("  - Unit of measurement tracking (e.g., '1 cup', '1 piece', '100g')")
        print("  - Data source attribution (e.g., 'USDA Foundation Foods')")
    else:
        print("\n❌ Recipe table migration failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()

