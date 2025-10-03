"""
Main app routes for the Ape Wellness Tracker Flask application.

This module defines all the main web routes for the application, including
the homepage, routes to add, edit, and delete apes, recipes, and meals.
Each route is responsible for handling the corresponding CRUD operations
and rendering the appropriate templates.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from backend.extensions import db
from backend.models.entry import Apes, Recipe, Meals, FoodCategory
from backend.helpers import add_to_db, query_db
from datetime import datetime, timedelta
from flask_security import login_required, roles_required, current_user, change_user_password
import io
import os
import csv
import json
from werkzeug.utils import secure_filename

# Blueprint for site-wide routes
site = Blueprint('site', __name__)

# Allowed file extensions for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@site.route('/')
@site.route('/dashboard')
@login_required
def dashboard():
    """Display the main dashboard"""
    # Get all apes
    apes = Apes.query.all()
    
    # Get all recipes
    recipes = Recipe.query.all()
    
    # Get recent meals (last 20)
    recent_meals = Meals.query.order_by(Meals.date.desc()).limit(20).all()
    
    # Calculate today's statistics
    from datetime import datetime, timedelta
    today = datetime.now().date()
    today_meals = Meals.query.filter(Meals.date >= today).all()
    total_meals_today = len(today_meals)
    total_calories_today = sum(meal.recipe.calories for meal in today_meals)
    
    return render_template('dashboard.html',
                         apes=apes,
                         recipes=recipes,
                         recent_meals=recent_meals,
                         total_meals_today=total_meals_today,
                         total_calories_today=total_calories_today,
                         today_date=datetime.now().strftime('%Y-%m-%d'))


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
        # Convert age to birthday (approximate)
        from datetime import datetime, timedelta
        today = datetime.now().date()
        birthday = today - timedelta(days=int(age) * 365)
        new_ape = Apes(ape_name=ape_name, birthday=birthday)
        add_to_db(new_ape, "ape")
    else:
        print("Need to fill in all forms.")
    return redirect(url_for('site.dashboard'))


@site.route('/create_ape', methods=['GET', 'POST'])
@login_required
def create_ape():
    """
    Display and handle the form for creating a new ape.
    """
    if request.method == 'POST':
        ape_name = request.form.get("ape_name")
        birthday_str = request.form.get("birthday")
        weight = request.form.get("weight")
        mother = request.form.get("mother")
        
        if ape_name and birthday_str:
            try:
                from datetime import datetime
                birthday = datetime.strptime(birthday_str, "%Y-%m-%d").date()
                new_ape = Apes(
                    ape_name=ape_name, 
                    birthday=birthday,
                    weight=float(weight) if weight else None,
                    mother=mother if mother else None
                )
                
                # Handle image upload if provided
                if 'image' in request.files:
                    file = request.files['image']
                    if file and file.filename != '':
                        # Check file size
                        file.seek(0, os.SEEK_END)
                        file_size = file.tell()
                        file.seek(0)
                        
                        if file_size <= MAX_FILE_SIZE and allowed_file(file.filename):
                            # Read file data
                            image_data = file.read()
                            mime_type = file.content_type or 'image/jpeg'
                            
                            # Set image data
                            new_ape.image_data = image_data
                            new_ape.image_mime_type = mime_type
                            
                            # Set filename for backward compatibility
                            filename = secure_filename(f"{ape_name.lower().replace(' ', '_')}.jpg")
                            new_ape.image_filename = filename
                
                add_to_db(new_ape, "ape")
                flash(f'Ape "{ape_name}" created successfully!', 'success')
                return redirect(url_for('site.all_apes'))
            except ValueError:
                flash('Invalid birthday format. Please use YYYY-MM-DD.', 'error')
        else:
            flash('Please fill in all required fields.', 'error')
    
    return render_template('create_ape.html')


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
    return redirect(url_for('site.dashboard'))


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
        return redirect(url_for('site.dashboard'))

    date = datetime.strptime(date_str, "%Y-%m-%d")

    new_meal = Meals(
        ape_id=int(ape_id),
        recipe_id=int(recipe_id),
        date=date,
        user_id=current_user.id
    )

    add_to_db(new_meal, "meal")
    return redirect(url_for('site.dashboard'))


@site.route('/apes/<int:ape_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ape(ape_id):
    """
    Display and handle the form for editing an existing ape.
    """
    ape = Apes.query.get_or_404(ape_id)
    if request.method == 'POST':
        ape.ape_name = request.form['ape_name']
        birthday_str = request.form['birthday']
        weight = request.form.get('weight')
        mother = request.form.get('mother')
        
        try:
            from datetime import datetime
            ape.birthday = datetime.strptime(birthday_str, "%Y-%m-%d").date()
            ape.weight = float(weight) if weight else None
            ape.mother = mother if mother else None
            
            # Handle image upload if provided
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '':
                    # Check file size
                    file.seek(0, os.SEEK_END)
                    file_size = file.tell()
                    file.seek(0)
                    
                    if file_size <= MAX_FILE_SIZE and allowed_file(file.filename):
                        # Read file data
                        image_data = file.read()
                        mime_type = file.content_type or 'image/jpeg'
                        
                        # Update image data
                        ape.image_data = image_data
                        ape.image_mime_type = mime_type
                        
                        # Update filename for backward compatibility
                        filename = secure_filename(f"{ape.ape_name.lower().replace(' ', '_')}.jpg")
                        ape.image_filename = filename
                        
                        flash(f'Profile photo updated for {ape.ape_name}!', 'success')
                    else:
                        flash('Invalid image file. Please upload a valid image under 5MB.', 'error')
            
            db.session.commit()
            flash(f'{ape.ape_name} information updated successfully!', 'success')
            return redirect(url_for('site.ape_profile_page', ape_id=ape.id))
        except ValueError:
            flash('Invalid birthday format. Please use YYYY-MM-DD.', 'error')
    
    return render_template('edit_ape.html', ape=ape)


@site.route('/recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
@roles_required("Admin")
def edit_recipe(recipe_id):
    """
    Display and handle the form for editing an existing recipe.
    """
    recipe = Recipe.query.get_or_404(recipe_id)
    if request.method == 'POST':
        try:
            recipe.meal_name = request.form['meal_name']
            recipe.description = request.form.get('description', '')
            recipe.calories = int(request.form['calories'])
            recipe.food_category = request.form.get('food_category', 'Other')
            
            db.session.commit()
            
            flash(f'Food item "{recipe.meal_name}" has been updated successfully.', 'success')
            return redirect(url_for('site.manage_foods'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating food item: {str(e)}', 'error')
            return redirect(url_for('site.manage_foods'))
    
    return render_template('edit_recipe.html', recipe=recipe)


@site.route('/meals/<int:meal_id>/edit', methods=['GET', 'POST'])
@roles_required("Admin")
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
        return redirect(url_for('site.dashboard'))
    return render_template('edit_meal.html', meal=meal, apes=apes, recipes=recipes)


@site.route('/apes/<int:ape_id>/delete', methods=['POST'])
@login_required
def delete_ape(ape_id):
    """
    Delete an ape from the database.
    """
    ape = Apes.query.get_or_404(ape_id)
    ape_name = ape.ape_name
    db.session.delete(ape)
    db.session.commit()
    flash(f'{ape_name} has been removed from the system.', 'success')
    return redirect(url_for('site.all_apes'))





@site.route('/recipes/<int:recipe_id>/delete', methods=['POST'])
@roles_required("Admin")
def delete_recipe_form(recipe_id):
    """
    Delete a recipe from the database via form submission.
    """
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        recipe_name = recipe.meal_name
        
        # Check if recipe is used in any meals
        if recipe.meals:
            flash(f'Cannot delete food item "{recipe_name}" because it is used in {len(recipe.meals)} existing meals.', 'error')
            return redirect(url_for('site.manage_foods'))
        
        db.session.delete(recipe)
        db.session.commit()
        
        flash(f'Food item "{recipe_name}" has been deleted successfully.', 'success')
        return redirect(url_for('site.manage_foods'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting food item: {str(e)}', 'error')
        return redirect(url_for('site.manage_foods'))

@site.route('/meals/<int:meal_id>/delete', methods=['POST'])
@roles_required("Admin")
def delete_meal(meal_id):
    """
    Delete a meal from the database.
    """
    meal = Meals.query.get_or_404(meal_id)
    db.session.delete(meal)
    db.session.commit()
    return redirect(url_for('site.dashboard'))


@site.route('/log_feeding')
@login_required
def log_feeding():
    """
    Display the log feeding page for adding nutrition data.
    """
    # Get URL parameters for pre-filled data
    pre_filled_food = request.args.get('food', '')
    pre_filled_calories = request.args.get('calories', '')
    pre_filled_ape = request.args.get('ape', '')
    
    # Get all apes for selection
    apes = Apes.query.all()
    
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
    Handle feeding log submissions from the JavaScript interface.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
        
        ape_ids = data.get('ape_ids', [])
        feeding_items = data.get('feeding_items', [])
        feeding_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        if not ape_ids:
            return jsonify({'success': False, 'error': 'No apes selected'}), 400
        
        if not feeding_items:
            return jsonify({'success': False, 'error': 'No food items added'}), 400
        
        # Convert date string to datetime
        try:
            feeding_datetime = datetime.strptime(feeding_date, '%Y-%m-%d')
        except ValueError:
            feeding_datetime = datetime.now()
        
        saved_meals = []
        total_calories = 0
        
        # For each food item, create a recipe if it doesn't exist, then create meals for each ape
        for item in feeding_items:
            food_name = item.get('name', '').strip()
            calories = item.get('calories', 0)
            quantity = item.get('quantity', 1)
            
            if not food_name or calories <= 0:
                continue
            
            # Check if recipe exists, create if not
            recipe = Recipe.query.filter_by(meal_name=food_name).first()
            if not recipe:
                # Determine food category based on name
                food_name_lower = food_name.lower()
                food_category = 'Other'
                
                # Simple category detection
                if any(fruit in food_name_lower for fruit in ['banana', 'apple', 'orange', 'grapes', 'mango', 'papaya', 'watermelon', 'strawberries', 'blueberries', 'pineapple']):
                    food_category = 'Fruits'
                elif any(veg in food_name_lower for veg in ['carrot', 'broccoli', 'spinach', 'lettuce', 'cucumber', 'tomato', 'pepper', 'potato', 'kale', 'cauliflower']):
                    food_category = 'Vegetables'
                elif any(protein in food_name_lower for protein in ['chicken', 'fish', 'egg', 'bean', 'nut', 'seed', 'tofu', 'yogurt', 'cheese', 'lentil']):
                    food_category = 'Protein'
                elif any(grain in food_name_lower for grain in ['rice', 'bread', 'pasta', 'oat', 'quinoa', 'corn', 'wheat']):
                    food_category = 'Grains'
                elif any(treat in food_name_lower for treat in ['honey', 'chocolate', 'cookie', 'ice cream', 'smoothie', 'popcorn']):
                    food_category = 'Treats'
                
                recipe = Recipe(
                    meal_name=food_name,
                    description=f"Quick added: {food_name}",
                    calories=calories,
                    food_category=food_category
                )
                add_to_db(recipe, "recipe")
            
            # Create meals for each selected ape
            for ape_id in ape_ids:
                meal = Meals(
                    ape_id=int(ape_id),
                    recipe_id=recipe.id,
                    date=feeding_datetime,
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
            'message': f'Feeding logged successfully for {len(ape_ids)} ape(s)',
            'saved_meals': saved_meals,
            'total_calories': total_calories,
            'ape_count': len(ape_ids)
        })
        
    except Exception as e:
        print(f"Error saving feeding: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to save feeding data'}), 500





@site.route('/ape/<int:ape_id>')
@login_required
def ape_profile_page(ape_id):
    """Display individual ape profile page"""
    ape = Apes.query.get_or_404(ape_id)
    
    # Get recent meals for this ape (last 20)
    recent_meals = Meals.query.filter_by(ape_id=ape_id)\
                              .order_by(Meals.date.desc())\
                              .limit(20)\
                              .all()
    
    # Calculate nutrition summary for last 7 days
    from datetime import datetime, timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_meals_week = Meals.query.filter(
        Meals.ape_id == ape_id,
        Meals.date >= seven_days_ago
    ).all()
    
    total_calories_week = sum(meal.recipe.calories for meal in recent_meals_week)
    avg_calories_per_meal = total_calories_week / len(recent_meals_week) if recent_meals_week else 0
    
    # Prepare chart data for pie charts
    from collections import defaultdict
    from sqlalchemy import func
    
    # Food category distribution (all time)
    category_data = db.session.query(
        Recipe.food_category,
        func.count(Meals.id).label('count'),
        func.sum(Recipe.calories).label('total_calories')
    ).join(Meals).filter(Meals.ape_id == ape_id)\
     .group_by(Recipe.food_category)\
     .all()
    
    pie_chart_data = {
        'labels': [cat.food_category or 'Other' for cat in category_data],
        'counts': [cat.count for cat in category_data],
        'calories': [cat.total_calories for cat in category_data],
        'colors': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF']
    }
    
    # Monthly calorie trends for Superset (SQLite compatible)
    monthly_trends = db.session.query(
        func.strftime('%Y-%m', Meals.date).label('month'),
        func.sum(Recipe.calories).label('total_calories'),
        func.count(Meals.id).label('meal_count')
    ).join(Recipe).filter(Meals.ape_id == ape_id)\
     .group_by(func.strftime('%Y-%m', Meals.date))\
     .order_by(func.strftime('%Y-%m', Meals.date))\
     .all()
    
    return render_template('ape_profile.html', 
                         ape=ape,
                         recent_meals=recent_meals,
                         recent_meals_week=recent_meals_week,
                         total_calories_week=total_calories_week,
                         avg_calories_per_meal=avg_calories_per_meal,
                         pie_chart_data=pie_chart_data,
                         now=datetime.now(),
                         timedelta=timedelta)


@site.route('/apes')
@login_required
def all_apes():
    apes = Apes.query.all()
    return render_template('all_apes.html', apes=apes)


@site.route('/manage_foods')
@login_required
def manage_foods():
    """Display food management page"""
    recipes = Recipe.query.all()
    categories = FoodCategory.query.filter_by(is_active=True).order_by(FoodCategory.sort_order, FoodCategory.name).all()
    
    # Debug: Print counts
    print(f"DEBUG: Found {len(recipes)} recipes and {len(categories)} categories")
    if recipes:
        print(f"DEBUG: First recipe: {recipes[0].meal_name}")
    
    return render_template('manage_foods.html', recipes=recipes, categories=categories)


@site.route('/api/recipes', methods=['POST'])
@login_required
def create_recipe():
    """Create a new recipe via API"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('meal_name') or not data.get('calories'):
            return jsonify({'success': False, 'message': 'Food name and calories are required'})
        
        # Create new recipe
        new_recipe = Recipe(
            meal_name=data['meal_name'],
            calories=int(data['calories']),
            food_category=data.get('food_category', 'Other'),
            description=data.get('description', '')
        )
        
        db.session.add(new_recipe)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Food item created successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@site.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
