"""
Helpers for loading and updating saved meal log entries (edit modal API).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend.models.entry import FoodCategory, Recipe
from backend.utils.config_loader import get_feeding_period_hour, get_nutrition_defaults
from backend.utils.meal_nutrition import meal_calories, meal_serving_scale


def feeding_datetime_from_parts(date_str: str, feeding_period: str) -> datetime:
    feeding_datetime = datetime.strptime(date_str, '%Y-%m-%d')
    hour = get_feeding_period_hour(feeding_period or 'morning')
    return feeding_datetime.replace(hour=hour, minute=0, second=0, microsecond=0)


def meal_to_edit_dict(meal) -> dict:
    """Serialize a Meals row for the edit modal."""
    recipe = meal.recipe
    if not recipe:
        return {
            'id': meal.id,
            'ape_id': meal.ape_id,
            'ape_name': meal.ape.ape_name if meal.ape else '',
            'recipe_id': meal.recipe_id,
            'food_name': '',
            'date': meal.date.strftime('%Y-%m-%d') if meal.date else '',
            'feeding_period': meal.feeding_period or 'morning',
            'calories_logged': meal_calories(meal),
            'catalog_calories': 0,
            'quantity': 1.0,
            'recipe_quantity': 1.0,
            'unit': 'serving',
            'source': '',
            'gram_weight': 0,
            'protein_g': 0,
            'fiber_g': 0,
        }

    scale = meal_serving_scale(meal)
    recipe_qty = recipe.quantity if recipe.quantity and recipe.quantity > 0 else 1.0
    logged_qty = recipe_qty * scale

    return {
        'id': meal.id,
        'ape_id': meal.ape_id,
        'ape_name': meal.ape.ape_name if meal.ape else '',
        'recipe_id': recipe.id,
        'food_name': recipe.meal_name,
        'date': meal.date.strftime('%Y-%m-%d') if meal.date else '',
        'feeding_period': meal.feeding_period or 'morning',
        'calories_logged': meal_calories(meal),
        'catalog_calories': recipe.calories or 0,
        'quantity': round(logged_qty, 2) if logged_qty != int(logged_qty) else int(logged_qty),
        'recipe_quantity': recipe_qty,
        'unit': recipe.unit_of_measurement or 'serving',
        'unit_raw': recipe.unit_of_measurement or '',
        'source': recipe.source or '',
        'gram_weight': recipe.gram_weight or 0,
        'protein_g': recipe.protein_g if recipe.protein_g is not None else 0,
        'fiber_g': recipe.fiber_g if recipe.fiber_g is not None else 0,
    }


def resolve_recipe_for_edit(data: dict) -> Optional[Recipe]:
    recipe_id = data.get('recipe_id')
    if recipe_id:
        return Recipe.query.get(int(recipe_id))
    food_name = (data.get('food_name') or '').strip()
    if food_name:
        return Recipe.query.filter_by(meal_name=food_name).first()
    return None


def ensure_recipe_for_edit(data: dict, logged_calories: int) -> Recipe:
    recipe = resolve_recipe_for_edit(data)
    if recipe:
        return recipe

    food_name = (data.get('food_name') or '').strip()
    if not food_name:
        raise ValueError('Food name is required')

    nutrition_defaults = get_nutrition_defaults()
    default_category = FoodCategory.query.filter_by(is_active=True).first()
    food_category = default_category.name if default_category else 'Other'
    unit = (data.get('unit') or '').strip() or None
    source = (data.get('source') or '').strip() or None

    recipe = Recipe(
        meal_name=food_name,
        description=f"Quick added: {food_name}",
        calories=max(logged_calories, 1),
        quantity=1.0,
        unit_of_measurement=unit,
        source=source,
        food_category=food_category,
        protein_g=nutrition_defaults['protein_g'],
        fiber_g=nutrition_defaults['fiber_g'],
    )
    return recipe


def apply_meal_edit(meal, data: dict) -> None:
    """Apply JSON payload from edit modal to an existing Meals row."""
    ape_id = data.get('ape_id')
    if ape_id is not None:
        meal.ape_id = int(ape_id)

    calories = int(data.get('calories', 0) or 0)
    quantity = float(data.get('quantity', 1) or 1)
    if quantity <= 0:
        quantity = 1.0
    logged_calories = max(0, round(calories * quantity))

    recipe = ensure_recipe_for_edit(data, logged_calories)
    if not recipe.id:
        from backend.extensions import db
        db.session.add(recipe)
        db.session.flush()

    meal.recipe_id = recipe.id
    meal.calories_logged = logged_calories

    date_str = data.get('date')
    feeding_period = data.get('feeding_period') or meal.feeding_period or 'morning'
    if date_str:
        meal.date = feeding_datetime_from_parts(date_str, feeding_period)
    meal.feeding_period = feeding_period

    source = (data.get('source') or '').strip()
    if source and not recipe.source:
        recipe.source = source
