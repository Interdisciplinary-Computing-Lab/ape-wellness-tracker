#!/usr/bin/env python3
"""
Seed data script for Ape Wellness Tracker
Populates the database with ape information and food items.
"""

from datetime import date, datetime, timedelta
from run import app
from backend.extensions import db
from backend.models.entry import Apes, Recipe, Meals
from backend.helpers import add_to_db

def seed_apes():
    """Seed the database with ape information"""
    
    # Clear existing apes
    Apes.query.delete()
    
    apes_data = [
        {
            'ape_name': 'MAISHA',
            'birthday': date(2000, 5, 28),
            'weight': 42.5,
            'mother': 'Matata'
        },
        {
            'ape_name': 'TECO',
            'birthday': date(2010, 6, 1),
            'weight': 38.2,
            'mother': None
        },
        {
            'ape_name': 'NYOTA',
            'birthday': date(1998, 4, 4),
            'weight': 45.8,
            'mother': None
        },
        {
            'ape_name': 'CLARA',
            'birthday': date(2010, 5, 27),
            'weight': 39.1,
            'mother': None
        },
        {
            'ape_name': 'MALI',
            'birthday': date(2007, 9, 4),
            'weight': 41.3,
            'mother': None
        },
        {
            'ape_name': 'ELIKYA',
            'birthday': date(1997, 6, 28),
            'weight': 44.7,
            'mother': 'Matata'
        }
    ]
    
    for ape_data in apes_data:
        ape = Apes(**ape_data)
        add_to_db(ape, "ape")
        print(f"Added ape: {ape.ape_name} (Age: {ape.age}, Birthday: {ape.birthday})")

