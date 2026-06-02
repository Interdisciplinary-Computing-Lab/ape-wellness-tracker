"""Date range helpers for reports and exports."""

from datetime import datetime, timedelta

from flask import request

from backend.models.entry import Meals
from backend.utils.meal_queries import meals_for_current_user


def calculate_date_range():
    """Calculate date range from reports page query parameters."""
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


def parse_export_date_range():
    """Parse optional date range from raw export query parameters."""
    date_range = request.args.get('range', 'all')
    custom_date = request.args.get('date', '')
    custom_start_date = request.args.get('start_date', '')
    custom_end_date = request.args.get('end_date', '')

    start_date = None
    end_date = None

    if date_range == 'today':
        start_date = end_date = datetime.now().date()
    elif date_range == 'week':
        start_date = datetime.now().date() - timedelta(days=7)
        end_date = datetime.now().date()
    elif date_range == 'month':
        start_date = datetime.now().date() - timedelta(days=30)
        end_date = datetime.now().date()
    elif date_range == 'custom' and custom_date:
        try:
            start_date = end_date = datetime.strptime(custom_date, '%Y-%m-%d').date()
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

    return start_date, end_date


def get_meals_in_range(start_date, end_date):
    """Get current user's meal logs within date range."""
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    return meals_for_current_user().filter(
        Meals.date >= start_datetime,
        Meals.date <= end_datetime,
    ).all()
