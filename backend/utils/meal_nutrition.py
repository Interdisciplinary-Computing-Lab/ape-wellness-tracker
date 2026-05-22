"""
Helpers for per-meal nutrition (logged portions vs. catalog Recipe defaults).
"""


def meal_calories(meal):
    """Calories for this feeding event; falls back to recipe catalog value."""
    if meal.calories_logged is not None:
        return meal.calories_logged
    if meal.recipe:
        return meal.recipe.calories
    return 0


def meal_serving_scale(meal):
    """Ratio of logged portion to recipe base (1.0 = one catalog serving)."""
    if not meal.recipe or not meal.recipe.calories:
        return 1.0
    if meal.calories_logged is not None:
        return meal.calories_logged / meal.recipe.calories
    return 1.0


def meal_protein_g(meal):
    base = 2.0
    if meal.recipe and meal.recipe.protein_g is not None:
        base = meal.recipe.protein_g
    return round(base * meal_serving_scale(meal), 1)


def meal_fiber_g(meal):
    base = 1.0
    if meal.recipe and meal.recipe.fiber_g is not None:
        base = meal.recipe.fiber_g
    return round(base * meal_serving_scale(meal), 1)
