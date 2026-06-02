"""
Ape management routes for the Ape Wellness Tracker application.
"""

from flask import render_template, request, redirect, url_for, flash
from backend.extensions import db
from backend.models.entry import Apes, Meals, Recipe
from backend.helpers import add_to_db
from backend.utils.file_utils import allowed_file, MAX_FILE_SIZE
from flask_security import login_required, roles_required
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from backend.routes import site
import os


@site.route('/add_ape', methods=['POST'])
@login_required
def add_ape():
    """
    Handle submission for adding a new ape to the database.
    """
    ape_name = request.form.get("ape_name")
    age = request.form.get("age")

    if ape_name and age:
        # Convert age to birthday (approximate)
        today = datetime.now().date()
        birthday = today - timedelta(days=int(age) * 365)
        new_ape = Apes(ape_name=ape_name, birthday=birthday)
        add_to_db(new_ape, "ape")
    else:
        print("Need to fill in all forms.")
    return redirect(url_for('dashboard.dashboard'))


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
        
        if ape_name and birthday_str:
            try:
                birthday = datetime.strptime(birthday_str, "%Y-%m-%d").date()
                new_ape = Apes(
                    ape_name=ape_name, 
                    birthday=birthday,
                    weight=float(weight) if weight else None,
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
        
        try:
            ape.birthday = datetime.strptime(birthday_str, "%Y-%m-%d").date()
            ape.weight = float(weight) if weight else None
            
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


@site.route('/apes/<int:ape_id>/archive', methods=['POST'])
@login_required
def archive_ape(ape_id):
    """
    Archive an ape instead of deleting it.
    """
    ape = Apes.query.get_or_404(ape_id)
    ape_name = ape.ape_name
    if ape.is_archived:
        flash(f'{ape_name} is already archived.', 'info')
        return redirect(url_for('site.archived_apes'))

    try:
        ape.is_archived = True
        ape.archived_at = datetime.now()
        db.session.commit()
        flash(
            f'{ape_name} has been archived. View archived apes from the sidebar under Apes.',
            'success',
        )
        return redirect(url_for('site.archived_apes'))
    except Exception as e:
        db.session.rollback()
        flash(f'Could not archive {ape_name}: {e}', 'error')
        return redirect(url_for('site.ape_profile_page', ape_id=ape_id))


@site.route('/apes/<int:ape_id>/unarchive', methods=['POST'])
@login_required
def unarchive_ape(ape_id):
    """
    Unarchive an ape to restore it to active status.
    """
    ape = Apes.query.get_or_404(ape_id)
    ape_name = ape.ape_name
    ape.is_archived = False
    ape.archived_at = None
    db.session.commit()
    flash(f'{ape_name} has been restored from archive.', 'success')
    return redirect(url_for('site.archived_apes'))


@site.route('/apes/<int:ape_id>/delete', methods=['POST'])
@login_required
@roles_required("Admin")
def delete_ape(ape_id):
    """
    Permanently delete an ape from the database (Admin only).
    This should only be used for archived apes.
    """
    ape = Apes.query.get_or_404(ape_id)
    ape_name = ape.ape_name
    
    # Check if ape has any meals - if so, we need to handle them
    if ape.meals:
        # For safety, we'll delete all associated meals first
        for meal in ape.meals:
            db.session.delete(meal)
    
    # Delete the ape
    db.session.delete(ape)
    db.session.commit()
    
    flash(f'{ape_name} has been permanently deleted from the system.', 'success')
    return redirect(url_for('site.archived_apes'))


@site.route('/archived_apes')
@login_required
def archived_apes():
    """
    Display all archived apes.
    """
    archived_apes_list = Apes.query.filter_by(is_archived=True).order_by(Apes.archived_at.desc()).all()
    return render_template('archived_apes.html', apes=archived_apes_list)


@site.route('/apes')
@login_required
def all_apes():
    """Display all active apes"""
    apes = Apes.query.filter_by(is_archived=False).all()
    return render_template('all_apes.html', apes=apes)


@site.route('/ape/<int:ape_id>')
@login_required
def ape_profile_page(ape_id):
    """Display individual ape profile page"""
    from datetime import timedelta
    from sqlalchemy import func
    from backend.models.entry import Recipe
    from backend.utils.meal_nutrition import meal_calories
    
    ape = Apes.query.get_or_404(ape_id)
    
    # Recent meals for activity feed and summary (queried fresh, not stale relationship cache)
    recent_meals = (
        Meals.query.filter_by(ape_id=ape_id)
        .order_by(Meals.date.desc(), Meals.id.desc())
        .limit(30)
        .all()
    )
    
    # Calculate nutrition summary for last 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_meals_week = Meals.query.filter(
        Meals.ape_id == ape_id,
        Meals.date >= seven_days_ago
    ).all()
    
    total_calories_week = sum(meal_calories(meal) for meal in recent_meals_week)
    avg_calories_per_meal = total_calories_week / len(recent_meals_week) if recent_meals_week else 0
    
    # Prepare chart data for pie charts
    # Food category distribution (all time)
    effective_calories = func.coalesce(Meals.calories_logged, Recipe.calories)
    category_data = db.session.query(
        Recipe.food_category,
        func.count(Meals.id).label('count'),
        func.sum(effective_calories).label('total_calories')
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
        func.sum(effective_calories).label('total_calories'),
        func.count(Meals.id).label('meal_count')
    ).join(Recipe).filter(Meals.ape_id == ape_id)\
     .group_by(func.strftime('%Y-%m', Meals.date))\
     .order_by(func.strftime('%Y-%m', Meals.date))\
     .all()
    
    edit_apes = Apes.query.filter_by(is_archived=False).order_by(Apes.ape_name).all()
    recipes = Recipe.query.order_by(Recipe.food_category, Recipe.meal_name).all()

    return render_template('ape_profile.html', 
                         ape=ape,
                         edit_apes=edit_apes,
                         recipes=recipes,
                         recent_meals=recent_meals,
                         recent_meals_week=recent_meals_week,
                         total_calories_week=total_calories_week,
                         avg_calories_per_meal=avg_calories_per_meal,
                         pie_chart_data=pie_chart_data,
                         now=datetime.now(),
                         timedelta=timedelta)

