from backend.extensions import db
from backend.models.entry import Meals, Apes, Recipe
import sys
import sqlalchemy as sa

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