def seed_foods():
    """Seed the database with comprehensive food items"""
    
    # Clear existing recipes
    Recipe.query.delete()
    
    foods_data = [
        # Fruits (primary staple)
        {'meal_name': 'Banana', 'description': 'Fresh banana', 'calories': 105},
        {'meal_name': 'Apple', 'description': 'Fresh apple', 'calories': 95},
        {'meal_name': 'Grapes', 'description': 'Fresh grapes', 'calories': 62},
        {'meal_name': 'Blueberries', 'description': 'Fresh blueberries', 'calories': 85},
        {'meal_name': 'Strawberries', 'description': 'Fresh strawberries', 'calories': 49},
        {'meal_name': 'Watermelon', 'description': 'Fresh watermelon', 'calories': 30},
        {'meal_name': 'Cantaloupe', 'description': 'Fresh cantaloupe', 'calories': 34},
        {'meal_name': 'Papaya', 'description': 'Fresh papaya', 'calories': 43},
        {'meal_name': 'Orange', 'description': 'Fresh orange', 'calories': 62},
        {'meal_name': 'Pear', 'description': 'Fresh pear', 'calories': 57},
        {'meal_name': 'Peach', 'description': 'Fresh peach', 'calories': 59},
        {'meal_name': 'Plum', 'description': 'Fresh plum', 'calories': 46},
        
        # Vegetables
        {'meal_name': 'Carrot', 'description': 'Fresh carrot', 'calories': 41},
        {'meal_name': 'Sweet Potato', 'description': 'Cooked sweet potato', 'calories': 103},
        {'meal_name': 'Cucumber', 'description': 'Fresh cucumber', 'calories': 16},
        {'meal_name': 'Bell Pepper', 'description': 'Fresh bell pepper', 'calories': 31},
        {'meal_name': 'Kale', 'description': 'Fresh kale', 'calories': 33},
        {'meal_name': 'Romaine Lettuce', 'description': 'Fresh romaine lettuce', 'calories': 17},
        {'meal_name': 'Collard Greens', 'description': 'Fresh collard greens', 'calories': 32},
        {'meal_name': 'Spinach', 'description': 'Fresh spinach', 'calories': 23},
        {'meal_name': 'Broccoli', 'description': 'Fresh broccoli', 'calories': 34},
        {'meal_name': 'Cauliflower', 'description': 'Fresh cauliflower', 'calories': 25},
        {'meal_name': 'Green Beans', 'description': 'Fresh green beans', 'calories': 31},
        {'meal_name': 'Zucchini', 'description': 'Fresh zucchini', 'calories': 17},
        {'meal_name': 'Tomato', 'description': 'Fresh tomato', 'calories': 22},
        {'meal_name': 'Cabbage', 'description': 'Fresh cabbage', 'calories': 22},
        
        # Grains & Protein Sources
        {'meal_name': 'Cooked Rice', 'description': 'White rice, cooked', 'calories': 130},
        {'meal_name': 'Brown Rice', 'description': 'Brown rice, cooked', 'calories': 111},
        {'meal_name': 'Oatmeal', 'description': 'Cooked oatmeal', 'calories': 68},
        {'meal_name': 'Lentils', 'description': 'Cooked lentils', 'calories': 116},
        {'meal_name': 'Boiled Egg', 'description': 'Hard boiled egg', 'calories': 78},
        {'meal_name': 'Almonds', 'description': 'Raw almonds (small portion)', 'calories': 164},
        {'meal_name': 'Peanuts', 'description': 'Raw peanuts (small portion)', 'calories': 166},
        {'meal_name': 'Sunflower Seeds', 'description': 'Raw sunflower seeds (small portion)', 'calories': 164},
        
        # Enrichment Treats
        {'meal_name': 'Fruit Smoothie', 'description': 'Blended fruit smoothie', 'calories': 120},
        {'meal_name': 'Popcorn', 'description': 'Plain air-popped popcorn', 'calories': 31},
        {'meal_name': 'Dried Apricots', 'description': 'Dried apricots', 'calories': 48},
        {'meal_name': 'Dried Cranberries', 'description': 'Dried cranberries', 'calories': 46},
        {'meal_name': 'Raisins', 'description': 'Dried raisins', 'calories': 85},
        {'meal_name': 'Fruit Juice Ice Pop', 'description': 'Natural fruit juice ice pop', 'calories': 45},
        {'meal_name': 'Yogurt', 'description': 'Plain yogurt', 'calories': 59},
        {'meal_name': 'Cottage Cheese', 'description': 'Low-fat cottage cheese', 'calories': 98},
        
        # Mixed Meals
        {'meal_name': 'Fruit Salad', 'description': 'Mixed fresh fruit salad', 'calories': 85},
        {'meal_name': 'Vegetable Mix', 'description': 'Mixed fresh vegetables', 'calories': 45},
        {'meal_name': 'Rice and Vegetables', 'description': 'Cooked rice with mixed vegetables', 'calories': 175},
        {'meal_name': 'Oatmeal with Fruit', 'description': 'Oatmeal topped with fresh fruit', 'calories': 125},
        {'meal_name': 'Egg and Vegetables', 'description': 'Boiled egg with fresh vegetables', 'calories': 120},
    ]
    
    for food_data in foods_data:
        recipe = Recipe(**food_data)
        add_to_db(recipe, "recipe")
        print(f"Added food: {recipe.meal_name} ({recipe.calories} cal)")

def seed_sample_meals():
    """Seed some sample meals for demonstration"""
    
    # Clear existing meals
    Meals.query.delete()
    
    # Get apes and recipes
    apes = Apes.query.all()
    recipes = Recipe.query.all()
    
    if not apes or not recipes:
        print("No apes or recipes found. Please run seed_apes() and seed_foods() first.")
        return
    
    # Create sample meals for the last 7 days
    for i in range(7):
        meal_date = datetime.now() - timedelta(days=i)
        
        for ape in apes:
            # Add 2-3 meals per day per ape
            for meal_count in range(2, 4):
                recipe = recipes[meal_count % len(recipes)]  # Cycle through recipes
                
                meal = Meals(
                    ape_id=ape.id,
                    recipe_id=recipe.id,
                    date=meal_date.replace(hour=8 + (meal_count * 4), minute=30)
                )
                add_to_db(meal, "meal")
    
    print(f"Added sample meals for {len(apes)} apes over the last 7 days")

def main():
    """Main seeding function"""
    print("Starting database seeding...")
    
    with app.app_context():
        try:
            seed_apes()
            print("\n" + "="*50 + "\n")
            
            seed_foods()
            print("\n" + "="*50 + "\n")
            
            seed_sample_meals()
            print("\n" + "="*50 + "\n")
            
            print("Database seeding completed successfully!")
            
        except Exception as e:
            print(f"Error during seeding: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    main() 