"""
Recipe/Food management routes for the Ape Wellness Tracker application.
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from backend.extensions import db
from backend.models.entry import Recipe, FoodCategory
from backend.helpers import add_to_db, sync_recipe_category
from flask_security import login_required
from backend.routes import site
from backend.utils.authz import catalog_create_required, catalog_write_required


def _nonnegative_float(value, default=0.0):
    """Parse an optional nutrition value without allowing negative amounts."""
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return default


def _recipe_json(recipe):
    """Serialize a recipe for API responses."""
    return {
        'id': recipe.id,
        'meal_name': recipe.meal_name,
        'calories': recipe.calories,
        'quantity': recipe.quantity,
        'unit_of_measurement': recipe.unit_of_measurement,
        'source': recipe.source,
        'food_category': recipe.food_category,
        'description': recipe.description,
        'gram_weight': recipe.gram_weight,
        'protein_g': recipe.protein_g,
        'fiber_g': recipe.fiber_g,
        'is_favorite': bool(recipe.is_favorite),
    }


@site.route('/add_recipe', methods=['POST'])
@login_required
@catalog_create_required
def add_recipe():
    """
    Handle submission for adding a new recipe to the database.
    """
    meal_name = request.form.get("meal_name")
    description = request.form.get("description")
    calories = request.form.get("calories")

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


@site.route('/recipes/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
@catalog_write_required
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
            quantity = request.form.get('quantity', '1.0')
            try:
                recipe.quantity = float(quantity)
            except (ValueError, TypeError):
                recipe.quantity = 1.0
            recipe.unit_of_measurement = request.form.get('unit_of_measurement', '')
            recipe.source = request.form.get('source', '')
            recipe.protein_g = _nonnegative_float(
                request.form.get('protein_g'), recipe.protein_g or 0.0
            )
            recipe.fiber_g = _nonnegative_float(
                request.form.get('fiber_g'), recipe.fiber_g or 0.0
            )
            sync_recipe_category(recipe, request.form.get('food_category', 'Other'))
            
            db.session.commit()
            
            flash(f'Food item "{recipe.meal_name}" has been updated successfully.', 'success')
            return redirect(url_for('site.manage_foods'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating food item: {str(e)}', 'error')
            return redirect(url_for('site.manage_foods'))
    
    categories = FoodCategory.query.filter_by(is_active=True).order_by(
        FoodCategory.sort_order, FoodCategory.name
    ).all()
    return render_template('edit_recipe.html', recipe=recipe, categories=categories)


@site.route('/recipes/<int:recipe_id>/delete', methods=['POST'])
@login_required
@catalog_write_required
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


@site.route('/manage_foods')
@login_required
def manage_foods():
    """Display food management page"""
    recipes = Recipe.query.order_by(
        Recipe.is_favorite.desc(), Recipe.meal_name
    ).all()
    categories = FoodCategory.query.filter_by(is_active=True).order_by(FoodCategory.sort_order, FoodCategory.name).all()
    
    return render_template('manage_foods.html', recipes=recipes, categories=categories)


@site.route('/api/recipes', methods=['POST'])
@login_required
@catalog_create_required
def create_recipe():
    """Create a new recipe via API"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('meal_name') or not data.get('calories'):
            return jsonify({'success': False, 'message': 'Food name and calories are required'})
        
        # Create new recipe
        quantity = float(data.get('quantity', 1.0))
        new_recipe = Recipe(
            meal_name=data['meal_name'],
            calories=int(data['calories']),
            quantity=quantity,
            unit_of_measurement=data.get('unit_of_measurement', ''),
            source=data.get('source', ''),
            description=data.get('description', ''),
            protein_g=_nonnegative_float(data.get('protein_g')),
            fiber_g=_nonnegative_float(data.get('fiber_g')),
        )
        sync_recipe_category(new_recipe, data.get('food_category', 'Other'))
        
        db.session.add(new_recipe)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Food item created successfully',
            'recipe': {
                **_recipe_json(new_recipe),
                'catalog_serving_label': new_recipe.catalog_serving_label(),
                'is_custom_food': new_recipe.is_custom_food,
            },
        })
    except Exception as e:
        db.session.rollback()
        # If unique name conflict, return existing recipe so UI can refresh
        meal_name = (request.get_json() or {}).get('meal_name')
        if meal_name:
            existing = Recipe.query.filter_by(meal_name=meal_name).first()
            if existing:
                return jsonify({
                    'success': True,
                    'message': 'Food already exists',
                    'recipe': {
                        **_recipe_json(existing),
                        'catalog_serving_label': existing.catalog_serving_label(),
                        'is_custom_food': existing.is_custom_food,
                    },
                })
        return jsonify({'success': False, 'message': str(e)})


