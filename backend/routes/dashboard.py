"""
Dashboard routes for the Ape Wellness Tracker application.
"""

from flask import render_template
from backend.models.entry import Apes, Recipe, Meals
from flask_security import login_required
from datetime import datetime
from backend.routes import site


@site.route('/')
@site.route('/dashboard')
@login_required
def dashboard():
    """Display the main dashboard"""
    # Get all active apes (not archived)
    apes = Apes.query.filter_by(is_archived=False).all()
    
    # Get all recipes
    recipes = Recipe.query.all()
    
    # Get recent meals (last 20)
    recent_meals = Meals.query.order_by(Meals.date.desc()).limit(20).all()
    
    # Calculate today's statistics
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_meals = Meals.query.filter(Meals.date >= today_start).all()
    total_meals_today = len(today_meals)
    total_calories_today = sum(meal.recipe.calories for meal in today_meals)
    
    return render_template('dashboard.html',
                         apes=apes,
                         recipes=recipes,
                         recent_meals=recent_meals,
                         total_meals_today=total_meals_today,
                         total_calories_today=total_calories_today,
                         today_date=datetime.now().strftime('%Y-%m-%d'))

