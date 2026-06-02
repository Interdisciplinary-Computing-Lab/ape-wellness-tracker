"""
Dashboard routes for the Ape Wellness Tracker application.
"""

from flask import render_template
from backend.models.entry import Apes, Recipe, Meals
from backend.utils.meal_nutrition import meal_calories
from flask_security import login_required
from datetime import datetime
from sqlalchemy import func
from backend.routes import site


@site.route('/')
@site.route('/dashboard')
@login_required
def dashboard():
    """Display the main dashboard"""
    # Get all active apes (not archived)
    apes = Apes.query.filter_by(is_archived=False).all()
    
    recipes = Recipe.query.order_by(Recipe.food_category, Recipe.meal_name).all()
    
    # Recent activity (newest first)
    recent_meals = (
        Meals.query
        .order_by(Meals.date.desc(), Meals.id.desc())
        .limit(30)
        .all()
    )

    # Today's statistics — calendar day only (exclude future-dated logs)
    today = datetime.now().date()
    today_meals = Meals.query.filter(func.date(Meals.date) == today).all()
    total_meals_today = len(today_meals)
    total_calories_today = sum(meal_calories(meal) for meal in today_meals)
    
    edit_apes = apes

    return render_template('dashboard.html',
                         apes=apes,
                         edit_apes=edit_apes,
                         recipes=recipes,
                         recent_meals=recent_meals,
                         total_meals_today=total_meals_today,
                         total_calories_today=total_calories_today,
                         today_date=datetime.now().strftime('%Y-%m-%d'))

