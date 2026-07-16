"""
Meal logging and management routes for the Ape Wellness Tracker application.
"""

from flask import render_template, request, redirect, url_for, jsonify
from backend.extensions import db
from backend.models.entry import Apes, Recipe, Meals, FoodCategory
from flask_security import login_required, current_user
from datetime import datetime
import re
from backend.routes import site
from backend.utils.meal_queries import get_user_meal_or_404


def _recipe_unit_label(unit, recipe_quantity):
    """Format unit_of_measurement so catalog quick-add parses quantity + unit correctly."""
    unit = (unit or '').strip()
    if not unit:
        return None
    if re.match(r'^\d', unit):
        return unit
    qty = recipe_quantity if recipe_quantity and recipe_quantity > 0 else 1.0
    if qty == 1.0 or qty == 1:
        return unit
    if qty == int(qty):
        return f'{int(qty)} {unit}'
    qty_str = f'{qty:.2f}'.rstrip('0').rstrip('.')
    return f'{qty_str} {unit}'


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
    recipe = Recipe.query.get(int(recipe_id))

    now = datetime.now()
    new_meal = Meals(
        ape_id=int(ape_id),
        recipe_id=int(recipe_id),
        date=date,
        logged_at=now,
        calories_logged=recipe.calories if recipe else None,
        user_id=current_user.id
    )

    db.session.add(new_meal)
    db.session.commit()
    return redirect(url_for('dashboard.dashboard'))


@site.route('/meals/<int:meal_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_meal(meal_id):
    """
    Display and handle the form for editing an existing meal.
    """
    meal = get_user_meal_or_404(meal_id)
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
    meal = get_user_meal_or_404(meal_id)
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
    recipes = Recipe.query.order_by(
        Recipe.is_favorite.desc(), Recipe.food_category, Recipe.meal_name
    ).all()
    
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
                         pre_filled_ape=pre_filled_ape,
                         default_feeding_date=datetime.now().strftime('%Y-%m-%d'))


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
        if feeding_period == 'night':
            feeding_period = 'evening'
        from backend.utils.config_loader import get_meal_type_for_period
        meal_type = (data.get('meal_type') or '').strip()
        if meal_type not in ('Breakfast', 'Lunch', 'Dinner'):
            meal_type = get_meal_type_for_period(feeding_period)
        
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
        from datetime import timedelta
        logged_at = datetime.now()
        from backend.utils.config_loader import get_nutrition_defaults
        nutrition_defaults = get_nutrition_defaults()

        try:
            for item in feeding_items:
                food_name = item.get('name', '').strip()
                calories = int(item.get('calories', 0) or 0)
                quantity = float(item.get('quantity', 1))
                recipe_quantity = float(item.get('recipe_quantity', 0) or 0)
                unit = item.get('unit', '')
                source = (item.get('source') or '').strip() or None

                if not food_name or calories <= 0:
                    continue

                if quantity <= 0:
                    quantity = 1.0
                logged_calories = max(0, round(calories * quantity))

                if recipe_quantity > 0:
                    catalog_calories = calories
                    catalog_quantity = recipe_quantity
                    catalog_unit = _recipe_unit_label(unit, catalog_quantity)
                else:
                    catalog_calories = max(calories, logged_calories)
                    catalog_quantity = 1.0
                    catalog_unit = unit if unit else None

                recipe = Recipe.query.filter_by(meal_name=food_name).first()
                if not recipe:
                    from backend.helpers import sync_recipe_category
                    food_category = (item.get('food_category') or '').strip() or 'Other'
                    recipe = Recipe(
                        meal_name=food_name,
                        description=f"Quick added: {food_name}",
                        calories=catalog_calories,
                        quantity=catalog_quantity,
                        unit_of_measurement=catalog_unit,
                        source=source or 'Custom',
                        protein_g=nutrition_defaults['protein_g'],
                        fiber_g=nutrition_defaults['fiber_g'],
                    )
                    sync_recipe_category(recipe, food_category)
                    db.session.add(recipe)
                    db.session.flush()
                else:
                    if source and not recipe.source:
                        recipe.source = source
                    food_category = (item.get('food_category') or '').strip()
                    if food_category and recipe.is_custom_food:
                        from backend.helpers import sync_recipe_category
                        sync_recipe_category(recipe, food_category)

                if not recipe.id:
                    raise ValueError(f"Could not resolve recipe for {food_name}")

                for ape_id in ape_ids:
                    meal = Meals(
                        ape_id=int(ape_id),
                        recipe_id=recipe.id,
                        date=feeding_datetime,
                        logged_at=logged_at,
                        feeding_period=feeding_period,
                        meal_type=meal_type,
                        calories_logged=logged_calories,
                        user_id=current_user.id,
                    )
                    db.session.add(meal)
                    saved_meals.append({
                        'ape_id': ape_id,
                        'recipe_name': food_name,
                        'calories': logged_calories,
                    })
                    total_calories += logged_calories
                    logged_at += timedelta(microseconds=1)

            if not saved_meals:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': 'No meals were saved. Check that each food has calories greater than zero.',
                }), 400

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return jsonify({
            'success': True,
            'message': f'Meals logged successfully for {len(ape_ids)} ape(s)',
            'saved_meals': saved_meals,
            'total_calories': total_calories,
            'ape_count': len(ape_ids),
            'meal_count': len(saved_meals),
            'feeding_date': feeding_datetime.strftime('%Y-%m-%d'),
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to save meal data'}), 500


@site.route('/api/meals/<int:meal_id>', methods=['GET'])
@login_required
def api_get_meal(meal_id):
    """Load one saved meal for the edit modal."""
    meal = get_user_meal_or_404(meal_id)
    from backend.utils.meal_edit import meal_to_edit_dict
    return jsonify({'success': True, 'meal': meal_to_edit_dict(meal)})


@site.route('/api/meals/<int:meal_id>', methods=['PATCH'])
@login_required
def api_update_meal(meal_id):
    """Update a saved meal from the edit modal."""
    meal = get_user_meal_or_404(meal_id)
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data received'}), 400

    calories = int(data.get('calories', 0) or 0)
    if calories <= 0:
        return jsonify({'success': False, 'error': 'Calories must be greater than zero'}), 400

    try:
        from backend.utils.meal_edit import apply_meal_edit, meal_to_edit_dict
        apply_meal_edit(meal, data)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Meal updated',
            'meal': meal_to_edit_dict(meal),
        })
    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to update meal'}), 500


@site.route('/api/meals/<int:meal_id>', methods=['DELETE'])
@login_required
def api_delete_meal(meal_id):
    """Delete a saved meal from the edit modal."""
    meal = get_user_meal_or_404(meal_id)
    try:
        db.session.delete(meal)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Meal removed'})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to delete meal'}), 500
