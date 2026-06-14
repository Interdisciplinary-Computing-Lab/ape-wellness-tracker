#!/usr/bin/env python3
"""
Import USDA Foundation Foods CSV data into Recipe rows.

Reads data/fdc/raw/ and data/fdc/category_map.json.

Usage (from project root):
  python misc/scripts/import_fdc_foundation.py --dry-run
  python misc/scripts/import_fdc_foundation.py
  python misc/scripts/import_fdc_foundation.py --import-all
  python misc/scripts/import_fdc_foundation.py --import-all --include-excluded
"""

from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend import create_app
from backend.extensions import db
from backend.models.entry import FoodCategory, Recipe
from backend.utils.fdc_loader import (
    FdcFoundationLoader,
    _normalize_desc,
    load_category_map,
)

# Legacy catalog meal_name -> exact FDC description (update-existing mode only)
MEAL_TO_FDC_DESCRIPTION = {
    "Banana": "Bananas, ripe and slightly ripe, raw",
    "Apple": "Apples, gala, with skin, raw",
    "Grapes": "Grapes, red, seedless, raw",
    "Blueberries": "Blueberries, raw",
    "Strawberries": "Strawberries, raw",
    "Watermelon": "Watermelon, seedless, flesh only, raw",
    "Cantaloupe": "Melons, cantaloupe, raw",
    "Orange": "Oranges, raw, navels",
    "Peach": "Peaches, yellow, raw",
    "Plum": "Plum, black, with skin, raw",
    "Pear": "Pears, raw, bartlett",
    "Carrot": "Carrots, mature, raw",
    "Sweet Potato": "Sweet potatoes, orange flesh, without skin, raw",
    "Cucumber": "Cucumber, with peel, raw",
    "Bell Pepper": "Peppers, bell, red, raw",
    "Kale": "Kale, raw",
    "Romaine Lettuce": "Lettuce, cos or romaine, raw",
    "Collard Greens": "Collards, raw",
    "Spinach": "Spinach, mature",
    "Broccoli": "Broccoli, raw",
    "Cauliflower": "Cauliflower, raw",
    "Green Beans": "Beans, snap, green, canned, regular pack, drained solids",
    "Zucchini": "Squash, summer, green, zucchini, includes skin, raw",
    "Tomato": "Tomato, roma",
    "Cabbage": "Cabbage, green, raw",
    "Corn": "Corn, sweet, yellow and white kernels, \xa0fresh, raw",
    "Brown Rice": "Rice, brown, long grain, unenriched, raw",
    "Cooked Rice": "Rice, white, long grain, unenriched, raw",
    "Oatmeal": "Oats, whole grain, rolled, old fashioned",
    "Quinoa": "Flour, quinoa",
    "Regular Potato": "Potatoes, russet, without skin, raw",
    "Lentils": "Lentils, dry",
    "Boiled Egg": "Eggs, Grade A, Large, egg whole",
    "Chickpeas": "Chickpeas (garbanzo beans, bengal gram), canned, sodium added, drained and rinsed",
    "Black Beans": "Beans, Dry, Black (0% moisture)",
    "Almonds": "Nuts, almonds, dry roasted, with salt added",
    "Peanuts": "Peanuts, raw",
    "Sunflower Seeds": "Seeds, sunflower seed, kernel, raw",
    "Walnuts": "Nuts, walnuts, English, halves, raw",
    "Pumpkin Seeds": "Seeds, pumpkin seeds (pepitas), raw",
    "Cashews": "Nuts, cashew nuts, raw",
    "Yogurt": "Yogurt, plain, whole milk",
    "Cottage Cheese": "Cottage cheese, full fat, large or small curd",
    "Almond Milk": "Almond milk, unsweetened, plain, shelf stable",
    "Soy Milk": "Soy milk, unsweetened, plain, shelf stable",
    "Cheese Toothpaste": "Cream cheese, full fat, block",
    "Dried Figs": "Figs, dried, uncooked",
    "Dried Mango": "Mango, Tommy Atkins, peeled, raw",
    "Dried Pineapple": "Pineapple, raw",
    "Dried Apricots": "Apricot, with skin, raw",
}


def _category_lookup() -> dict[str, FoodCategory]:
    return {c.name: c for c in FoodCategory.query.filter_by(is_active=True).all()}


