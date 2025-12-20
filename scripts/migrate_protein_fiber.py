#!/usr/bin/env python3
"""
Migration script to populate protein_g and fiber_g values for existing recipes.
This script uses the old hardcoded logic to calculate initial values, then stores them in the database.
"""
import sys
import os

# Add parent directory to path to import from backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run import app
from backend.extensions import db
from backend.models.entry import Recipe


def get_protein_fiber_legacy(meal_name):
    """
    Legacy function to calculate protein and fiber values based on meal name.
    This is used only for migration to populate existing records.
    """
    if not meal_name:
        return (2.0, 1.0)
    
    meal_lower = str(meal_name).lower()
    
    # High protein foods
    if any(word in meal_lower for word in ['egg', 'chicken', 'meat', 'fish', 'beef', 'pork', 'turkey', 'protein']):
        return (12.0, 0.5)
    # High fiber foods
    elif any(word in meal_lower for word in ['apple', 'banana', 'orange', 'berry', 'fruit']):
        return (0.5, 3.5)
    elif any(word in meal_lower for word in ['spinach', 'broccoli', 'carrot', 'vegetable', 'lettuce', 'kale']):
        return (2.0, 2.5)
    elif any(word in meal_lower for word in ['bean', 'lentil', 'legume', 'chickpea']):
        return (7.0, 6.0)
    elif any(word in meal_lower for word in ['rice', 'grain', 'oat', 'quinoa']):
        return (3.0, 1.5)
    elif any(word in meal_lower for word in ['milk', 'dairy', 'cheese', 'yogurt']):
        return (8.0, 0.0)
    elif any(word in meal_lower for word in ['nut', 'almond', 'peanut', 'seed']):
        return (6.0, 3.0)
    # Default values for other foods
    else:
        return (2.0, 1.0)


def migrate_protein_fiber():
    """Migrate existing recipes to include protein_g and fiber_g values"""
    with app.app_context():
        recipes = Recipe.query.all()
        updated_count = 0
        
        for recipe in recipes:
            # Only update if protein_g or fiber_g is None
            if recipe.protein_g is None or recipe.fiber_g is None:
                protein, fiber = get_protein_fiber_legacy(recipe.meal_name)
                recipe.protein_g = protein
                recipe.fiber_g = fiber
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            print(f"[SUCCESS] Updated {updated_count} recipes with protein and fiber values")
        else:
            print("[INFO] No recipes needed updating (all already have protein/fiber values)")
        
        # Also update any recipes that still have None values to defaults
        recipes_with_none = Recipe.query.filter(
            (Recipe.protein_g.is_(None)) | (Recipe.fiber_g.is_(None))
        ).all()
        
        if recipes_with_none:
            for recipe in recipes_with_none:
                if recipe.protein_g is None:
                    recipe.protein_g = 2.0
                if recipe.fiber_g is None:
                    recipe.fiber_g = 1.0
            db.session.commit()
            print(f"[SUCCESS] Set default values for {len(recipes_with_none)} recipes with None values")


if __name__ == "__main__":
    migrate_protein_fiber()

