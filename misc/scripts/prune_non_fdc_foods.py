#!/usr/bin/env python3
"""
Keep USDA FDC catalog foods plus any names listed in data/fdc/custom_foods.json.
Link those two to Foundation Foods nutrition, then remove all other non-FDC recipes
and their meal log rows.

Usage (from project root):
  python misc/scripts/prune_non_fdc_foods.py --dry-run
  python misc/scripts/prune_non_fdc_foods.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend import create_app
from backend.extensions import db
from backend.models.entry import FoodCategory, Meals, Recipe
from backend.utils.fdc_loader import (
    FdcFoundationLoader,
    _normalize_desc,
    load_category_map,
)

CUSTOM_FOODS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "fdc",
    "custom_foods.json",
)


def load_custom_foods() -> dict:
    with open(CUSTOM_FOODS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["custom_display_names"]


def _find_fdc_record(loader: FdcFoundationLoader, fdc_description: str):
    target = _normalize_desc(fdc_description)
    for record in loader.iter_records(load_category_map(), include_excluded_categories=True):
        if _normalize_desc(record.description) == target:
            return record
    return None


def _apply_record_to_recipe(recipe: Recipe, record, food_category: str, description: str) -> None:
    categories = {c.name: c for c in FoodCategory.query.filter_by(is_active=True).all()}
    recipe.calories = record.calories
    recipe.protein_g = record.protein_g
    recipe.fiber_g = record.fiber_g
    recipe.quantity = record.quantity
    recipe.unit_of_measurement = record.unit_of_measurement
    recipe.source = record.source
    recipe.fdc_id = record.fdc_id
    recipe.description = description
    recipe.food_category = food_category
    cat = categories.get(food_category)
    recipe.category_id = cat.id if cat else None


def link_custom_foods(loader: FdcFoundationLoader, dry_run: bool, *, verbose: bool = True) -> list[int]:
    """Assign FDC nutrition to custom display names; return recipe ids to remove (duplicates)."""
    custom = load_custom_foods()
    duplicate_ids: list[int] = []

    for meal_name, meta in custom.items():
        record = _find_fdc_record(loader, meta["fdc_description"])
        if not record:
            if verbose:
                print(f"  [ERROR] No FDC match for {meal_name} -> {meta['fdc_description']}")
            continue

        for dup in Recipe.query.filter(
            Recipe.fdc_id == record.fdc_id,
            Recipe.meal_name != meal_name,
        ).all():
            dup.fdc_id = None

        recipe = Recipe.query.filter_by(meal_name=meal_name).first()
        if not recipe:
            if verbose:
                print(f"  {'[dry-run] ' if dry_run else ''}create custom {meal_name} from FDC {record.fdc_id}")
            if not dry_run:
                categories = {c.name: c for c in FoodCategory.query.filter_by(is_active=True).all()}
                cat = categories.get(meta["food_category"])
                recipe = Recipe(
                    meal_name=meal_name,
                    description=meta.get("description", ""),
                    calories=record.calories,
                    quantity=record.quantity,
                    unit_of_measurement=record.unit_of_measurement,
                    food_category=meta["food_category"],
                    protein_g=record.protein_g,
                    fiber_g=record.fiber_g,
                    source=record.source,
                    fdc_id=record.fdc_id,
                    category_id=cat.id if cat else None,
                )
                db.session.add(recipe)
                db.session.flush()
        else:
            if verbose:
                print(
                    f"  {'[dry-run] ' if dry_run else ''}link {meal_name}: "
                    f"cal {recipe.calories} -> {record.calories} (FDC {record.fdc_id})"
                )
            if not dry_run:
                _apply_record_to_recipe(
                    recipe, record, meta["food_category"], meta.get("description", "")
                )

        for dup in Recipe.query.filter(
            Recipe.fdc_id == record.fdc_id,
            Recipe.meal_name != meal_name,
        ).all():
            if dup.id not in duplicate_ids:
                if verbose:
                    print(f"    remove duplicate catalog entry: {dup.meal_name}")
                duplicate_ids.append(dup.id)

    return duplicate_ids


def collect_recipes_to_remove(keep_names: set[str], extra_ids: list[int]) -> list[Recipe]:
    remove: list[Recipe] = []
    extra_set = set(extra_ids)
    for recipe in Recipe.query.all():
        if recipe.id in extra_set:
            remove.append(recipe)
            continue
        if recipe.meal_name in keep_names:
            continue
        if recipe.fdc_id:
            continue
        remove.append(recipe)
    return remove


def prune_non_fdc_recipes(*, dry_run: bool = False, verbose: bool = True) -> int:
    """Remove recipes without fdc_id except custom display names. Requires app context."""
    custom = load_custom_foods()
    keep_names = set(custom.keys())

    loader = FdcFoundationLoader()
    if verbose:
        print("Linking custom foods to USDA Foundation Foods...")
    duplicate_ids = link_custom_foods(loader, dry_run, verbose=verbose)

    to_remove = collect_recipes_to_remove(keep_names, duplicate_ids)
    meal_count = sum(
        Meals.query.filter_by(recipe_id=r.id).count() for r in to_remove
    )

    if verbose:
        print(f"\nWill remove {len(to_remove)} food(s) and {meal_count} meal log row(s).")
        for r in to_remove[:20]:
            print(f"  - {r.meal_name} (fdc_id={r.fdc_id})")
        if len(to_remove) > 20:
            print(f"  ... and {len(to_remove) - 20} more")

        remaining_fdc = Recipe.query.filter(Recipe.fdc_id.isnot(None)).count()
        remaining_custom = Recipe.query.filter(Recipe.meal_name.in_(keep_names)).count()
        print(
            f"\nAfter prune: ~{remaining_fdc} USDA foods + "
            f"{remaining_custom} custom display name(s)"
        )

    if dry_run:
        if verbose:
            print("\n(dry run — no changes written)")
        return len(to_remove)

    for recipe in to_remove:
        Meals.query.filter_by(recipe_id=recipe.id).delete(synchronize_session=False)
        db.session.delete(recipe)

    db.session.commit()
    if verbose:
        print("\nDone.")
    return len(to_remove)


def run_prune(dry_run: bool) -> int:
    app = create_app(sync_fdc_catalog=False)

    with app.app_context():
        prune_non_fdc_recipes(dry_run=dry_run, verbose=True)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Remove non-USDA foods except custom display names in custom_foods.json"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return run_prune(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
