#!/usr/bin/env python3
"""
Migration script to add category_id column to the existing recipe table.
This script adds the foreign key relationship between Recipe and FoodCategory.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import create_app
from backend.extensions import db

def migrate_recipe_table():
    """Add category_id column to recipe table"""
    print("Starting Recipe table migration...")
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Add the category_id column to the recipe table
            print("Adding category_id column to recipe table...")
            
            # Use raw SQL to add the column
            from sqlalchemy import text
            db.session.execute(text("""
                ALTER TABLE recipe 
                ADD COLUMN category_id INTEGER 
                REFERENCES food_categories(id)
            """))
            
            db.session.commit()
            print("✓ Successfully added category_id column to recipe table")
            
            # Verify the column was added
            result = db.session.execute(text("PRAGMA table_info(recipe)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'category_id' in columns:
                print("✓ Column verification successful")
            else:
                print("❌ Column verification failed")
                return False
                
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {str(e)}")
            return False

def main():
    """Main migration function"""
    success = migrate_recipe_table()
    
    if success:
        print("\n✓ Recipe table migration completed successfully!")
        print("The application should now work with the new food category system.")
    else:
        print("\n❌ Recipe table migration failed!")
        sys.exit(1)

if __name__ == '__main__':
    main() 