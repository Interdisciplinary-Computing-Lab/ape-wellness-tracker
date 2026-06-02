"""
Meal log queries scoped to the signed-in user.

Apes, recipes, and categories are shared across staff; only meal entries are per-user.
"""

from flask_security import current_user
from backend.models.entry import Meals


def meals_for_current_user():
    """Base query for meal logs owned by the signed-in user."""
    if not current_user.is_authenticated:
        return Meals.query.filter(False)
    return Meals.query.filter(Meals.user_id == current_user.id)


def get_user_meal_or_404(meal_id):
    """Load a meal log only if it belongs to the current user."""
    return meals_for_current_user().filter_by(id=meal_id).first_or_404()