def _apply_fdc_to_recipe(recipe: Recipe, record, categories: dict[str, FoodCategory]) -> None:
    recipe.calories = record.calories
    recipe.protein_g = record.protein_g
    recipe.fiber_g = record.fiber_g
    recipe.quantity = record.quantity
    recipe.unit_of_measurement = record.unit_of_measurement
    recipe.gram_weight = record.gram_weight
    recipe.source = record.source
    recipe.fdc_id = record.fdc_id
    recipe.description = record.description
    recipe.food_category = record.app_category
    cat = categories.get(record.app_category)
    if cat:
        recipe.category_id = cat.id


def _match_fdc_for_recipe(meal_name: str, by_desc: dict[str, dict]) -> dict | None:
    override = MEAL_TO_FDC_DESCRIPTION.get(meal_name)
    if override:
        hit = by_desc.get(_normalize_desc(override))
        if hit:
            return hit

    meal = meal_name.lower().strip()
    best_score = 0
    best = None
    for entry in by_desc.values():
        desc = entry["description"].lower()
        score = 0
        if desc == meal:
            score = 900
        elif desc == f"{meal}, raw":
            score = 850
        elif desc.startswith(meal + ",") or desc.startswith(meal + "s,"):
            score = 800
        elif re.search(rf"\b{re.escape(meal)}s?\b", desc):
            score = 500 - len(desc) // 10
        if score > best_score:
            best_score = score
            best = entry
    if best_score >= 800:
        return best
    return None


def _update_existing(
    loader: FdcFoundationLoader,
    category_map: dict,
    dry_run: bool,
) -> tuple[int, int, int]:
    """Update recipes already in the DB by name match to FDC."""
    foundation_ids = loader.foundation_ids()
    nutrients = loader.load_nutrients(foundation_ids)
    foods = loader.load_foods_by_fdc_id(nutrients)
    portions = loader.load_portions(foundation_ids)
    by_desc = {_normalize_desc(v["description"]): v for v in foods.values()}

    from backend.utils.fdc_loader import scaled_nutrition

    updated = skipped = missing_nutrient = 0
    categories = _category_lookup()

    for recipe in Recipe.query.order_by(Recipe.meal_name).all():
        if recipe.fdc_id and recipe.fdc_id in foods:
            food = foods[recipe.fdc_id]
        else:
            food = _match_fdc_for_recipe(recipe.meal_name, by_desc)
        if not food:
            print(f"  skip (no FDC match): {recipe.meal_name}")
            skipped += 1
            continue

        fdc_id = food["fdc_id"]
        holder = Recipe.query.filter_by(fdc_id=fdc_id).first()
        if holder and holder.id != recipe.id:
            print(
                f"  skip (FDC {fdc_id} already on '{holder.meal_name}'): {recipe.meal_name}"
            )
            skipped += 1
            continue

        nut = nutrients.get(fdc_id)
        if not nut or "energy" not in nut:
            print(f"  skip (no nutrients): {recipe.meal_name} -> {food['description']}")
            missing_nutrient += 1
            continue

        portion = portions.get(fdc_id)
        if portion:
            gram_weight = portion["gram_weight"]
            scaled = scaled_nutrition(nut, gram_weight)
            quantity = portion["quantity"]
            unit = portion["unit_of_measurement"]
        else:
            gram_weight = 100.0
            scaled = scaled_nutrition(nut, gram_weight)
            quantity = 100.0
            unit = "100 g"

        app_cat = recipe.food_category
        from backend.utils.fdc_loader import resolve_app_category

        mapped = resolve_app_category(food["food_category_id"], food["description"], category_map)
        if mapped:
            app_cat = mapped

        print(
            f"  {'[dry-run] ' if dry_run else ''}update {recipe.meal_name}: "
            f"cal {recipe.calories} -> {scaled['calories']}, "
            f"category -> {app_cat}, FDC {fdc_id}"
        )

        if not dry_run:
            recipe.calories = scaled["calories"]
            recipe.protein_g = scaled["protein_g"]
            recipe.fiber_g = scaled["fiber_g"]
            recipe.quantity = quantity
            recipe.unit_of_measurement = unit
            recipe.gram_weight = gram_weight
            recipe.source = f"USDA Foundation Foods (FDC {fdc_id})"
            recipe.fdc_id = fdc_id
            recipe.description = food["description"]
            recipe.food_category = app_cat
            cat = categories.get(app_cat)
            if cat:
                recipe.category_id = cat.id
            updated += 1
        else:
            updated += 1

    return updated, skipped, missing_nutrient


