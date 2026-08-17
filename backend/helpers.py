from backend.extensions import db
from backend.models.entry import Meals, Apes, Recipe, FoodCategory
from backend.utils.meal_queries import meals_for_current_user
import sys
import sqlalchemy as sa
from datetime import datetime

def sync_recipe_category(recipe, food_category_name):
    """Keep recipe.food_category and recipe.category_id in sync."""
    name = (food_category_name or 'Other').strip() or 'Other'
    recipe.food_category = name
    cat = FoodCategory.query.filter_by(name=name, is_active=True).first()
    recipe.category_id = cat.id if cat else None


def add_to_db(table_object, name):
    """Add an initialized table object to the database."""
    try:
        db.session.add(table_object)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Could not update the {name} table: {e}", file=sys.stderr)

def query_meals():
    """Query current user's meals with joins."""
    return (
        meals_for_current_user()
        .join(Apes)
        .join(Recipe)
        .with_entities(Meals.date, Apes.ape_name, Recipe.meal_name, Recipe.calories)
        .all()
    )

def query_db():
    """Return all apes, recipes, and meals."""
    apes = Apes.query.all()
    recipes = Recipe.query.all()
    meals = query_meals()
    return (apes, recipes, meals)

def get_time_period(dt):
    """
    Convert a datetime object to a time period string.
    
    Args:
        dt: datetime object
        
    Returns:
        str: Time period ('morning', 'afternoon', or 'evening')
    """
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    
    hour = dt.hour
    
    if 6 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 18:
        return 'afternoon'
    elif 18 <= hour < 24:
        return 'evening'
    else:  # 0 <= hour < 6 — overnight maps to the morning period
        return 'morning'

def get_time_period_display(dt):
    """
    Convert a datetime object to a formatted string with date and time period.
    This matches the time periods used in the log meals form.
    
    Args:
        dt: datetime object
        
    Returns:
        str: Formatted string (e.g., '10/15/2025 - Morning')
    """
    period = get_time_period(dt)
    if period == 'night':
        period = 'evening'
    
    period_display = {
        'morning': 'Morning',
        'afternoon': 'Afternoon',
        'evening': 'Evening',
    }
    
    period_name = period_display.get(period, 'Unknown')
    date_str = dt.strftime('%m/%d/%Y')
    
    return f"{date_str} - {period_name}"
