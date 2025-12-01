from backend.extensions import db
from backend.models.entry import Meals, Apes, Recipe
import sys
import sqlalchemy as sa
from datetime import datetime

def add_to_db(table_object, name):
    """Add an initialized table object to the database."""
    try:
        db.session.add(table_object)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Could not update the {name} table: {e}", file=sys.stderr)

def query_meals():
    """Query meals with joins."""
    query = db.select(
        Meals.date,
        Apes.ape_name,
        Recipe.meal_name,
        Recipe.calories
    ).select_from(Meals).join(Apes).join(Recipe)
    return db.session.execute(query).all()

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
        str: Time period ('morning', 'afternoon', 'evening', 'night')
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
    else:  # 0 <= hour < 6
        return 'night'

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
    
    period_display = {
        'morning': 'Morning',
        'afternoon': 'Afternoon',
        'evening': 'Evening',
        'night': 'Night'
    }
    
    period_name = period_display.get(period, 'Unknown')
    date_str = dt.strftime('%m/%d/%Y')
    
    return f"{date_str} - {period_name}"