def import_all_fdc_foods(
    loader: FdcFoundationLoader,
    category_map: dict,
    dry_run: bool,
    include_excluded: bool,
    *,
    verbose: bool = True,
) -> tuple[int, int, int]:
    """Upsert all foundation foods into Recipe by fdc_id."""
    created = updated = skipped = 0
    categories = _category_lookup()
    used_meal_names: set[str] = {r.meal_name for r in Recipe.query.all()}

    for record in loader.iter_records(
        category_map,
        include_excluded_categories=include_excluded,
    ):
        recipe = Recipe.query.filter_by(fdc_id=record.fdc_id).first()
        if not recipe:
            recipe = Recipe.query.filter(
                db.func.lower(Recipe.meal_name) == record.meal_name.lower()
            ).first()

        meal_name = record.meal_name
        if not recipe:
            base_name = meal_name
            n = 2
            while meal_name in used_meal_names:
                suffix = f" ({record.fdc_id})"
                trim = 120 - len(suffix)
                meal_name = base_name[:trim].rstrip(" ,") + suffix if len(base_name) > trim else base_name + f" #{n}"
                n += 1

        action = "create" if not recipe else "update"
        if verbose:
            print(
                f"  {'[dry-run] ' if dry_run else ''}{action} [{record.app_category}] "
                f"{meal_name}: {record.calories} cal / {record.quantity} {record.unit_of_measurement}"
            )

        if dry_run:
            if recipe:
                updated += 1
            else:
                created += 1
            used_meal_names.add(meal_name)
            continue

        if not recipe:
            recipe = Recipe(
                meal_name=meal_name,
                description=record.description,
                calories=record.calories,
                quantity=record.quantity,
                unit_of_measurement=record.unit_of_measurement,
                food_category=record.app_category,
                protein_g=record.protein_g,
                fiber_g=record.fiber_g,
                gram_weight=record.gram_weight,
                source=record.source,
                fdc_id=record.fdc_id,
            )
            cat = categories.get(record.app_category)
            if cat:
                recipe.category_id = cat.id
            db.session.add(recipe)
            created += 1
        else:
            if recipe.meal_name != meal_name and meal_name not in used_meal_names:
                recipe.meal_name = meal_name
            _apply_fdc_to_recipe(recipe, record, categories)
            updated += 1

        used_meal_names.add(recipe.meal_name)

    return created, updated, skipped


def run_import(
    dry_run: bool,
    import_all: bool,
    include_excluded: bool,
) -> int:
    loader = FdcFoundationLoader()
    category_map = load_category_map()
    print(f"Loaded {len(loader.foundation_ids())} foundation foods from {loader.raw_dir}")

    app = create_app(sync_fdc_catalog=False)
    with app.app_context():
        if import_all:
            print("Mode: import all foundation foods into catalog")
            created, updated, skipped = import_all_fdc_foods(
                loader, category_map, dry_run, include_excluded, verbose=True
            )
            if not dry_run:
                db.session.commit()
            print(f"\nDone. created={created}, updated={updated}, skipped={skipped}")
        else:
            print("Mode: update existing catalog items only")
            updated, skipped, missing = _update_existing(loader, category_map, dry_run)
            if not dry_run and updated:
                db.session.commit()
            print(
                f"\nDone. updated={updated}, skipped={skipped}, "
                f"missing_nutrients={missing}"
                + (" (dry run)" if dry_run else "")
            )
    return 0


def main():
    parser = argparse.ArgumentParser(description="Import USDA Foundation Foods into Recipe rows")
    parser.add_argument("--dry-run", action="store_true", help="Preview without DB writes")
    parser.add_argument(
        "--import-all",
        action="store_true",
        help="Import all foundation foods (not only existing catalog names)",
    )
    parser.add_argument(
        "--include-excluded",
        action="store_true",
        help="Include restaurant/branded/etc. FDC categories normally skipped",
    )
    args = parser.parse_args()
    return run_import(
        dry_run=args.dry_run,
        import_all=args.import_all,
        include_excluded=args.include_excluded,
    )


if __name__ == "__main__":
    raise SystemExit(main())
