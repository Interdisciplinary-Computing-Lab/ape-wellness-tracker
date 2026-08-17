"""Canonical feeding purposes and compatibility mappings for historical meals."""

FEEDING_PURPOSES = ('Forage', 'Enrichment', 'Reward', 'Other')
FEEDING_PURPOSE_LABELS = tuple((purpose, purpose) for purpose in FEEDING_PURPOSES)
DEFAULT_FEEDING_PURPOSE = 'Forage'

PURPOSE_BY_PERIOD = {
    'morning': 'Forage',
    'afternoon': 'Enrichment',
    'evening': 'Reward',
}

LEGACY_PURPOSE_MAP = {
    'Breakfast': 'Forage',
    'Lunch': 'Enrichment',
    'Dinner': 'Reward',
}


def normalize_feeding_purpose(value, default=DEFAULT_FEEDING_PURPOSE):
    """Return a current purpose, translating historical meal-type labels."""
    value = (value or '').strip()
    value = LEGACY_PURPOSE_MAP.get(value, value)
    return value if value in FEEDING_PURPOSES else default
