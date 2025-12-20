"""
Nutrition calculation utilities for the Ape Wellness Tracker application.

DEPRECATED: This module is kept for backward compatibility during migration.
Nutrition data should now be stored in the Recipe model (protein_g, fiber_g fields).
Category detection should use the FoodCategory database model instead.
"""


# These functions are deprecated but kept for migration scripts
# New code should use Recipe.protein_g, Recipe.fiber_g and FoodCategory model

def get_protein_fiber(meal_name):
    """
    DEPRECATED: Calculate realistic protein and fiber values based on meal name.
    
    This function is deprecated. Use Recipe.protein_g and Recipe.fiber_g from the database instead.
    Kept only for migration scripts.
    
    Returns tuple (protein_g, fiber_g).
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


def detect_food_category(food_name):
    """
    DEPRECATED: Detect food category based on food name.
    
    This function is deprecated. Use the FoodCategory database model instead.
    Kept only for migration scripts.
    
    Returns category name string.
    """
    if not food_name:
        return 'Other'
    
    food_name_lower = food_name.lower()
    
    # Simple category detection
    if any(fruit in food_name_lower for fruit in ['banana', 'apple', 'orange', 'grapes', 'mango', 'papaya', 'watermelon', 'strawberries', 'blueberries', 'pineapple']):
        return 'Fruits'
    elif any(veg in food_name_lower for veg in ['carrot', 'broccoli', 'spinach', 'lettuce', 'cucumber', 'tomato', 'pepper', 'potato', 'kale', 'cauliflower']):
        return 'Vegetables'
    elif any(protein in food_name_lower for protein in ['chicken', 'fish', 'egg', 'bean', 'nut', 'seed', 'tofu', 'yogurt', 'cheese', 'lentil']):
        return 'Protein'
    elif any(grain in food_name_lower for grain in ['rice', 'bread', 'pasta', 'oat', 'quinoa', 'corn', 'wheat']):
        return 'Grains'
    elif any(treat in food_name_lower for treat in ['honey', 'chocolate', 'cookie', 'ice cream', 'smoothie', 'popcorn']):
        return 'Treats'
    
    return 'Other'

