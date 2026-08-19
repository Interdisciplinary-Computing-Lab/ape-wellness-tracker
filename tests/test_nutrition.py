from backend.utils.meal_nutrition import meal_calories, meal_fiber_g, meal_protein_g, meal_serving_scale


class Recipe:
    def __init__(self, calories=100, protein_g=10, fiber_g=4):
        self.calories = calories
        self.protein_g = protein_g
        self.fiber_g = fiber_g


class Meal:
    def __init__(self, calories_logged=None, recipe=None):
        self.calories_logged = calories_logged
        self.recipe = recipe


def test_meal_calories_prefers_logged_value():
    meal = Meal(calories_logged=40, recipe=Recipe(calories=100))
    assert meal_calories(meal) == 40


def test_meal_calories_falls_back_to_recipe():
    meal = Meal(calories_logged=None, recipe=Recipe(calories=85))
    assert meal_calories(meal) == 85


def test_serving_scale_and_macros():
    meal = Meal(calories_logged=50, recipe=Recipe(calories=100, protein_g=10, fiber_g=4))
    assert meal_serving_scale(meal) == 0.5
    assert meal_protein_g(meal) == 5.0
    assert meal_fiber_g(meal) == 2.0
