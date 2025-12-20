"""
Food category management routes for the Ape Wellness Tracker application.
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from backend.extensions import db
from backend.models.entry import FoodCategory, Recipe
from flask_security import login_required
from backend.routes import site


@site.route('/manage_categories')
@login_required
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

