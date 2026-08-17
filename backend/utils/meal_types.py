"""Meal type values used for logging, dashboards, and reports."""

MEAL_TYPES = ('Forage', 'Enrichment', 'Reward', 'Other')
MEAL_TYPE_LABELS = tuple((meal_type, meal_type) for meal_type in MEAL_TYPES)
DEFAULT_MEAL_TYPE = 'Forage'

MEAL_TYPE_BY_PERIOD = {
    'morning': 'Forage',
    'afternoon': 'Enrichment',
    'evening': 'Reward',
}

# Retired labels are rewritten in the database at startup; this mapping also
# covers requests already in flight during a deploy.
RETIRED_MEAL_TYPES = {
    'Breakfast': 'Forage',
    'Lunch': 'Enrichment',
    'Dinner': 'Reward',
}


def normalize_meal_type(value, default=DEFAULT_MEAL_TYPE):
    """Return a current meal type, translating retired labels."""
    value = (value or '').strip()
    value = RETIRED_MEAL_TYPES.get(value, value)
    return value if value in MEAL_TYPES else default