@login_required
def update_recipe(recipe_id):
    """Update an existing recipe via API"""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        data = request.get_json()
        
        # Update fields
        if data.get('meal_name'):
            recipe.meal_name = data['meal_name']
        if data.get('calories'):
            recipe.calories = int(data['calories'])
        if data.get('food_category'):
            recipe.food_category = data['food_category']
        if data.get('description') is not None:
            recipe.description = data['description']
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Food item updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@site.route('/api/recipes/<int:recipe_id>', methods=['GET'])
@login_required
def get_recipe(recipe_id):
    """Get a single recipe via API"""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        return jsonify({
            'success': True,
            'recipe': {
                'id': recipe.id,
                'meal_name': recipe.meal_name,
                'calories': recipe.calories,
                'food_category': recipe.food_category,
                'description': recipe.description
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@site.route('/api/test/recipes/<int:recipe_id>', methods=['GET'])
def test_get_recipe(recipe_id):
    """Test endpoint to get a single recipe without authentication"""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        return jsonify({
            'success': True,
            'recipe': {
                'id': recipe.id,
                'meal_name': recipe.meal_name,
                'calories': recipe.calories,
                'food_category': recipe.food_category,
                'description': recipe.description
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@site.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
@login_required
def delete_recipe(recipe_id):
    """Delete a recipe via API"""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        
        # Check if recipe is used in any meals
        if recipe.meals:
            return jsonify({'success': False, 'message': 'Cannot delete food item that is used in existing meals'})
        
        db.session.delete(recipe)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Food item deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@site.route('/recipes/add', methods=['POST'])
@login_required
def add_recipe_form():
    """Add a new recipe via form submission"""
    try:
        meal_name = request.form.get('meal_name')
        calories = request.form.get('calories')
        food_category = request.form.get('food_category')
        description = request.form.get('description', '')
        
        if not meal_name or not calories:
            flash('Food name and calories are required.', 'error')
            return redirect(url_for('site.manage_foods'))
        
        # Check if recipe already exists
        existing_recipe = Recipe.query.filter_by(meal_name=meal_name).first()
        if existing_recipe:
            flash(f'A food item named "{meal_name}" already exists.', 'error')
            return redirect(url_for('site.manage_foods'))
        
        new_recipe = Recipe(
            meal_name=meal_name,
            calories=int(calories),
            food_category=food_category,
            description=description
        )
        
        db.session.add(new_recipe)
        db.session.commit()
        
        flash(f'"{meal_name}" has been added successfully.', 'success')
        return redirect(url_for('site.manage_foods'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding food item: {str(e)}', 'error')
        return redirect(url_for('site.manage_foods'))

# Food Category Management Routes
@site.route('/manage_categories')
@login_required
@roles_required("Admin")
def manage_categories():
    """Display food category management page"""
    categories = FoodCategory.query.order_by(FoodCategory.sort_order, FoodCategory.name).all()
    
    # Calculate food counts for each category
    category_counts = {}
    for category in categories:
        # Count recipes that match this category by name (using the legacy food_category field)
        count = Recipe.query.filter_by(food_category=category.name).count()
        
        # Also check for alternative category names that might be stored differently
        if count == 0:
            # Check for simplified names that might have been used
            simplified_name = category.name.split(' ')[0]  # Get first word (e.g., "Fruits" from "Fruits")
            alt_count = Recipe.query.filter_by(food_category=simplified_name).count()
            if alt_count > 0:
                count = alt_count
        
        category_counts[category.id] = count
    
    return render_template('manage_categories.html', categories=categories, category_counts=category_counts)


@site.route('/categories/add', methods=['POST'])
@login_required
@roles_required("Admin")
def add_category():
    """Add a new food category"""
    try:
        name = request.form.get('name')
        description = request.form.get('description', '')
        icon = request.form.get('icon', 'fas fa-tag')
        color = request.form.get('color', 'badge-secondary')
        sort_order = int(request.form.get('sort_order', 0))
        
        if not name:
            flash('Category name is required.', 'error')
            return redirect(url_for('site.manage_categories'))
        
        # Check if category already exists
        existing_category = FoodCategory.query.filter_by(name=name).first()
        if existing_category:
            flash(f'A category named "{name}" already exists.', 'error')
            return redirect(url_for('site.manage_categories'))
        
        new_category = FoodCategory(
            name=name,
            description=description,
            icon=icon,
            color=color,
            sort_order=sort_order
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        flash(f'Category "{name}" has been added successfully.', 'success')
        return redirect(url_for('site.manage_categories'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding category: {str(e)}', 'error')
        return redirect(url_for('site.manage_categories'))

@site.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required("Admin")
def edit_category(category_id):
    """Edit an existing food category"""
    category = FoodCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description', '')
            icon = request.form.get('icon', 'fas fa-tag')
            color = request.form.get('color', 'badge-secondary')
            sort_order = int(request.form.get('sort_order', 0))
            is_active = 'is_active' in request.form
            
            if not name:
                flash('Category name is required.', 'error')
                return render_template('edit_category.html', category=category)
            
            # Check if name changed and if new name already exists
            if name != category.name:
                existing_category = FoodCategory.query.filter_by(name=name).first()
                if existing_category:
                    flash(f'A category named "{name}" already exists.', 'error')
                    return render_template('edit_category.html', category=category)
            
            category.name = name
            category.description = description
            category.icon = icon
            category.color = color
            category.sort_order = sort_order
            category.is_active = is_active
            
            db.session.commit()
            
            flash(f'Category "{name}" has been updated successfully.', 'success')
            return redirect(url_for('site.manage_categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating category: {str(e)}', 'error')
    
    return render_template('edit_category.html', category=category)

@site.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@roles_required("Admin")
def delete_category(category_id):
    """Delete a food category"""
    try:
        category = FoodCategory.query.get_or_404(category_id)
        
        # Check if category is used by any recipes
        if category.recipes.count() > 0:
            flash(f'Cannot delete category "{category.name}" because it is used by {category.recipes.count()} food items.', 'error')
            return redirect(url_for('site.manage_categories'))
        
        db.session.delete(category)
        db.session.commit()
        
        flash(f'Category "{category.name}" has been deleted successfully.', 'success')
        return redirect(url_for('site.manage_categories'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'error')
        return redirect(url_for('site.manage_categories'))

@site.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    """Get all active food categories via API"""
    try:
        categories = FoodCategory.query.filter_by(is_active=True).order_by(FoodCategory.sort_order, FoodCategory.name).all()
        return jsonify({
            'success': True,
            'categories': [
                {
                    'id': cat.id,
                    'name': cat.name,
                    'description': cat.description,
                    'icon': cat.icon,
                    'color': cat.color
                }
                for cat in categories
            ]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@site.route('/reports')
@login_required
def reports():
    """Display aggregate reports for all apes"""
    from datetime import datetime, timedelta
    from collections import defaultdict
    from sqlalchemy import func
    
    # Get date range from query parameters (default to today)
    date_range = request.args.get('range', 'today')
    custom_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    custom_start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))
    custom_end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Calculate date range
    if date_range == 'today':
        start_date = datetime.now().date()
        end_date = datetime.now().date()
    elif date_range == 'week':
        start_date = datetime.now().date() - timedelta(days=7)
        end_date = datetime.now().date()
    elif date_range == 'month':
        start_date = datetime.now().date() - timedelta(days=30)
        end_date = datetime.now().date()
    elif date_range == 'custom':
        try:
            start_date = datetime.strptime(custom_date, '%Y-%m-%d').date()
            end_date = start_date
        except ValueError:
            start_date = datetime.now().date()
            end_date = start_date
    elif date_range == 'custom_range':
        try:
            start_date = datetime.strptime(custom_start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(custom_end_date, '%Y-%m-%d').date()
            # Ensure start_date is not after end_date
            if start_date > end_date:
                start_date, end_date = end_date, start_date
        except ValueError:
            start_date = datetime.now().date()
            end_date = start_date
    else:
        start_date = datetime.now().date()
        end_date = datetime.now().date()
    
    # Get all apes
    apes = Apes.query.all()
    
    # Get meals within date range
    meals_in_range = Meals.query.filter(
        Meals.date >= start_date,
        Meals.date <= end_date + timedelta(days=1)  # Include the entire end date
    ).all()
    
    # Calculate aggregate statistics
    total_calories = sum(meal.recipe.calories for meal in meals_in_range)
    total_meals = len(meals_in_range)
    avg_calories_per_meal = total_calories / total_meals if total_meals > 0 else 0
    
    # Calculate per-ape statistics
    ape_stats = {}
    for ape in apes:
        ape_meals = [meal for meal in meals_in_range if meal.ape_id == ape.id]
        ape_calories = sum(meal.recipe.calories for meal in ape_meals)
        ape_meal_count = len(ape_meals)
        ape_avg_calories = ape_calories / ape_meal_count if ape_meal_count > 0 else 0
        
        ape_stats[ape.id] = {
            'name': ape.ape_name,
            'calories': ape_calories,
            'meal_count': ape_meal_count,
            'avg_calories': ape_avg_calories,
            'percentage_of_total': (ape_calories / total_calories * 100) if total_calories > 0 else 0
        }
    
    # Food category distribution
    category_stats = defaultdict(lambda: {'count': 0, 'calories': 0})
    for meal in meals_in_range:
        category = meal.recipe.food_category or 'Other'
        category_stats[category]['count'] += 1
        category_stats[category]['calories'] += meal.recipe.calories
    
    # Convert to list for template
    category_data = [
        {
            'category': category,
            'count': stats['count'],
            'calories': stats['calories'],
            'percentage': (stats['calories'] / total_calories * 100) if total_calories > 0 else 0
        }
        for category, stats in category_stats.items()
    ]
    
    # Sort categories by calories
    category_data.sort(key=lambda x: x['calories'], reverse=True)
    
    # Daily breakdown for the date range
    daily_stats = defaultdict(lambda: {'calories': 0, 'meals': 0})
    for meal in meals_in_range:
        meal_date = meal.date.date()
        daily_stats[meal_date]['calories'] += meal.recipe.calories
        daily_stats[meal_date]['meals'] += 1
    
    # Convert to sorted list
    daily_data = [
        {
            'date': date,
            'calories': stats['calories'],
            'meals': stats['meals']
        }
        for date, stats in daily_stats.items()
    ]
    daily_data.sort(key=lambda x: x['date'])
    
    return render_template('reports.html',
                         apes=apes,
                         ape_stats=ape_stats,
                         total_calories=total_calories,
                         total_meals=total_meals,
                         avg_calories_per_meal=avg_calories_per_meal,
                         category_data=category_data,
                         daily_data=daily_data,
                         date_range=date_range,
                         start_date=start_date,
                         end_date=end_date,
                         custom_date=custom_date,
                         custom_start_date=custom_start_date,
                         custom_end_date=custom_end_date)


@site.route('/reports/download/<format>')
@login_required
def download_reports(format):
    """Download nutrition reports data in CSV or JSON format"""
    from datetime import datetime, timedelta
    from collections import defaultdict
    from sqlalchemy import func
    
    # Get the same date range parameters as the reports route
    date_range = request.args.get('range', 'today')
    custom_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    custom_start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))
    custom_end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Calculate date range (same logic as reports route)
    if date_range == 'today':
        start_date = datetime.now().date()
        end_date = datetime.now().date()
    elif date_range == 'week':
        start_date = datetime.now().date() - timedelta(days=7)
        end_date = datetime.now().date()
    elif date_range == 'month':
        start_date = datetime.now().date() - timedelta(days=30)
        end_date = datetime.now().date()
    elif date_range == 'custom':
        try:
            start_date = datetime.strptime(custom_date, '%Y-%m-%d').date()
            end_date = start_date
        except ValueError:
            start_date = datetime.now().date()
            end_date = start_date
    elif date_range == 'custom_range':
        try:
            start_date = datetime.strptime(custom_start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(custom_end_date, '%Y-%m-%d').date()
            if start_date > end_date:
                start_date, end_date = end_date, start_date
        except ValueError:
            start_date = datetime.now().date()
            end_date = start_date
    else:
        start_date = datetime.now().date()
        end_date = datetime.now().date()
    
    # Get all apes and meals in range
    apes = Apes.query.all()
    meals_in_range = Meals.query.filter(
        Meals.date >= start_date,
        Meals.date <= end_date + timedelta(days=1)
    ).all()
    
    # Calculate statistics (same as reports route)
    total_calories = sum(meal.recipe.calories for meal in meals_in_range)
    total_meals = len(meals_in_range)
    avg_calories_per_meal = total_calories / total_meals if total_meals > 0 else 0
    
    # Per-ape statistics
    ape_stats = {}
    for ape in apes:
        ape_meals = [meal for meal in meals_in_range if meal.ape_id == ape.id]
        ape_calories = sum(meal.recipe.calories for meal in ape_meals)
        ape_meal_count = len(ape_meals)
        ape_avg_calories = ape_calories / ape_meal_count if ape_meal_count > 0 else 0
        
        ape_stats[ape.id] = {
            'name': ape.ape_name,
            'calories': ape_calories,
            'meal_count': ape_meal_count,
            'avg_calories': ape_avg_calories,
            'percentage_of_total': (ape_calories / total_calories * 100) if total_calories > 0 else 0
        }
    
    # Food category distribution
    category_stats = defaultdict(lambda: {'count': 0, 'calories': 0})
    for meal in meals_in_range:
        category = meal.recipe.food_category or 'Other'
        category_stats[category]['count'] += 1
        category_stats[category]['calories'] += meal.recipe.calories
    
    category_data = [
        {
            'category': category,
            'count': stats['count'],
            'calories': stats['calories'],
            'percentage': (stats['calories'] / total_calories * 100) if total_calories > 0 else 0
        }
        for category, stats in category_stats.items()
    ]
    category_data.sort(key=lambda x: x['calories'], reverse=True)
    
    # Daily breakdown
    daily_stats = defaultdict(lambda: {'calories': 0, 'meals': 0})
    for meal in meals_in_range:
        meal_date = meal.date.date()
        daily_stats[meal_date]['calories'] += meal.recipe.calories
        daily_stats[meal_date]['meals'] += 1
    
    daily_data = [
        {
            'date': date.strftime('%Y-%m-%d'),
            'calories': stats['calories'],
            'meals': stats['meals']
        }
        for date, stats in daily_stats.items()
    ]
    daily_data.sort(key=lambda x: x['date'])
    
    # Generate filename with date range
    filename_date_range = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
    
    if format.lower() == 'csv':
        return generate_csv_report(filename_date_range, apes, ape_stats, category_data, daily_data, 
                                 total_calories, total_meals, avg_calories_per_meal, start_date, end_date)
    elif format.lower() == 'json':
        return generate_json_report(filename_date_range, apes, ape_stats, category_data, daily_data,
                                  total_calories, total_meals, avg_calories_per_meal, start_date, end_date)
    else:
        flash('Invalid download format. Please choose CSV or JSON.', 'error')
        return redirect(url_for('site.reports'))


def generate_csv_report(filename_date_range, apes, ape_stats, category_data, daily_data, 
                       total_calories, total_meals, avg_calories_per_meal, start_date, end_date):
    """Generate CSV report"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Report header
    writer.writerow(['Ape Wellness Tracker - Nutrition Report'])
    writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['Date Range:', f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"])
    writer.writerow([])
    
    # Summary statistics
    writer.writerow(['SUMMARY STATISTICS'])
    writer.writerow(['Total Calories', total_calories])
    writer.writerow(['Total Meals', total_meals])
    writer.writerow(['Average Calories per Meal', f"{avg_calories_per_meal:.1f}"])
    writer.writerow(['Active Apes', len(apes)])
    writer.writerow([])
    
    # Per-ape statistics
    writer.writerow(['PER-APE STATISTICS'])
    writer.writerow(['Ape Name', 'Total Calories', 'Total Meals', 'Avg Calories/Meal', '% of Total'])
    for ape in apes:
        stats = ape_stats[ape.id]
        writer.writerow([
            stats['name'],
            stats['calories'],
            stats['meal_count'],
            f"{stats['avg_calories']:.1f}",
            f"{stats['percentage_of_total']:.1f}%"
        ])
    writer.writerow([])
    
    # Food category distribution
    writer.writerow(['FOOD CATEGORY DISTRIBUTION'])
    writer.writerow(['Category', 'Meals', 'Total Calories', '% of Total'])
    for category in category_data:
        writer.writerow([
            category['category'],
            category['count'],
            category['calories'],
            f"{category['percentage']:.1f}%"
        ])
    writer.writerow([])
    
    # Daily breakdown
    writer.writerow(['DAILY BREAKDOWN'])
    writer.writerow(['Date', 'Total Calories', 'Total Meals'])
    for day in daily_data:
        writer.writerow([day['date'], day['calories'], day['meals']])
    
    # Prepare response
    output.seek(0)
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    filename = f"nutrition_report_{filename_date_range}.csv"
    return send_file(
        mem,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )


def generate_json_report(filename_date_range, apes, ape_stats, category_data, daily_data,
                        total_calories, total_meals, avg_calories_per_meal, start_date, end_date):
    """Generate JSON report"""
    report_data = {
        'report_info': {
            'generated': datetime.now().isoformat(),
            'date_range': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        },
        'summary_statistics': {
            'total_calories': total_calories,
            'total_meals': total_meals,
            'avg_calories_per_meal': round(avg_calories_per_meal, 1),
            'active_apes': len(apes)
        },
        'per_ape_statistics': [
            {
                'ape_name': ape_stats[ape.id]['name'],
                'total_calories': ape_stats[ape.id]['calories'],
                'total_meals': ape_stats[ape.id]['meal_count'],
                'avg_calories_per_meal': round(ape_stats[ape.id]['avg_calories'], 1),
                'percentage_of_total': round(ape_stats[ape.id]['percentage_of_total'], 1)
            }
            for ape in apes
        ],
        'food_category_distribution': [
            {
                'category': cat['category'],
                'meals': cat['count'],
                'total_calories': cat['calories'],
                'percentage_of_total': round(cat['percentage'], 1)
            }
            for cat in category_data
        ],
        'daily_breakdown': daily_data
    }
    
    # Prepare response
    mem = io.BytesIO()
    mem.write(json.dumps(report_data, indent=2).encode('utf-8'))
    mem.seek(0)
    
    filename = f"nutrition_report_{filename_date_range}.json"
    return send_file(
        mem,
        as_attachment=True,
        download_name=filename,
        mimetype='application/json'
    )


# Image Upload Routes

@site.route('/ape/<int:ape_id>/image')
@login_required
def ape_image(ape_id):
    """Serve ape image from BLOB data"""
    try:
        ape = Apes.query.get_or_404(ape_id)
        
        if ape.image_data and ape.image_mime_type:
            return send_file(
                io.BytesIO(ape.image_data),
                mimetype=ape.image_mime_type,
                as_attachment=False
            )
        else:
            # Fallback to static file if no BLOB data
            return redirect(url_for('static', filename='images/bonobo-placeholder.jpg'))
    except Exception as e:
        return redirect(url_for('static', filename='images/bonobo-placeholder.jpg'))


@site.route('/ape/<int:ape_id>/upload_image', methods=['POST'])
@login_required
def upload_ape_image(ape_id):
    """Upload image for an ape"""
    try:
        ape = Apes.query.get_or_404(ape_id)
        
        # Check if file was uploaded
        if 'image' not in request.files:
            flash('No image file selected', 'error')
            return redirect(url_for('site.ape_profile_page', ape_id=ape_id))
        
        file = request.files['image']
        
        # Check if file is empty
        if file.filename == '':
            flash('No image file selected', 'error')
            return redirect(url_for('site.ape_profile_page', ape_id=ape_id))
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            flash('Image file is too large. Maximum size is 5MB.', 'error')
            return redirect(url_for('site.ape_profile_page', ape_id=ape_id))
        
        # Check file extension
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload a PNG, JPG, JPEG, GIF, or WebP image.', 'error')
            return redirect(url_for('site.ape_profile_page', ape_id=ape_id))
        
        # Read file data
        image_data = file.read()
        mime_type = file.content_type or 'image/jpeg'
        
        # Update ape record with image data
        ape.image_data = image_data
        ape.image_mime_type = mime_type
        
        # Also update filename for backward compatibility
        filename = secure_filename(f"{ape.ape_name.lower().replace(' ', '_')}.jpg")
        ape.image_filename = filename
        
        db.session.commit()
        
        flash(f'Image uploaded successfully for {ape.ape_name}!', 'success')
        return redirect(url_for('site.ape_profile_page', ape_id=ape_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error uploading image: {str(e)}', 'error')
        return redirect(url_for('site.ape_profile_page', ape_id=ape_id))


@site.route('/ape/<int:ape_id>/remove_image', methods=['POST'])
@login_required
def remove_ape_image(ape_id):
    """Remove image from an ape"""
    try:
        ape = Apes.query.get_or_404(ape_id)
        
        # Clear image data
        ape.image_data = None
        ape.image_mime_type = None
        ape.image_filename = None
        
        db.session.commit()
        
        flash(f'Image removed successfully for {ape.ape_name}', 'success')
        return redirect(url_for('site.ape_profile_page', ape_id=ape_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing image: {str(e)}', 'error')
        return redirect(url_for('site.ape_profile_page', ape_id=ape_id))


@site.route('/user_profile')
@login_required
def user_profile():
    """Display user profile page"""
    return render_template('user_profile.html', user=current_user)


@site.route('/user_profile/change_password', methods=['POST'])
@login_required
def change_password():
    """Handle password change requests"""
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not all([current_password, new_password, confirm_password]):
            flash('All password fields are required.', 'error')
            return redirect(url_for('site.user_profile'))
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('site.user_profile'))
        
        if len(new_password) < 8:
            flash('New password must be at least 8 characters long.', 'error')
            return redirect(url_for('site.user_profile'))
        
        # Verify current password
        if not current_user.verify_password(current_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('site.user_profile'))
        
        # Change the password
        current_user.password = current_user.encrypt_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('site.user_profile'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error changing password: {str(e)}', 'error')
        return redirect(url_for('site.user_profile'))
