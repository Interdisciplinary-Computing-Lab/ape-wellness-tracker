#!/usr/bin/env python3
"""
Migration script to:
1. Update "Trash Lettuce" (with description "Cabbage") back to "Cabbage" (with description "Fresh cabbage")
2. Create a new "Trash Lettuce" entry with description "Brussels sprouts" that can be searched by "Brussels sprouts"
"""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend import create_app
from backend.extensions import db
from backend.models.entry import Recipe

def migrate_cabbage_trash_lettuce():
    """Update cabbage and create new trash lettuce entry"""
    print("Starting migration for Cabbage and Trash Lettuce...")
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Find and update "Trash Lettuce" to "Cabbage"
            trash_lettuce = Recipe.query.filter_by(meal_name='Trash Lettuce').first()
            
            if trash_lettuce:
                print(f"Found 'Trash Lettuce' entry (ID: {trash_lettuce.id})")
                
                # Check if "Cabbage" already exists
                existing_cabbage = Recipe.query.filter_by(meal_name='Cabbage').first()
                
                if existing_cabbage:
                    print("'Cabbage' already exists. Updating its description to 'Fresh cabbage'...")
                    existing_cabbage.description = 'Fresh cabbage'
                    db.session.commit()
                    print(" Updated existing Cabbage entry")
                else:
                    # Rename "Trash Lettuce" to "Cabbage"
                    print("Renaming 'Trash Lettuce' to 'Cabbage'...")
                    trash_lettuce.meal_name = 'Cabbage'
                    trash_lettuce.description = 'Fresh cabbage'
                    db.session.commit()
                    print(" Successfully renamed 'Trash Lettuce' to 'Cabbage'")
            else:
                print("'Trash Lettuce' not found. Checking if 'Cabbage' exists...")
                existing_cabbage = Recipe.query.filter_by(meal_name='Cabbage').first()
                if existing_cabbage:
                    print("'Cabbage' already exists. Updating description...")
                    existing_cabbage.description = 'Fresh cabbage'
                    db.session.commit()
                    print(" Updated Cabbage entry")
                else:
                    print("Neither 'Trash Lettuce' nor 'Cabbage' found. Creating 'Cabbage'...")
                    new_cabbage = Recipe(
                        meal_name='Cabbage',
                        description='Fresh cabbage',
                        calories=22,
                        food_category='Vegetables',
                        quantity=1.0
                    )
                    db.session.add(new_cabbage)
                    db.session.commit()
                    print(" Created new 'Cabbage' entry")
            
            # Step 2: Create new "Trash Lettuce" entry with description "Brussels sprouts"
            new_trash_lettuce = Recipe.query.filter_by(meal_name='Trash Lettuce').first()
            
            if new_trash_lettuce:
                print("'Trash Lettuce' already exists. Updating description to 'Brussels sprouts'...")
                new_trash_lettuce.description = 'Brussels sprouts'
                db.session.commit()
                print(" Updated 'Trash Lettuce' description to 'Brussels sprouts'")
            else:
                print("Creating new 'Trash Lettuce' entry with description 'Brussels sprouts'...")
                # Brussels sprouts typically have around 38 calories per 100g, but we'll use a reasonable value
                new_trash_lettuce = Recipe(
                    meal_name='Trash Lettuce',
                    description='Brussels sprouts',
                    calories=38,  # Typical calories for Brussels sprouts
                    food_category='Vegetables',
                    quantity=1.0
                )
                db.session.add(new_trash_lettuce)
                db.session.commit()
                print(" Created new 'Trash Lettuce' entry with description 'Brussels sprouts'")
            
            # Verify the changes
            print("\nVerifying changes...")
            cabbage = Recipe.query.filter_by(meal_name='Cabbage').first()
            trash_lettuce = Recipe.query.filter_by(meal_name='Trash Lettuce').first()
            
            if cabbage:
                print(f" Cabbage: '{cabbage.meal_name}' - Description: '{cabbage.description}'")
            else:
                print(" Cabbage not found after migration!")
            
            if trash_lettuce:
                print(f" Trash Lettuce: '{trash_lettuce.meal_name}' - Description: '{trash_lettuce.description}'")
                # Verify searchability
                if 'brussels sprouts' in trash_lettuce.description.lower():
                    print(" Trash Lettuce can be searched by 'Brussels sprouts' (description contains it)")
                else:
                    print("⚠ Warning: Trash Lettuce description may not be searchable by 'Brussels sprouts'")
            else:
                print(" Trash Lettuce not found after migration!")
            
            print("\n Migration completed successfully!")
            return True
                
        except Exception as e:
            db.session.rollback()
            print(f" Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main migration function"""
    success = migrate_cabbage_trash_lettuce()
    
    if success:
        print("\n Cabbage and Trash Lettuce migration completed successfully!")
        print("Changes made:")
        print("  - 'Trash Lettuce' (Cabbage) renamed to 'Cabbage' with description 'Fresh cabbage'")
        print("  - New 'Trash Lettuce' entry created with description 'Brussels sprouts'")
        print("  - 'Trash Lettuce' can now be found by searching 'Brussels sprouts'")
    else:
        print("\n Migration failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()

