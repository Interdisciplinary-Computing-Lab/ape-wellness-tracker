"""
Main app routes (e.g., homepage, adding apes, recipes, meals)

Defines the main web routes for the Ape Wellness Tracker Flask application.
"""

from flask import Blueprint, render_template, request, redirect, url_for
from backend.extensions import db
from backend.models.entry import Apes, Recipe, Meals
from backend.helpers import add_to_db, query_db
from datetime import datetime

# Blueprint for site-wide routes
site = Blueprint('site', __name__)


@site.route("/")
def index():
    # Query all apes
    apes = Apes.query.all()
    
    # Query all recipes
    recipes = Recipe.query.all()
    
    # Query all meals
    meals = Meals.query.all()
    
    return render_template(
        "index.html",
        apes=apes,
        recipes=recipes,
        meals=meals
    )


@site.route('/add_ape', methods=['POST'])
def add_ape():
    """
    Handles submission for adding a new ape.
    """
    ape_name = request.form.get("Input Ape")
    if ape_name:
        new_ape = Apes(ape_name=ape_name)
        add_to_db(new_ape, "ape")
    else:
        print("Need to fill in all forms.")
    return redirect(url_for('site.index'))


@site.route('/add_recipe', methods=['POST'])
def add_recipe():
    """
    Handles submission for adding a new recipe.
    """
    meal_name = request.form.get("Recipe Name")
    description = request.form.get("Description")
    calories = request.form.get("Calories")

    if all([meal_name, calories]):
        new_recipe = Recipe(meal_name=meal_name,
                            description=description,
                            calories=calories)
        add_to_db(new_recipe, "recipe")
    else:
        print("Need to fill in all forms.")
    return redirect(url_for('site.index'))


@site.route('/add_meal', methods=['POST'])
def add_meal():
    """
    Handles submission for adding a new meal.
    """
    meal_name = request.form.get("Select Meal")
    ape_name = request.form.get("Select Ape")
    new_meal = Meals(meal_name=meal_name, ape_name=ape_name)

    if request.form.get("Date"):
        date = datetime.strptime(request.form["Date"], "%Y-%m-%d")
        new_meal.date = date

    if all([meal_name, ape_name]):
        add_to_db(new_meal, "meal")
    else:
        print("Need to fill in meal and ape forms.")
    return redirect(url_for('site.index'))
