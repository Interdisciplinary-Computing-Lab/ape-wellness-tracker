"""
Report generation utilities for the Ape Wellness Tracker application.
"""

import io
import csv
from datetime import datetime
from flask import send_file


def generate_csv_report(filename_date_range, apes, ape_stats, category_data, daily_data, 
                       total_calories, total_meals, avg_calories_per_meal, start_date, end_date):
    """Generate CSV report"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Report header
    writer.writerow(['Ape Meal Tracker - Meal Report'])
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
    writer.writerow(['Ape Name', 'Total Calories', 'Total Meals', 'Avg Calories/Meal', 'Total Protein (g)', 'Total Fiber (g)'])
    for ape in apes:
        stats = ape_stats[ape.id]
        writer.writerow([
            stats['name'],
            stats['calories'],
            stats['meal_count'],
            f"{stats['avg_calories']:.1f}",
            stats.get('protein_g', 0.0),
            stats.get('fiber_g', 0.0)
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
    
    # Prepare response with UTF-8 BOM for Excel compatibility
    output.seek(0)
    mem = io.BytesIO()
    # Add UTF-8 BOM so Excel recognizes the encoding properly
    mem.write('\ufeff'.encode('utf-8'))
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    filename = f"nutrition_report_{filename_date_range}.csv"
    response = send_file(
        mem,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv; charset=utf-8'
    )
    # Add headers to ensure download works in browsers
    # Use filename* for UTF-8 encoding support
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

