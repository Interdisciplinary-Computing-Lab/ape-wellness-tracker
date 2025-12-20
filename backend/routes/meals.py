"""
Meal logging and management routes for the Ape Wellness Tracker application.
"""

from flask import render_template, request, redirect, url_for, jsonify
from backend.extensions import db
from backend.models.entry import Apes, Recipe, Meals, FoodCategory
from backend.helpers import add_to_db
from flask_security import login_required, current_user
from datetime import datetime
from backend.routes import site


@site.route('/add_meal', methods=['POST'])
@login_required
def add_meal():
    """
    Handle submission for adding a new meal to the database.
    """
    ape_id = request.form.get("ape_id")
    recipe_id = request.form.get("recipe_id")
    date_str = request.form.get("date")

    if not all([ape_id, recipe_id, date_str]):
        print("Need to fill in all forms.")
        return redirect(url_for('dashboard.dashboard'))

    date = datetime.strptime(date_str, "%Y-%m-%d")

    new_meal = Meals(
        ape_id=int(ape_id),
        recipe_id=int(recipe_id),
        date=date,
        user_id=current_user.id
    )

    add_to_db(new_meal, "meal")
    return redirect(url_for('dashboard.dashboard'))


@site.route('/meals/<int:meal_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_meal(meal_id):
    """
    Display and handle the form for editing an existing meal.
    """
    meal = Meals.query.get_or_404(meal_id)
    apes = Apes.query.all()
    recipes = Recipe.query.all()
    
    if request.method == 'POST':
        meal.ape_id = int(request.form['ape_id'])
        meal.recipe_id = int(request.form['recipe_id'])
        meal.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        db.session.commit()
        return redirect(url_for('dashboard.dashboard'))
    return render_template('edit_meal.html', meal=meal, apes=apes, recipes=recipes)


@site.route('/meals/<int:meal_id>/delete', methods=['POST'])
@login_required
def delete_meal(meal_id):
    """
    Delete a meal from the database.
    """
    meal = Meals.query.get_or_404(meal_id)
    db.session.delete(meal)
    db.session.commit()
    return redirect(url_for('dashboard.dashboard'))


@site.route('/log_feeding')
@login_required
def log_feeding():
    """
    Display the log meals page for adding nutrition data.
    """
    # Get URL parameters for pre-filled data
    pre_filled_food = request.args.get('food', '')
    pre_filled_calories = request.args.get('calories', '')
    pre_filled_ape = request.args.get('ape', '')
    
    # Get all active apes for selection (not archived)
    apes = Apes.query.filter_by(is_archived=False).all()
    
    # Get all available foods from database, grouped by category
    recipes = Recipe.query.order_by(Recipe.food_category, Recipe.meal_name).all()
    
    # Get all food categories for filtering
    categories = FoodCategory.query.filter_by(is_active=True).order_by(FoodCategory.sort_order).all()
    
    # Group recipes by category for easier template rendering
    foods_by_category = {}
    for recipe in recipes:
        category = recipe.food_category or 'Other'
        if category not in foods_by_category:
            foods_by_category[category] = []
        foods_by_category[category].append(recipe)
    
    return render_template('log_feeding.html', 
                         apes=apes,
                         recipes=recipes,
                         foods_by_category=foods_by_category,
                         categories=categories,
                         pre_filled_food=pre_filled_food,
                         pre_filled_calories=pre_filled_calories,
                         pre_filled_ape=pre_filled_ape)


@site.route('/save_feeding', methods=['POST'])
@login_required
def save_feeding():
    """
    Handle meal log submissions from the JavaScript interface.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        ape_ids = data.get('ape_ids', [])
        feeding_items = data.get('feeding_items', [])
        feeding_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        feeding_period = data.get('feeding_period', 'morning')  # Default to morning
        
        if not ape_ids:
            return jsonify({'success': False, 'error': 'No apes selected'}), 400
        
        if not feeding_items:
            return jsonify({'success': False, 'error': 'No food items added'}), 400
        
        # Convert date string to datetime and set time based on period
        try:
            feeding_datetime = datetime.strptime(feeding_date, '%Y-%m-%d')
            
            # Load period hours from config file
            from backend.utils.config_loader import get_feeding_period_hour
            hour = get_feeding_period_hour(feeding_period)
            feeding_datetime = feeding_datetime.replace(hour=hour, minute=0, second=0, microsecond=0)
            
        except ValueError:
            feeding_datetime = datetime.now()
        
        saved_meals = []
        total_calories = 0
        
        # For each food item, create a recipe if it doesn't exist, then create meals for each ape
        for item in feeding_items:
            food_name = item.get('name', '').strip()
            calories = item.get('calories', 0)
            quantity = float(item.get('quantity', 1))  # Can be float now (e.g., 0.5)
            unit = item.get('unit', '')
            
            if not food_name or calories <= 0:
                continue
            
            # Check if recipe exists, create if not
            recipe = Recipe.query.filter_by(meal_name=food_name).first()
            if not recipe:
                # Use default category from database (first active category, or 'Other')
                # Users can edit the category later through the food management interface
                from backend.models.entry import FoodCategory
                default_category = FoodCategory.query.filter_by(is_active=True).first()
                food_category = default_category.name if default_category else 'Other'
                
                # Load default nutrition values from config
                from backend.utils.config_loader import get_nutrition_defaults
                nutrition_defaults = get_nutrition_defaults()
                
                # For custom foods, use quantity=1.0 as base (the calories are for this base quantity)
                # The unit can be empty for custom foods
                recipe = Recipe(
                    meal_name=food_name,
                    description=f"Quick added: {food_name}",
                    calories=calories,
                    quantity=1.0,  # Base quantity for custom foods
                    unit_of_measurement=unit if unit else None,
                    source=None,  # Source removed from meal logging
                    food_category=food_category,
                    protein_g=nutrition_defaults['protein_g'],
                    fiber_g=nutrition_defaults['fiber_g']
                )
                add_to_db(recipe, "recipe")
            
            # Create meals for each selected ape
            for ape_id in ape_ids:
                meal = Meals(
                    ape_id=int(ape_id),
                    recipe_id=recipe.id,
                    date=feeding_datetime,
                    feeding_period=feeding_period,
                    user_id=current_user.id
                )
                add_to_db(meal, "meal")
                saved_meals.append({
                    'ape_id': ape_id,
                    'recipe_name': food_name,
                    'calories': calories * quantity
                })
                total_calories += calories * quantity
        
        return jsonify({
            'success': True,
            'message': f'Meals logged successfully for {len(ape_ids)} ape(s)',
            'saved_meals': saved_meals,
            'total_calories': total_calories,
            'ape_count': len(ape_ids)
        })
        
    except Exception as e:
        print(f"Error saving meals: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to save meal data'}), 500

