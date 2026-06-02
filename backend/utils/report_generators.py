"""
Excel report generation utilities for the Ape Wellness Tracker application.
These functions generate Excel reports using pandas and openpyxl.
"""

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font
from flask_security import current_user
from backend.models.entry import Apes, Recipe, Meals, FoodCategory, User
from sqlalchemy import func
from backend.extensions import db
from collections import defaultdict


def _scope_meals_query(query):
    if current_user.is_authenticated:
        return query.filter(Meals.user_id == current_user.id)
    return query.filter(False)


def format_excel_headers(file_path, sheet_name, header_row=1):
    """
    Format the header row in an Excel sheet to be bold.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet to format
        header_row: Row number for headers (default: 1)
    """
    workbook = load_workbook(file_path)
    worksheet = workbook[sheet_name]
    
    # Make header row bold
    bold_font = Font(bold=True)
    for cell in worksheet[header_row]:
        cell.font = bold_font
    
    workbook.save(file_path)
    workbook.close()


def generate_individual_summary(output_file, start_date=None, end_date=None):
    """
    Generate Bonobo_Individual_Diet_Summary.xlsx using pandas directly from database.
    
    Creates a report summarizing the total intake per ape, including macronutrients.
    
    Args:
        output_file: Path where the Excel file should be saved
        start_date: Optional start date for filtering meals
        end_date: Optional end date for filtering meals
    """
    from datetime import datetime
    
    effective_calories = func.coalesce(Meals.calories_logged, Recipe.calories)
    query = db.session.query(
        Meals.ape_id,
        Meals.recipe_id,
        Meals.date,
        Recipe.meal_name,
        effective_calories.label('calories'),
        Recipe.calories.label('recipe_calories'),
        Recipe.protein_g,
        Recipe.fiber_g,
        Apes.ape_name
    ).join(Recipe).join(Apes)
    query = _scope_meals_query(query)
    
    # Filter by date range if provided
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(Meals.date >= start_datetime)
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(Meals.date <= end_datetime)
    
    # Read into pandas DataFrame
    meals_df = pd.read_sql(query.statement, db.session.bind)
    
    if meals_df.empty:
        # Return empty report if no data
        summary_data = []
        all_apes = Apes.query.all()
        for ape in all_apes:
            summary_data.append({
                'Ape Name': ape.ape_name,
                'Total Calories Consumed': 0,
                'Total Meals Count': 0,
                'Average Calories per Meal': 0.0,
                'Total Protein (g)': 0.0,
                'Total Fiber (g)': 0.0
            })
        df = pd.DataFrame(summary_data)
    else:
        # Use protein and fiber from database (fill NaN with defaults)
        meals_df['protein_g'] = meals_df['protein_g'].fillna(2.0)
        meals_df['fiber_g'] = meals_df['fiber_g'].fillna(1.0)
        
        # Calculate per-ape statistics
        ape_stats = defaultdict(lambda: {'calories': 0, 'meals': 0, 'protein_g': 0, 'fiber_g': 0})
        
        for _, row in meals_df.iterrows():
            ape_name = row['ape_name'] if pd.notna(row['ape_name']) else 'Unknown'
            calories = row['calories'] if pd.notna(row['calories']) else 0
            recipe_calories = row['recipe_calories'] if pd.notna(row['recipe_calories']) else 0
            scale = (calories / recipe_calories) if recipe_calories else 1.0
            protein = (row['protein_g'] if pd.notna(row['protein_g']) else 2.0) * scale
            fiber = (row['fiber_g'] if pd.notna(row['fiber_g']) else 1.0) * scale

            ape_stats[ape_name]['calories'] += calories
            ape_stats[ape_name]['meals'] += 1
            ape_stats[ape_name]['protein_g'] += protein
            ape_stats[ape_name]['fiber_g'] += fiber
        
        # Get all apes (including those with no meals)
        all_apes = Apes.query.all()
        all_ape_names = [ape.ape_name for ape in all_apes]
        
        # Build the summary data
        summary_data = []
        for ape_name in sorted(all_ape_names):
            stats = ape_stats[ape_name]
            avg_calories = stats['calories'] / stats['meals'] if stats['meals'] > 0 else 0
            summary_data.append({
                'Ape Name': ape_name,
                'Total Calories Consumed': int(stats['calories']),
                'Total Meals Count': stats['meals'],
                'Average Calories per Meal': round(avg_calories, 1),
                'Total Protein (g)': round(stats['protein_g'], 1),
                'Total Fiber (g)': round(stats['fiber_g'], 1)
            })
        
        df = pd.DataFrame(summary_data)
    
    # Generate Excel file
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Individual Summary', index=False)
    
    # Format headers to be bold
    format_excel_headers(output_file, 'Individual Summary')
    
    return output_file


