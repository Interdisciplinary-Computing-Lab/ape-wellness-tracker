"""
Reports and data export routes for the Ape Wellness Tracker application.
"""

from flask import render_template, request, redirect, url_for, flash, send_file, current_app
from backend.extensions import db
from backend.models.entry import Apes, Recipe, Meals, FoodCategory, User
from backend.utils.report_utils import generate_csv_report
from backend.utils.report_generators import generate_individual_summary, generate_group_and_category_breakdown
from flask_security import login_required
from datetime import datetime, timedelta, date
from collections import defaultdict
from backend.utils.meal_nutrition import meal_calories, meal_protein_g, meal_fiber_g
from backend.routes import site
import pandas as pd
import sqlite3
import io
import tempfile
import os
import csv
import zipfile
import shutil
import sys


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
    total_calories = sum(meal_calories(meal) for meal in meals_in_range)
    total_meals = len(meals_in_range)
    avg_calories_per_meal = total_calories / total_meals if total_meals > 0 else 0
    
    # Calculate per-ape statistics
    ape_stats = {}
    for ape in apes:
        ape_meals = [meal for meal in meals_in_range if meal.ape_id == ape.id]
        ape_calories = sum(meal_calories(meal) for meal in ape_meals)
        ape_meal_count = len(ape_meals)
        ape_avg_calories = ape_calories / ape_meal_count if ape_meal_count > 0 else 0
        
        ape_protein = sum(meal_protein_g(meal) for meal in ape_meals)
        ape_fiber = sum(meal_fiber_g(meal) for meal in ape_meals)
        
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
        category_stats[category]['calories'] += meal_calories(meal)
    
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
        daily_stats[meal_date]['calories'] += meal_calories(meal)
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
    total_calories = sum(meal_calories(meal) for meal in meals_in_range)
    total_meals = len(meals_in_range)
    avg_calories_per_meal = total_calories / total_meals if total_meals > 0 else 0
    
    # Per-ape statistics
    ape_stats = {}
    for ape in apes:
        ape_meals = [meal for meal in meals_in_range if meal.ape_id == ape.id]
        ape_calories = sum(meal_calories(meal) for meal in ape_meals)
        ape_meal_count = len(ape_meals)
        ape_avg_calories = ape_calories / ape_meal_count if ape_meal_count > 0 else 0
        
        ape_protein = sum(meal_protein_g(meal) for meal in ape_meals)
        ape_fiber = sum(meal_fiber_g(meal) for meal in ape_meals)
        
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
        category_stats[category]['calories'] += meal_calories(meal)
    
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
        daily_stats[meal_date]['calories'] += meal_calories(meal)
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
    """Download raw database data as CSV files in a zip archive with optional date filtering"""
    try:
        # Get date range parameters
        date_range = request.args.get('range', 'all')
        custom_date = request.args.get('date', '')
        custom_start_date = request.args.get('start_date', '')
        custom_end_date = request.args.get('end_date', '')
        include_denormalized = request.args.get('denormalized', 'false').lower() == 'true'
        
        # Calculate date range for filtering meals
        start_date = None
        end_date = None
        
        if date_range == 'today':
            start_date = datetime.now().date()
            end_date = datetime.now().date()
        elif date_range == 'week':
            start_date = datetime.now().date() - timedelta(days=7)
            end_date = datetime.now().date()
        elif date_range == 'month':
            start_date = datetime.now().date() - timedelta(days=30)
            end_date = datetime.now().date()
        elif date_range == 'custom' and custom_date:
            try:
                start_date = datetime.strptime(custom_date, '%Y-%m-%d').date()
                end_date = start_date
            except ValueError:
                pass
        elif date_range == 'custom_range' and custom_start_date and custom_end_date:
            try:
                start_date = datetime.strptime(custom_start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(custom_end_date, '%Y-%m-%d').date()
                if start_date > end_date:
                    start_date, end_date = end_date, start_date
            except ValueError:
                pass
        
        # Create a temporary directory for CSV files
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Step 1: Generate CSV files in temporary directory
            # 1. Ape_Information.csv from Apes table
            apes_data = Apes.query.all()
            apes_csv_path = os.path.join(temp_dir, 'Ape_Information.csv')
            with open(apes_csv_path, 'w', newline='', encoding='utf-8-sig') as f:  # utf-8-sig adds BOM for Excel
                apes_writer = csv.writer(f)
                # Write header
                apes_writer.writerow(['id', 'ape_name', 'birthday', 'weight', 'image_filename', 'image_mime_type', 'is_archived', 'archived_at'])
                # Write data rows
                for ape in apes_data:
                    apes_writer.writerow([
                        ape.id,
                        ape.ape_name,
                        ape.birthday.strftime('%Y-%m-%d') if ape.birthday else '',
                        ape.weight,
                        ape.image_filename,
                        ape.image_mime_type,
                        ape.is_archived,
                        ape.archived_at.strftime('%Y-%m-%d %H:%M:%S') if ape.archived_at else ''
                    ])
            
            # 2. Meal_Logs.csv from Meals table (with optional date filtering)
            meals_query = Meals.query
            if start_date and end_date:
                # Convert date objects to datetime for proper comparison
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                meals_query = meals_query.filter(
                    Meals.date >= start_datetime,
                    Meals.date <= end_datetime
                )
            meals_data = meals_query.all()
            meals_csv_path = os.path.join(temp_dir, 'Meal_Logs.csv')
            with open(meals_csv_path, 'w', newline='', encoding='utf-8-sig') as f:  # utf-8-sig adds BOM for Excel
                meals_writer = csv.writer(f)
                # Write header
                meals_writer.writerow(['id', 'ape_id', 'recipe_id', 'date', 'feeding_period', 'user_id'])
                # Write data rows
                for meal in meals_data:
                    meals_writer.writerow([
                        meal.id,
                        meal.ape_id,
                        meal.recipe_id,
                        meal.date.strftime('%Y-%m-%d %H:%M:%S') if meal.date else '',
                        meal.feeding_period if meal.feeding_period else '',
                        meal.user_id
                    ])
            
            # 3. Meal_Definitions.csv from Recipe table
            recipes_data = Recipe.query.all()
            recipes_csv_path = os.path.join(temp_dir, 'Meal_Definitions.csv')
            with open(recipes_csv_path, 'w', newline='', encoding='utf-8-sig') as f:  # utf-8-sig adds BOM for Excel
                recipes_writer = csv.writer(f)
                # Write header
                recipes_writer.writerow(['id', 'meal_name', 'description', 'calories', 'quantity', 'unit_of_measurement', 'source', 'food_category', 'category_id', 'protein_g', 'fiber_g'])
                # Write data rows
                for recipe in recipes_data:
                    recipes_writer.writerow([
                        recipe.id,
                        recipe.meal_name,
                        recipe.description,
                        recipe.calories,
                        recipe.quantity,
                        recipe.unit_of_measurement,
                        recipe.source,
                        recipe.food_category,
                        recipe.category_id,
                        recipe.protein_g if recipe.protein_g is not None else '',
                        recipe.fiber_g if recipe.fiber_g is not None else ''
                    ])
            
            # 4. Food_Categories.csv from FoodCategory table
            categories_data = FoodCategory.query.all()
            categories_csv_path = os.path.join(temp_dir, 'Food_Categories.csv')
            with open(categories_csv_path, 'w', newline='', encoding='utf-8-sig') as f:  # utf-8-sig adds BOM for Excel
                categories_writer = csv.writer(f)
                # Write header
                categories_writer.writerow(['id', 'name', 'description', 'icon', 'color', 'is_active', 'sort_order', 'created_at', 'updated_at'])
                # Write data rows
                for category in categories_data:
                    categories_writer.writerow([
                        category.id,
                        category.name,
                        category.description,
                        category.icon,
                        category.color,
                        category.is_active,
                        category.sort_order,
                        category.created_at.strftime('%Y-%m-%d %H:%M:%S') if category.created_at else '',
                        category.updated_at.strftime('%Y-%m-%d %H:%M:%S') if category.updated_at else ''
                    ])
            
            # 5. Denormalized export (all meal data in one table) - optional
            if include_denormalized:
                denormalized_csv_path = os.path.join(temp_dir, 'Meal_Data_Denormalized.csv')
                with open(denormalized_csv_path, 'w', newline='', encoding='utf-8-sig') as f:  # utf-8-sig adds BOM for Excel
                    denormalized_writer = csv.writer(f)
                    # Write header with all relevant fields
                    denormalized_writer.writerow([
                        'meal_id', 'meal_date', 'feeding_period',
                        'ape_id', 'ape_name', 'ape_birthday', 'ape_age_at_meal', 'ape_weight',
                        'recipe_id', 'meal_name', 'meal_description', 'calories', 'quantity', 'unit_of_measurement', 'source', 'food_category', 'category_name',
                        'user_id', 'logged_by_email'
                    ])
                    
                    # Create lookup dictionaries for performance
                    apes_dict = {ape.id: ape for ape in apes_data}
                    recipes_dict = {recipe.id: recipe for recipe in recipes_data}
                    categories_dict = {cat.id: cat for cat in categories_data}
                    users_dict = {user.id: user for user in User.query.all()}
                    
                    # Write data rows
                    for meal in meals_data:
                        ape = apes_dict.get(meal.ape_id)
                        recipe = recipes_dict.get(meal.recipe_id)
                        category = categories_dict.get(recipe.category_id) if recipe and recipe.category_id else None
                        user = users_dict.get(meal.user_id)
                        
                        # Calculate age at meal time
                        age_at_meal = None
                        if ape and ape.birthday and meal.date:
                            meal_date = meal.date.date() if isinstance(meal.date, datetime) else meal.date
                            age_at_meal = meal_date.year - ape.birthday.year
                            if meal_date < date(meal_date.year, ape.birthday.month, ape.birthday.day):
                                age_at_meal -= 1
                        
                        denormalized_writer.writerow([
                            meal.id,
                            meal.date.strftime('%Y-%m-%d %H:%M:%S') if meal.date else '',
                            meal.feeding_period if meal.feeding_period else '',
                            meal.ape_id,
                            ape.ape_name if ape else '',
                            ape.birthday.strftime('%Y-%m-%d') if ape and ape.birthday else '',
                            age_at_meal if age_at_meal is not None else '',
                            ape.weight if ape else '',
                            meal.recipe_id,
                            recipe.meal_name if recipe else '',
                            recipe.description if recipe else '',
                            recipe.calories if recipe else '',
                            recipe.quantity if recipe else '',
                            recipe.unit_of_measurement if recipe else '',
                            recipe.source if recipe else '',
                            recipe.food_category if recipe else '',
                            category.name if category else '',
                            meal.user_id,
                            user.email if user else ''
                        ])
            
            # Step 2: Create zip file with all CSV files
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add all CSV files
                csv_files = ['Ape_Information.csv', 'Meal_Logs.csv', 'Meal_Definitions.csv', 'Food_Categories.csv']
                if include_denormalized:
                    csv_files.append('Meal_Data_Denormalized.csv')
                
                files_added = 0
                for csv_file in csv_files:
                    csv_path = os.path.join(temp_dir, csv_file)
                    if os.path.exists(csv_path):
                        zip_file.write(csv_path, csv_file)
                        files_added += 1
                
                # Ensure at least some files were added
                if files_added == 0:
                    raise ValueError("No files were generated for download")
            
            # Prepare the zip file for download
            zip_buffer.seek(0)
            
            # Verify zip file is not empty
            if zip_buffer.getvalue() == b'':
                raise ValueError("Generated zip file is empty")
            
            # Generate filename with timestamp and date range info
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            date_suffix = ''
            if start_date and end_date:
                if start_date == end_date:
                    date_suffix = f"_{start_date.strftime('%Y%m%d')}"
                else:
                    date_suffix = f"_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"
            filename = f"bonobo_feeding_log_raw_data{date_suffix}_{timestamp}.zip"
            
            response = send_file(
                zip_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/zip'
            )
            # Add headers to ensure download works in all browsers and pywebview
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'
            response.headers['Content-Type'] = 'application/zip'
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            return response
        
        finally:
            # Cleanup - remove temporary directory
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(f"Warning: Failed to cleanup temp directory {temp_dir}: {cleanup_error}", file=sys.stderr)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in download_raw_data: {str(e)}", file=sys.stderr)
        print(f"Traceback: {error_details}", file=sys.stderr)
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

