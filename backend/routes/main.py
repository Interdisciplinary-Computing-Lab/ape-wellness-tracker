"""
Main app routes for the Ape Wellness Tracker Flask application.

This module defines all the main web routes for the application, including
the homepage, routes to add, edit, and delete apes, recipes, and meals.
Each route is responsible for handling the corresponding CRUD operations
and rendering the appropriate templates.
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
    """
    Render the homepage with lists of all apes, recipes, and meals.

    Returns:
        Rendered index.html template with apes, recipes, and meals data.
    """
    apes = Apes.query.all()
    recipes = Recipe.query.all()
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
    Handle submission for adding a new ape to the database.

    Returns:
        Redirects to the homepage after processing the form.
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
    Handle submission for adding a new recipe to the database.

    Returns:
        Redirects to the homepage after processing the form.
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
    Handle submission for adding a new meal to the database.

    Returns:
        Redirects to the homepage after processing the form.
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

@site.route('/apes/<int:ape_id>/edit', methods=['GET', 'POST'])
def edit_ape(ape_id):
    """
    Display and handle the form for editing an existing ape.

    Args:
        ape_id (int): The ID of the ape to edit.

    Returns:
        GET: Renders the edit_ape.html template with the ape data.
        POST: Updates the ape and redirects to the homepage.
    """
    ape = Apes.query.get_or_404(ape_id)
    if request.method == 'POST':
        ape.ape_name = request.form['ape_name']
        ape.age = int(request.form['age'])
        db.session.commit()
        return redirect(url_for('site.index'))
    return render_template('edit_ape.html', ape=ape)

@site.route('/recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    """
    Display and handle the form for editing an existing recipe.

    Args:
        recipe_id (int): The ID of the recipe to edit.

    Returns:
        GET: Renders the edit_recipe.html template with the recipe data.
        POST: Updates the recipe and redirects to the homepage.
    """
    recipe = Recipe.query.get_or_404(recipe_id)
    if request.method == 'POST':
        recipe.meal_name = request.form['meal_name']
        recipe.description = request.form['description']
        recipe.calories = int(request.form['calories'])
        db.session.commit()
        return redirect(url_for('site.index'))
    return render_template('edit_recipe.html', recipe=recipe)

@site.route('/meals/<int:meal_id>/edit', methods=['GET', 'POST'])
def edit_meal(meal_id):
    """
    Display and handle the form for editing an existing meal.

    Args:
        meal_id (int): The ID of the meal to edit.

    Returns:
        GET: Renders the edit_meal.html template with the meal data.
        POST: Updates the meal and redirects to the homepage.
    """
    meal = Meals.query.get_or_404(meal_id)
    if request.method == 'POST':
        meal.ape_id = int(request.form['ape_id'])
        meal.recipe_id = int(request.form['recipe_id'])
        meal.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        db.session.commit()
        return redirect(url_for('site.index'))
    return render_template('edit_meal.html', meal=meal)

@site.route('/apes/<int:ape_id>/delete', methods=['POST'])
def delete_ape(ape_id):
    """
    Delete an ape from the database.

    Args:
        ape_id (int): The ID of the ape to delete.

    Returns:
        Redirects to the homepage after deletion.
    """
    ape = Apes.query.get_or_404(ape_id)
    db.session.delete(ape)
    db.session.commit()
    return redirect(url_for('site.index'))

@site.route('/recipes/<int:recipe_id>/delete', methods=['POST'])
def delete_recipe(recipe_id):
    """
    Delete a recipe from the database.

    Args:
        recipe_id (int): The ID of the recipe to delete.

    Returns:
        Redirects to the homepage after deletion.
    """
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    return redirect(url_for('site.index'))

@site.route('/meals/<int:meal_id>/delete', methods=['POST'])
def delete_meal(meal_id):
    """
    Delete a meal from the database.

    Args:
        meal_id (int): The ID of the meal to delete.

    Returns:
        Redirects to the homepage after deletion.
    """
    meal = Meals.query.get_or_404(meal_id)
    db.session.delete(meal)
    db.session.commit()
    return redirect(url_for('site.index'))