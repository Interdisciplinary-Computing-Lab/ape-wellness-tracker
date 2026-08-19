from backend.utils.meal_types import normalize_meal_type


def test_normalize_current_meal_type():
    assert normalize_meal_type("Forage") == "Forage"
    assert normalize_meal_type("Reward") == "Reward"


def test_normalize_retired_labels():
    assert normalize_meal_type("Breakfast") == "Forage"
    assert normalize_meal_type("Lunch") == "Enrichment"
    assert normalize_meal_type("Dinner") == "Reward"


def test_normalize_unknown_falls_back():
    assert normalize_meal_type("Snack") == "Forage"
    assert normalize_meal_type("") == "Forage"
