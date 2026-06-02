"""Aggregate meal statistics for reports views and CSV export."""

from collections import defaultdict

from backend.utils.meal_nutrition import meal_calories, meal_fiber_g, meal_protein_g


def build_report_aggregates(meals_in_range, apes, *, for_download=False):
    """
    Build stats dicts used by reports.html and CSV download.

    Returns:
        total_calories, total_meals, avg_calories_per_meal,
        ape_stats, category_data, daily_data
    """
    total_calories = sum(meal_calories(meal) for meal in meals_in_range)
    total_meals = len(meals_in_range)
    avg_calories_per_meal = total_calories / total_meals if total_meals > 0 else 0

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
            'fiber_g': round(ape_fiber, 1),
        }

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
            'percentage': (stats['calories'] / total_calories * 100) if total_calories > 0 else 0,
        }
        for category, stats in category_stats.items()
    ]
    category_data.sort(key=lambda x: x['calories'], reverse=True)

    if for_download:
        for row in category_data:
            row['percentage'] = round(row['percentage'], 1)

    daily_stats = defaultdict(lambda: {'calories': 0, 'meals': 0})
    for meal in meals_in_range:
        meal_date = meal.date.date()
        daily_stats[meal_date]['calories'] += meal_calories(meal)
        daily_stats[meal_date]['meals'] += 1

    if for_download:
        daily_data = [
            {
                'date': d.strftime('%Y-%m-%d'),
                'calories': stats['calories'],
                'meals': stats['meals'],
            }
            for d, stats in sorted(daily_stats.items())
        ]
    else:
        daily_data = [
            {
                'date': d,
                'calories': stats['calories'],
                'meals': stats['meals'],
            }
            for d, stats in daily_stats.items()
        ]
        daily_data.sort(key=lambda x: x['date'])

    return (
        total_calories,
        total_meals,
        avg_calories_per_meal,
        ape_stats,
        category_data,
        daily_data,
    )
