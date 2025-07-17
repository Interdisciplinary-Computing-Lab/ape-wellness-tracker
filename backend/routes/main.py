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
from flask_security import login_required, roles_required, current_user

# Blueprint for site-wide routes
site = Blueprint('site', __name__)

@site.route("/")
@login_required
def index():
    """
    Render the homepage with lists of all apes, recipes, and meals.
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
@login_required
def add_ape():
    """
    Handle submission for adding a new ape to the database.
    """
    ape_name = request.form.get("ape_name")
    age = request.form.get("age")

    print("FORM DATA:", request.form)

    if ape_name and age:
        new_ape = Apes(ape_name=ape_name, age=int(age))
        add_to_db(new_ape, "ape")
    else:
        print("Need to fill in all forms.")
    return redirect(url_for('site.index'))


@site.route('/add_recipe', methods=['POST'])
@login_required
def add_recipe():
    """
    Handle submission for adding a new recipe to the database.
    """
    meal_name = request.form.get("meal_name")
    description = request.form.get("description")
    calories = request.form.get("calories")

    print("FORM DATA:", request.form)

    if meal_name and calories:
        new_recipe = Recipe(
            meal_name=meal_name,
            description=description,
            calories=int(calories)
        )
        add_to_db(new_recipe, "recipe")
    else:
        print("Need to fill in all forms.")
    return redirect(url_for('site.index'))


@site.route('/add_meal', methods=['POST'])
@login_required
def add_meal():
    """
    Handle submission for adding a new meal to the database.
    """
    ape_id = request.form.get("ape_id")
    recipe_id = request.form.get("recipe_id")
    date_str = request.form.get("date")

    print("FORM DATA:", request.form)

    if not all([ape_id, recipe_id, date_str]):
        print("Need to fill in all forms.")
        return redirect(url_for('site.index'))

    date = datetime.strptime(date_str, "%Y-%m-%d")

    new_meal = Meals(
        ape_id=int(ape_id),
        recipe_id=int(recipe_id),
        date=date
    )

    add_to_db(new_meal, "meal")
    return redirect(url_for('site.index'))


@site.route('/apes/<int:ape_id>/edit', methods=['GET', 'POST'])
@roles_required("Admin")
def edit_ape(ape_id):
    """
    Display and handle the form for editing an existing ape.
    """
    ape = Apes.query.get_or_404(ape_id)
    if request.method == 'POST':
        ape.ape_name = request.form['ape_name']
        ape.age = int(request.form['age'])
        db.session.commit()
        return redirect(url_for('site.index'))
    return render_template('edit_ape.html', ape=ape)


@site.route('/recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
@roles_required("Admin")
def edit_recipe(recipe_id):
    """
    Display and handle the form for editing an existing recipe.
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
@roles_required("Admin")
def edit_meal(meal_id):
    """
    Display and handle the form for editing an existing meal.
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
@roles_required("Admin")
def delete_ape(ape_id):
    """
    Delete an ape from the database.
    """
    ape = Apes.query.get_or_404(ape_id)
    db.session.delete(ape)
    db.session.commit()
    return redirect(url_for('site.index'))


@site.route('/recipes/<int:recipe_id>/delete', methods=['POST'])
@roles_required("Admin")
def delete_recipe(recipe_id):
    """
    Delete a recipe from the database.
    """
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    return redirect(url_for('site.index'))


@site.route('/meals/<int:meal_id>/delete', methods=['POST'])
@roles_required("Admin")
def delete_meal(meal_id):
    """
    Delete a meal from the database.
    """
    meal = Meals.query.get_or_404(meal_id)
    db.session.delete(meal)
    db.session.commit()
    return redirect(url_for('site.index'))


@site.route('/log_feeding')
@login_required
def log_feeding():
    """
    Display the log feeding page for adding nutrition data.
    """
    # In a real application, you would fetch available apes and food items
    # For now, we'll use placeholder data
    return render_template('log_feeding.html')


@site.route('/apes/<int:ape_id>/profile')
@login_required
def ape_profile_page(ape_id):
    """
    Display the profile page for a specific ape.
    """
    ape = Apes.query.get_or_404(ape_id)
    return render_template('ape_profile.html', ape=ape)


@site.route('/apes')
@login_required
def all_apes():
    apes = Apes.query.all()
    return render_template('all_apes.html', apes=apes)
