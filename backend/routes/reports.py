"""
Reports and data export routes for the Ape Wellness Tracker application.
"""

from flask import render_template, request, redirect, url_for, flash, send_file, current_app
from backend.extensions import db
from backend.models.entry import Apes, Recipe, Meals
from backend.utils.report_utils import generate_csv_report
from backend.utils.report_generators import generate_individual_summary, generate_group_and_category_breakdown
from flask_security import login_required
from datetime import datetime, timedelta
from collections import defaultdict
from backend.routes import site
import pandas as pd
import sqlite3
import io
import tempfile
import os


def calculate_date_range():
    """Calculate date range from query parameters"""
    date_range = request.args.get('range', 'today')
    today_str = datetime.now().date().strftime('%Y-%m-%d')
    custom_date = request.args.get('date', today_str)
    custom_start_date = request.args.get('start_date', today_str)
    custom_end_date = request.args.get('end_date', today_str)
    
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
    
    return start_date, end_date, date_range, custom_date, custom_start_date, custom_end_date


def get_meals_in_range(start_date, end_date):
    """Get meals within date range"""
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    return Meals.query.filter(
        Meals.date >= start_datetime,
        Meals.date <= end_datetime
    ).all()


@site.route('/reports')
@login_required
def reports():
    """Display aggregate reports for all apes"""
    start_date, end_date, date_range, custom_date, custom_start_date, custom_end_date = calculate_date_range()
    
    # Get all apes
    apes = Apes.query.all()
    
    # Get meals within date range
    meals_in_range = get_meals_in_range(start_date, end_date)
    
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
        
        # Calculate protein and fiber totals from database values
        ape_protein = 0.0
        ape_fiber = 0.0
        for meal in ape_meals:
            # Use database values, with defaults if None
            protein = meal.recipe.protein_g if meal.recipe.protein_g is not None else 2.0
            fiber = meal.recipe.fiber_g if meal.recipe.fiber_g is not None else 1.0
            ape_protein += protein
            ape_fiber += fiber
        
        ape_stats[ape.id] = {
            'name': ape.ape_name,
            'calories': ape_calories,
            'meal_count': ape_meal_count,
            'avg_calories': ape_avg_calories,
            'protein_g': round(ape_protein, 1),
            'fiber_g': round(ape_fiber, 1)
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
    """Download meal reports data in CSV format"""
    start_date, end_date, _, _, _, _ = calculate_date_range()
    meals_in_range = get_meals_in_range(start_date, end_date)
    
    # Get all apes
    apes = Apes.query.all()
    
    # Calculate statistics (reuse same logic as reports view)
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
        
        # Calculate protein and fiber totals from database values
        ape_protein = 0.0
        ape_fiber = 0.0
        for meal in ape_meals:
            # Use database values, with defaults if None
            protein = meal.recipe.protein_g if meal.recipe.protein_g is not None else 2.0
            fiber = meal.recipe.fiber_g if meal.recipe.fiber_g is not None else 1.0
            ape_protein += protein
            ape_fiber += fiber
        
        ape_stats[ape.id] = {
            'name': ape.ape_name,
            'calories': ape_calories,
            'meal_count': ape_meal_count,
            'avg_calories': ape_avg_calories,
            'protein_g': round(ape_protein, 1),
            'fiber_g': round(ape_fiber, 1)
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
            'percentage': round((stats['calories'] / total_calories * 100) if total_calories > 0 else 0, 1)
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
        for date, stats in sorted(daily_stats.items())
    ]
    
    # Generate filename with date range
    filename_date_range = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
    
    if format.lower() == 'csv':
        return generate_csv_report(filename_date_range, apes, ape_stats, category_data, daily_data, 
                                 total_calories, total_meals, avg_calories_per_meal, start_date, end_date)
    else:
        flash('Invalid download format. Please choose CSV.', 'error')
        return redirect(url_for('site.reports'))




@site.route('/reports/download/raw', methods=['GET'])
@login_required
def download_raw_data():
    """Download raw database data as SQL dump file using SQLite's .dump functionality"""
    try:
        # Get database path from Flask app config
        # Note: SQLite URI format is sqlite:///path/to/db.db
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        # Remove sqlite:/// prefix to get actual file path
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
        elif db_uri.startswith('sqlite://'):
            db_path = db_uri.replace('sqlite://', '')
        else:
            db_path = db_uri
        
        # Ensure the path exists
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database file not found at: {db_path}")
        
        # Get date range parameters (optional - note: SQL dump includes all data)
        date_range = request.args.get('range', 'all')
        
        # For filtered exports, we'd need to create a filtered database copy
        # For now, we'll export the full database
        # TODO: If date filtering is needed, create a temporary filtered database
        
        # Create SQL dump
        sql_dump = io.StringIO()
        
        # Connect to database and dump
        conn = sqlite3.connect(db_path)
        for line in conn.iterdump():
            sql_dump.write(f'{line}\n')
        conn.close()
        
        # Get SQL content
        sql_content = sql_dump.getvalue()
        sql_dump.close()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"bonobo_feeding_log_database_{timestamp}.sql"
        
        # Create response with SQL content
        mem = io.BytesIO()
        mem.write(sql_content.encode('utf-8'))
        mem.seek(0)
        
        response = send_file(
            mem,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain; charset=utf-8'
        )
        
        # Add headers to ensure download works in all browsers and pywebview
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        return response
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in download_raw_data: {str(e)}", file=__import__('sys').stderr)
        print(f"Traceback: {error_details}", file=__import__('sys').stderr)
        flash(f'Error generating raw data download: {str(e)}', 'error')
        return redirect(url_for('site.reports'))


@site.route('/reports/download/excel', methods=['GET'])
@login_required
def download_excel_reports():
    """Download Excel reports (Individual Summary and Group Breakdown)"""
    try:
        start_date, end_date, _, _, _, _ = calculate_date_range()
        
        # Create temporary directory for Excel files
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Generate Excel reports
            individual_file = os.path.join(temp_dir, 'Bonobo_Individual_Diet_Summary.xlsx')
            group_file = os.path.join(temp_dir, 'Bonobo_Group_And_Category_Breakdown.xlsx')
            
            generate_individual_summary(individual_file, start_date, end_date)
            generate_group_and_category_breakdown(group_file, start_date, end_date)
            
            # Create zip file with both Excel files
            import zipfile
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                if os.path.exists(individual_file):
                    zip_file.write(individual_file, 'Bonobo_Individual_Diet_Summary.xlsx')
                if os.path.exists(group_file):
                    zip_file.write(group_file, 'Bonobo_Group_And_Category_Breakdown.xlsx')
            
            # Prepare zip file for download
            zip_buffer.seek(0)
            
            # Generate filename with timestamp and date range
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if start_date == end_date:
                date_suffix = f"_{start_date.strftime('%Y%m%d')}"
            else:
                date_suffix = f"_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"
            filename = f"bonobo_diet_reports{date_suffix}_{timestamp}.zip"
            
            response = send_file(
                zip_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/zip'
            )
            
            # Add headers
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'
            response.headers['Content-Type'] = 'application/zip'
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            return response
            
        finally:
            # Cleanup temporary directory
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(f"Warning: Failed to cleanup temp directory {temp_dir}: {cleanup_error}", file=__import__('sys').stderr)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in download_excel_reports: {str(e)}", file=__import__('sys').stderr)
        print(f"Traceback: {error_details}", file=__import__('sys').stderr)
        flash(f'Error generating Excel reports: {str(e)}', 'error')
        return redirect(url_for('site.reports'))