def generate_group_and_category_breakdown(output_file, start_date=None, end_date=None):
    """
    Generate Bonobo_Group_And_Category_Breakdown.xlsx using pandas directly from database.
    
    Creates a report detailing the group's daily activity and food category usage.
    
    Args:
        output_file: Path where the Excel file should be saved
        start_date: Optional start date for filtering meals
        end_date: Optional end date for filtering meals
    """
    from datetime import datetime
    
    effective_calories = func.coalesce(Meals.calories_logged, Recipe.calories)
    query = db.session.query(
        Meals.date,
        Meals.id,
        effective_calories.label('calories'),
        Recipe.food_category
    ).join(Recipe)
    query = _scope_meals_query(query)
    
    # Filter by date range if provided
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(Meals.date >= start_datetime)
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(Meals.date <= end_datetime)
    
    # Read into pandas DataFrame
    meals_df = pd.read_sql(query.statement, db.session.bind)
    
    if meals_df.empty:
        # Return empty reports if no data
        df_daily = pd.DataFrame(columns=['Date', 'Total Group Calories', 'Total Group Meals'])
        df_category = pd.DataFrame(columns=['Food Category', 'Category Total Meals', 'Category Total Calories', 'Percentage of Group Total (%)'])
    else:
        # Convert date column to datetime if it's a string
        if meals_df['date'].dtype == 'object':
            meals_df['date'] = pd.to_datetime(meals_df['date'], errors='coerce')
        
        # Extract date part (without time)
        meals_df['date_only'] = meals_df['date'].dt.date
        
        # Sheet 1: Daily Group Totals
        daily_stats = defaultdict(lambda: {'calories': 0, 'meals': 0})
        
        for _, row in meals_df.iterrows():
            if pd.notna(row['date_only']):
                date_str = str(row['date_only'])
                calories = row['calories'] if pd.notna(row['calories']) else 0
                daily_stats[date_str]['calories'] += calories
                daily_stats[date_str]['meals'] += 1
        
        # Convert to sorted list
        daily_data = [
            {
                'Date': date_str,
                'Total Group Calories': int(stats['calories']),
                'Total Group Meals': stats['meals']
            }
            for date_str, stats in sorted(daily_stats.items())
        ]
        df_daily = pd.DataFrame(daily_data)
        
        # Sheet 2: Food Category Breakdown
        category_stats = defaultdict(lambda: {'calories': 0, 'meals': 0})
        total_group_calories = 0
        
        for _, row in meals_df.iterrows():
            category = row['food_category'] if pd.notna(row['food_category']) else 'Other'
            calories = row['calories'] if pd.notna(row['calories']) else 0
            category_stats[category]['calories'] += calories
            category_stats[category]['meals'] += 1
            total_group_calories += calories
        
        # Convert to list with percentages
        category_data = []
        for category, stats in sorted(category_stats.items()):
            percentage = (stats['calories'] / total_group_calories * 100) if total_group_calories > 0 else 0
            category_data.append({
                'Food Category': category,
                'Category Total Meals': stats['meals'],
                'Category Total Calories': int(stats['calories']),
                'Percentage of Group Total (%)': round(percentage, 1)
            })
        
        df_category = pd.DataFrame(category_data)
    
    # Generate Excel file with multiple sheets
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_daily.to_excel(writer, sheet_name='Daily Group Totals', index=False)
        df_category.to_excel(writer, sheet_name='Food Category Breakdown', index=False)
    
    # Format headers to be bold for both sheets
    format_excel_headers(output_file, 'Daily Group Totals')
    format_excel_headers(output_file, 'Food Category Breakdown')
    
    return output_file

