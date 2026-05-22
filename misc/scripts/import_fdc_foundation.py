#!/usr/bin/env python3
"""
Import USDA Foundation Foods CSV data into Recipe rows.

Reads data/fdc/raw/ (foundation_food.csv, food.csv, food_nutrient.csv, food_portion.csv).
By default updates existing recipes only when a confident FDC match exists.

Usage (from project root):
  python misc/scripts/import_fdc_foundation.py --dry-run
  python misc/scripts/import_fdc_foundation.py
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from datetime import datetime

# Project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend import create_app
from backend.extensions import db
from backend.models.entry import Recipe

RAW_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "fdc",
    "raw",
)

# Energy: prefer classic kcal (1008), then Atwater-specific/general factors
NUTRIENT_ENERGY_IDS = ("1008", "2048", "2047")
NUTRIENT_PROTEIN = "1003"
NUTRIENT_FIBER = "1079"

# Catalog meal_name -> exact FDC description (foundation foods only)
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
    "Trash Lettuce": "Brussels sprouts, raw",
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


def _normalize_desc(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ").strip().lower())


def _load_measure_units() -> dict[str, str]:
    path = os.path.join(RAW_DIR, "measure_unit.csv")
    units = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            units[row["id"]] = row["name"]
    return units


def _load_foundation_foods(nutrients: dict[str, dict]) -> tuple[dict[str, dict], set[str]]:
    """Map normalized description -> best fdc row; return all foundation fdc ids."""
    ff_path = os.path.join(RAW_DIR, "foundation_food.csv")
    food_path = os.path.join(RAW_DIR, "food.csv")
    if not os.path.isfile(ff_path) or not os.path.isfile(food_path):
        raise FileNotFoundError(
            f"Missing Foundation Foods CSVs in {RAW_DIR}. "
            "Extract the December 2025 Foundation Foods zip there."
        )

    foundation_ids = set()
    with open(ff_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            foundation_ids.add(row["fdc_id"])

    candidates: dict[str, list[dict]] = {}
    with open(food_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["fdc_id"] not in foundation_ids:
                continue
            if row["data_type"] != "foundation_food":
                continue
            desc = row["description"]
            key = _normalize_desc(desc)
            candidates.setdefault(key, []).append(
                {
                    "fdc_id": row["fdc_id"],
                    "description": desc,
                    "publication_date": row.get("publication_date") or "",
                }
            )

    by_desc: dict[str, dict] = {}
    for key, rows in candidates.items():
        with_energy = [r for r in rows if "energy" in nutrients.get(r["fdc_id"], {})]
        pool = with_energy or rows
        by_desc[key] = max(pool, key=lambda r: r["publication_date"])

    return by_desc, foundation_ids


def _load_nutrients(foundation_ids: set[str]) -> dict[str, dict[str, float]]:
    path = os.path.join(RAW_DIR, "food_nutrient.csv")
    wanted = set(NUTRIENT_ENERGY_IDS) | {NUTRIENT_PROTEIN, NUTRIENT_FIBER}
    out: dict[str, dict[str, float]] = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fdc_id = row["fdc_id"]
            if fdc_id not in foundation_ids:
                continue
            nid = row["nutrient_id"]
            if nid not in wanted:
                continue
            try:
                amount = float(row["amount"])
            except (TypeError, ValueError):
                continue
            bucket = out.setdefault(fdc_id, {})
            if nid in NUTRIENT_ENERGY_IDS and "energy" not in bucket:
                # First seen wins per file order; re-sort below by priority
                bucket.setdefault("_energy_candidates", {})[nid] = amount
            elif nid == NUTRIENT_PROTEIN:
                bucket["protein"] = amount
            elif nid == NUTRIENT_FIBER:
                bucket["fiber"] = amount

    for bucket in out.values():
        candidates = bucket.pop("_energy_candidates", {})
        for nid in NUTRIENT_ENERGY_IDS:
            if nid in candidates:
                bucket["energy"] = candidates[nid]
                break
    return out


def _load_portions(foundation_ids: set[str], measure_units: dict[str, str]) -> dict[str, dict]:
    path = os.path.join(RAW_DIR, "food_portion.csv")
    best: dict[str, dict] = {}
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fdc_id = row["fdc_id"]
            if fdc_id not in foundation_ids:
                continue
            try:
                gram_weight = float(row["gram_weight"] or 0)
            except (TypeError, ValueError):
                gram_weight = 0.0
            if gram_weight <= 0:
                continue
            try:
                seq = int(row["seq_num"] or 9999)
            except (TypeError, ValueError):
                seq = 9999
            try:
                amount = float(row["amount"] or 1) or 1.0
            except (TypeError, ValueError):
                amount = 1.0

            prev = best.get(fdc_id)
            if prev and seq >= prev["seq_num"]:
                continue

            modifier = (row.get("modifier") or "").strip()
            portion_desc = (row.get("portion_description") or "").strip()
            unit_id = row.get("measure_unit_id", "")
            unit_name = measure_units.get(unit_id, portion_desc or "serving")

            label_parts = [p for p in [str(amount) if amount != 1 else "", unit_name, modifier] if p]
            unit_label = " ".join(label_parts).strip() or unit_name

            best[fdc_id] = {
                "seq_num": seq,
                "quantity": amount,
                "gram_weight": gram_weight,
                "unit_of_measurement": unit_label[:50],
            }
    return best


def _match_fdc(meal_name: str, by_desc: dict[str, dict]) -> dict | None:
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


def _scaled_nutrition(nutrients: dict, gram_weight: float) -> dict:
    factor = gram_weight / 100.0
    energy = nutrients.get("energy")
    if energy is None:
        raise ValueError("missing energy (nutrient 1008)")
    return {
        "calories": max(0, round(energy * factor)),
        "protein_g": round(nutrients.get("protein", 0) * factor, 2),
        "fiber_g": round(nutrients.get("fiber", 0) * factor, 2),
    }


def run_import(dry_run: bool) -> int:
    measure_units = _load_measure_units()
    ff_path = os.path.join(RAW_DIR, "foundation_food.csv")
    foundation_ids = set()
    with open(ff_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            foundation_ids.add(row["fdc_id"])
    print(f"Loaded {len(foundation_ids)} foundation foods from {RAW_DIR}")

    nutrients = _load_nutrients(foundation_ids)
    by_desc, _ = _load_foundation_foods(nutrients)
    portions = _load_portions(foundation_ids, measure_units)

    app = create_app()
    updated = skipped = missing_nutrient = 0

    with app.app_context():
        recipes = Recipe.query.order_by(Recipe.meal_name).all()
        for recipe in recipes:
            fdc = _match_fdc(recipe.meal_name, by_desc)
            if not fdc:
                print(f"  skip (no FDC match): {recipe.meal_name}")
                skipped += 1
                continue

            fdc_id = fdc["fdc_id"]
            nut = nutrients.get(fdc_id)
            if not nut or "energy" not in nut:
                print(f"  skip (no nutrients): {recipe.meal_name} -> {fdc['description']}")
                missing_nutrient += 1
                continue

            portion = portions.get(fdc_id)
            if portion:
                gram_weight = portion["gram_weight"]
                quantity = portion["quantity"]
                unit = portion["unit_of_measurement"]
            else:
                gram_weight = 100.0
                quantity = 100.0
                unit = "100 g"

            scaled = _scaled_nutrition(nut, gram_weight)
            source = f"USDA Foundation Foods (FDC {fdc_id})"

            print(
                f"  {'[dry-run] ' if dry_run else ''}update {recipe.meal_name}: "
                f"cal {recipe.calories} -> {scaled['calories']}, "
                f"qty {recipe.quantity} -> {quantity} {unit}, "
                f"from '{fdc['description']}'"
            )

            if not dry_run:
                recipe.calories = scaled["calories"]
                recipe.protein_g = scaled["protein_g"]
                recipe.fiber_g = scaled["fiber_g"]
                recipe.quantity = quantity
                recipe.unit_of_measurement = unit
                recipe.source = source
                if not recipe.description or (recipe.description or "").startswith("Fresh "):
                    recipe.description = fdc["description"]
                updated += 1
            else:
                updated += 1

        if not dry_run and updated:
            db.session.commit()

    print(
        f"\nDone. matched/updated={updated}, skipped={skipped}, "
        f"missing_nutrients={missing_nutrient}"
        + (" (dry run — no DB changes)" if dry_run else "")
    )
    return 0


def main():
    parser = argparse.ArgumentParser(description="Import USDA Foundation Foods into Recipe rows")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned updates without writing to the database",
    )
    args = parser.parse_args()
    return run_import(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