@site.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
@login_required
@catalog_write_required
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
        if data.get('quantity') is not None:
            recipe.quantity = float(data['quantity'])
        if data.get('unit_of_measurement') is not None:
            recipe.unit_of_measurement = data['unit_of_measurement']
        if data.get('source') is not None:
            recipe.source = data['source']
        if data.get('food_category') is not None:
            sync_recipe_category(recipe, data['food_category'])
        if data.get('description') is not None:
            recipe.description = data['description']
        if data.get('protein_g') is not None:
            recipe.protein_g = _nonnegative_float(data['protein_g'])
        if data.get('fiber_g') is not None:
            recipe.fiber_g = _nonnegative_float(data['fiber_g'])
        if 'is_favorite' in data:
            recipe.is_favorite = bool(data['is_favorite'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Food item updated successfully',
            'recipe': _recipe_json(recipe),
        })
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
            'recipe': _recipe_json(recipe),
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@site.route('/api/recipes/<int:recipe_id>/favorite', methods=['POST'])
@login_required
@catalog_create_required
def toggle_recipe_favorite(recipe_id):
    """Toggle shared staff favorite flag for a recipe."""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        recipe.is_favorite = not recipe.is_favorite
        db.session.commit()
        status = 'added to' if recipe.is_favorite else 'removed from'
        return jsonify({
            'success': True,
            'is_favorite': recipe.is_favorite,
            'message': f'"{recipe.meal_name}" {status} favorites',
            'recipe': _recipe_json(recipe),
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})


@site.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
@login_required
@catalog_write_required
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
@catalog_create_required
def add_recipe_form():
    """Add a new recipe via form submission"""
    try:
        meal_name = request.form.get('meal_name')
        calories = request.form.get('calories')
        quantity = request.form.get('quantity', '1.0')
        unit_of_measurement = request.form.get('unit_of_measurement', '')
        source = request.form.get('source', '')
        food_category = request.form.get('food_category')
        description = request.form.get('description', '')
        protein_g = _nonnegative_float(request.form.get('protein_g'))
        fiber_g = _nonnegative_float(request.form.get('fiber_g'))
        
        if not meal_name or not calories:
            flash('Food name and calories are required.', 'error')
            return redirect(url_for('site.manage_foods'))
        
        # Check if recipe already exists
        existing_recipe = Recipe.query.filter_by(meal_name=meal_name).first()
        if existing_recipe:
            flash(f'A food item named "{meal_name}" already exists.', 'error')
            return redirect(url_for('site.manage_foods'))
        
        try:
            quantity_float = float(quantity)
        except (ValueError, TypeError):
            quantity_float = 1.0
        
        new_recipe = Recipe(
            meal_name=meal_name,
            calories=int(calories),
            quantity=quantity_float,
            unit_of_measurement=unit_of_measurement,
            source=source,
            description=description,
            protein_g=protein_g,
            fiber_g=fiber_g,
        )
        sync_recipe_category(new_recipe, food_category)
        
        db.session.add(new_recipe)
        db.session.commit()
        
        flash(f'"{meal_name}" has been added successfully.', 'success')
        return redirect(url_for('site.manage_foods'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding food item: {str(e)}', 'error')
        return redirect(url_for('site.manage_foods'))

