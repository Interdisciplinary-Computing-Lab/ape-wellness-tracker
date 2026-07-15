"""Build raw CSV zip exports for reports."""

import csv
import io
import os
import shutil
import sys
import tempfile
import zipfile
from datetime import date, datetime

from backend.models.entry import Apes, FoodCategory, Meals, Recipe, User
from backend.utils.meal_queries import meals_for_current_user


def build_raw_data_zip(start_date, end_date, include_denormalized=False):
    """
    Write CSV files to a temp dir, zip them, return (BytesIO buffer, download filename).

    Raises ValueError if zip would be empty.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        apes_data = Apes.query.all()
        apes_csv_path = os.path.join(temp_dir, 'Ape_Information.csv')
        with open(apes_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            apes_writer = csv.writer(f)
            apes_writer.writerow(
                [
                    'id',
                    'ape_name',
                    'birthday',
                    'weight_kg',
                    'image_filename',
                    'image_mime_type',
                    'is_archived',
                    'archived_at',
                ]
            )
            for ape in apes_data:
                apes_writer.writerow(
                    [
                        ape.id,
                        ape.ape_name,
                        ape.birthday.strftime('%Y-%m-%d') if ape.birthday else '',
                        ape.weight,
                        ape.image_filename,
                        ape.image_mime_type,
                        ape.is_archived,
                        ape.archived_at.strftime('%Y-%m-%d %H:%M:%S') if ape.archived_at else '',
                    ]
                )

        meals_query = meals_for_current_user()
        if start_date and end_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            meals_query = meals_query.filter(
                Meals.date >= start_datetime,
                Meals.date <= end_datetime,
            )
        meals_data = meals_query.all()
        meals_csv_path = os.path.join(temp_dir, 'Meal_Logs.csv')
        with open(meals_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            meals_writer = csv.writer(f)
            meals_writer.writerow(
                ['id', 'ape_id', 'recipe_id', 'date', 'feeding_period', 'user_id']
            )
            for meal in meals_data:
                meals_writer.writerow(
                    [
                        meal.id,
                        meal.ape_id,
                        meal.recipe_id,
                        meal.date.strftime('%Y-%m-%d %H:%M:%S') if meal.date else '',
                        meal.feeding_period if meal.feeding_period else '',
                        meal.user_id,
                    ]
                )

        recipes_data = Recipe.query.all()
        recipes_csv_path = os.path.join(temp_dir, 'Meal_Definitions.csv')
        with open(recipes_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            recipes_writer = csv.writer(f)
            recipes_writer.writerow(
                [
                    'id',
                    'meal_name',
                    'description',
                    'calories',
                    'quantity',
                    'unit_of_measurement',
                    'source',
                    'food_category',
                    'category_id',
                    'protein_g',
                    'fiber_g',
                ]
            )
            for recipe in recipes_data:
                recipes_writer.writerow(
                    [
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
                        recipe.fiber_g if recipe.fiber_g is not None else '',
                    ]
                )

        categories_data = FoodCategory.query.all()
        categories_csv_path = os.path.join(temp_dir, 'Food_Categories.csv')
        with open(categories_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            categories_writer = csv.writer(f)
            categories_writer.writerow(
                [
                    'id',
                    'name',
                    'description',
                    'icon',
                    'color',
                    'is_active',
                    'sort_order',
                    'created_at',
                    'updated_at',
                ]
            )
            for category in categories_data:
                categories_writer.writerow(
                    [
                        category.id,
                        category.name,
                        category.description,
                        category.icon,
                        category.color,
                        category.is_active,
                        category.sort_order,
                        category.created_at.strftime('%Y-%m-%d %H:%M:%S')
                        if category.created_at
                        else '',
                        category.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                        if category.updated_at
                        else '',
                    ]
                )

        if include_denormalized:
            denormalized_csv_path = os.path.join(temp_dir, 'Meal_Data_Denormalized.csv')
            with open(denormalized_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                denormalized_writer = csv.writer(f)
                denormalized_writer.writerow(
                    [
                        'meal_id',
                        'meal_date',
                        'feeding_period',
                        'ape_id',
                        'ape_name',
                        'ape_birthday',
                        'ape_age_at_meal',
                        'ape_weight_kg',
                        'recipe_id',
                        'meal_name',
                        'meal_description',
                        'calories',
                        'quantity',
                        'unit_of_measurement',
                        'source',
                        'food_category',
                        'category_name',
                        'user_id',
                        'logged_by_email',
                    ]
                )

                apes_dict = {ape.id: ape for ape in apes_data}
                recipes_dict = {recipe.id: recipe for recipe in recipes_data}
                categories_dict = {cat.id: cat for cat in categories_data}
                users_dict = {user.id: user for user in User.query.all()}

                for meal in meals_data:
                    ape = apes_dict.get(meal.ape_id)
                    recipe = recipes_dict.get(meal.recipe_id)
                    category = (
                        categories_dict.get(recipe.category_id)
                        if recipe and recipe.category_id
                        else None
                    )
                    user = users_dict.get(meal.user_id)

                    age_at_meal = None
                    if ape and ape.birthday and meal.date:
                        meal_date = (
                            meal.date.date() if isinstance(meal.date, datetime) else meal.date
                        )
                        age_at_meal = meal_date.year - ape.birthday.year
                        if meal_date < date(meal_date.year, ape.birthday.month, ape.birthday.day):
                            age_at_meal -= 1

                    denormalized_writer.writerow(
                        [
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
                            user.email if user else '',
                        ]
                    )

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            csv_files = [
                'Ape_Information.csv',
                'Meal_Logs.csv',
                'Meal_Definitions.csv',
                'Food_Categories.csv',
            ]
            if include_denormalized:
                csv_files.append('Meal_Data_Denormalized.csv')

            files_added = 0
            for csv_file in csv_files:
                csv_path = os.path.join(temp_dir, csv_file)
                if os.path.exists(csv_path):
                    zip_file.write(csv_path, csv_file)
                    files_added += 1

            if files_added == 0:
                raise ValueError('No files were generated for download')

        zip_buffer.seek(0)
        if zip_buffer.getvalue() == b'':
            raise ValueError('Generated zip file is empty')

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        date_suffix = ''
        if start_date and end_date:
            if start_date == end_date:
                date_suffix = f"_{start_date.strftime('%Y%m%d')}"
            else:
                date_suffix = (
                    f"_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"
                )
        filename = f'bonobo_feeding_log_raw_data{date_suffix}_{timestamp}.zip'
        return zip_buffer, filename
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception as cleanup_error:
            print(
                f'Warning: Failed to cleanup temp directory {temp_dir}: {cleanup_error}',
                file=sys.stderr,
            )
