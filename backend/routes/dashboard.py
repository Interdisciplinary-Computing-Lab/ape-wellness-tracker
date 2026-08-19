"""
Dashboard routes for the Ape Wellness Tracker application.
"""

from flask import render_template
from backend.models.entry import Apes, Recipe, Meals
from backend.utils.meal_nutrition import meal_calories
from backend.utils.meal_queries import meals_for_current_user, recent_meals_for_current_user
from backend.utils.meal_types import (
    DEFAULT_MEAL_TYPE,
    MEAL_TYPES,
    MEAL_TYPE_LABELS,
)
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
    
    recent_meals = recent_meals_for_current_user(limit=30)

    # Today's statistics — meals whose feeding date is today (server calendar)
    today = datetime.now().date()
    today_meals = meals_for_current_user().filter(func.date(Meals.date) == today).all()
    total_meals_today = len(today_meals)
    total_calories_today = sum(meal_calories(meal) for meal in today_meals)

    # Per-ape daily totals include all staff logs (shared care view for the kitchen)
    facility_today_meals = Meals.query.filter(func.date(Meals.date) == today).all()
    ape_calories_today = {}
    ape_meal_calories_today = {}
    for meal in facility_today_meals:
        cal = meal_calories(meal)
        ape_calories_today[meal.ape_id] = ape_calories_today.get(meal.ape_id, 0) + cal
        meal_label = meal.resolved_meal_type
        if meal_label not in MEAL_TYPES:
            meal_label = DEFAULT_MEAL_TYPE
        by_meal = ape_meal_calories_today.setdefault(
            meal.ape_id,
            {label: 0 for label in MEAL_TYPES},
        )
        by_meal[meal_label] += cal
    
    edit_apes = apes

    return render_template('dashboard.html',
                         apes=apes,
                         edit_apes=edit_apes,
                         recipes=recipes,
                         recent_meals=recent_meals,
                         total_meals_today=total_meals_today,
                         total_calories_today=total_calories_today,
                         ape_calories_today=ape_calories_today,
                         ape_meal_calories_today=ape_meal_calories_today,
                         feeding_period_meal_labels=MEAL_TYPE_LABELS,
                         today_date=datetime.now().strftime('%Y-%m-%d'))
