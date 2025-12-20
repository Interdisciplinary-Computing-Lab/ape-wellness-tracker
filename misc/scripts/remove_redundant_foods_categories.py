#!/usr/bin/env python3
"""
Migration script to remove redundant food items and categories from the database.
Removes:
- "milk" and "crackers" food items from the Recipe table
- "dairy" and "Treats" categories from the FoodCategory table
"""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend import create_app
from backend.extensions import db
from backend.models.entry import Recipe, FoodCategory, Meals

def remove_redundant_items():
    """Remove redundant food items and categories"""
    print("Starting removal of redundant food items and categories...")
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Items to remove (case-insensitive search)
            food_items_to_remove = ['milk', 'crackers']
            categories_to_remove = ['dairy', 'Treats']
            
            removed_foods = []
            removed_categories = []
            
            # Remove food items
            for food_name in food_items_to_remove:
                # Search case-insensitively
                recipes = Recipe.query.filter(
                    db.func.lower(Recipe.meal_name) == food_name.lower()
                ).all()
                
                for recipe in recipes:
                    # Check if recipe is used in any meals
                    meals = Meals.query.filter_by(recipe_id=recipe.id).all()
                    meal_count = len(meals)
                    if meal_count > 0:
                        print(f"Removing {meal_count} meal(s) that use '{recipe.meal_name}'...")
                        for meal in meals:
                            db.session.delete(meal)
                        print(f"Removing food item: '{recipe.meal_name}'")
                        db.session.delete(recipe)
                        removed_foods.append(recipe.meal_name)
                    else:
                        print(f"Removing food item: '{recipe.meal_name}'")
                        db.session.delete(recipe)
                        removed_foods.append(recipe.meal_name)
            
            # Remove categories
            for category_name in categories_to_remove:
                # Search case-insensitively
                categories = FoodCategory.query.filter(
                    db.func.lower(FoodCategory.name) == category_name.lower()
                ).all()
                
                for category in categories:
                    # Check if category is used by any recipes
                    recipes = Recipe.query.filter_by(category_id=category.id).all()
                    recipe_count = len(recipes)
                    if recipe_count > 0:
                        print(f"⚠️  Warning: Category '{category.name}' is used by {recipe_count} recipe(s).")
                        print(f"   Setting category_id to NULL for these recipes...")
                        for recipe in recipes:
                            recipe.category_id = None
                        print(f"Removing category: '{category.name}'")
                        db.session.delete(category)
                        removed_categories.append(category.name)
                    else:
                        print(f"Removing category: '{category.name}'")
                        db.session.delete(category)
                        removed_categories.append(category.name)
            
            # Commit changes
            db.session.commit()
            
            print("\n✓ Removal completed successfully!")
            if removed_foods:
                print(f"Removed food items: {', '.join(removed_foods)}")
            else:
                print("No food items were removed (none found or all are in use)")
            
            if removed_categories:
                print(f"Removed categories: {', '.join(removed_categories)}")
            else:
                print("No categories were removed (none found or all are in use)")
            
            return True
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Removal failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main function"""
    success = remove_redundant_items()
    
    if success:
        print("\n✓ Redundant items removal completed successfully!")
    else:
        print("\n❌ Redundant items removal failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()

