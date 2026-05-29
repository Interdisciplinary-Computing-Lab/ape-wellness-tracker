"""
Load USDA FoodData Central Foundation Foods CSVs from data/fdc/raw/.
"""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass
from typing import Iterator

NUTRIENT_ENERGY_IDS = ("1008", "2048", "2047")
NUTRIENT_PROTEIN = "1003"
NUTRIENT_FIBER = "1079"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "fdc", "raw")
CATEGORY_MAP_PATH = os.path.join(PROJECT_ROOT, "data", "fdc", "category_map.json")

MEAL_NAME_MAX_LEN = 120


@dataclass
class FdcFoodRecord:
    fdc_id: str
    description: str
    food_category_id: str
    publication_date: str
    app_category: str
    calories: int
    protein_g: float
    fiber_g: float
    quantity: float
    unit_of_measurement: str
    energy_per_100g: float
    gram_weight: float
    meal_name: str
    source: str


def _normalize_desc(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ").strip().lower())


def load_category_map(path: str | None = None) -> dict:
    path = path or CATEGORY_MAP_PATH
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def resolve_app_category(
    food_category_id: str,
    description: str,
    category_map: dict,
) -> str | None:
    """Return app category name, or None if this FDC category is excluded."""
    exclude = set(category_map.get("exclude_fdc_category_ids", []))
    if str(food_category_id) in exclude:
        return None

    fdc_to_app = category_map.get("fdc_to_app_category", {})
    base = fdc_to_app.get(str(food_category_id), category_map.get("default_category", "Other"))

    dried_cat_id = str(category_map.get("dried_fruit_fdc_category_id", "9"))
    if str(food_category_id) == dried_cat_id:
        desc_lower = description.lower()
        for kw in category_map.get("dried_fruit_keywords", []):
            if kw in desc_lower:
                return category_map.get("dried_fruit_category", "Dried Fruits")

    return base


def make_meal_name(description: str, fdc_id: str, max_len: int = MEAL_NAME_MAX_LEN) -> str:
    """Unique display name for Recipe.meal_name."""
    desc = re.sub(r"\s+", " ", description.replace("\xa0", " ").strip())
    if len(desc) <= max_len:
        return desc
    suffix = f" ({fdc_id})"
    trim = max_len - len(suffix)
    return desc[:trim].rstrip(" ,") + suffix


def scaled_nutrition(nutrients: dict, gram_weight: float) -> dict:
    factor = gram_weight / 100.0
    energy = nutrients.get("energy")
    if energy is None:
        raise ValueError("missing energy nutrient")
    return {
        "calories": max(0, round(energy * factor)),
        "protein_g": round(nutrients.get("protein", 0) * factor, 2),
        "fiber_g": round(nutrients.get("fiber", 0) * factor, 2),
        "energy_per_100g": energy,
        "gram_weight": gram_weight,
    }


class FdcFoundationLoader:
    def __init__(self, raw_dir: str | None = None):
        self.raw_dir = raw_dir or RAW_DIR
        self._measure_units: dict[str, str] | None = None

    def _path(self, name: str) -> str:
        return os.path.join(self.raw_dir, name)

    def foundation_ids(self) -> set[str]:
        path = self._path("foundation_food.csv")
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Missing {path}")
        ids: set[str] = set()
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                ids.add(row["fdc_id"])
        return ids

    def load_measure_units(self) -> dict[str, str]:
        if self._measure_units is not None:
            return self._measure_units
        units: dict[str, str] = {}
        with open(self._path("measure_unit.csv"), encoding="utf-8") as f:
            for row in csv.DictReader(f):
                units[row["id"]] = row["name"]
        self._measure_units = units
        return units

    def load_nutrients(self, foundation_ids: set[str]) -> dict[str, dict[str, float]]:
        wanted = set(NUTRIENT_ENERGY_IDS) | {NUTRIENT_PROTEIN, NUTRIENT_FIBER}
        out: dict[str, dict[str, float]] = {}
        with open(self._path("food_nutrient.csv"), encoding="utf-8") as f:
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
                if nid in NUTRIENT_ENERGY_IDS:
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

    def load_portions(self, foundation_ids: set[str]) -> dict[str, dict]:
        measure_units = self.load_measure_units()
        best: dict[str, dict] = {}
        with open(self._path("food_portion.csv"), encoding="utf-8") as f:
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

    def load_foods_by_fdc_id(self, nutrients: dict[str, dict[str, float]]) -> dict[str, dict]:
        """fdc_id -> best food.csv row for foundation foods."""
        foundation_ids = self.foundation_ids()
        by_fdc: dict[str, dict] = {}
        with open(self._path("food.csv"), encoding="utf-8") as f:
            for row in csv.DictReader(f):
                fdc_id = row["fdc_id"]
                if fdc_id not in foundation_ids or row["data_type"] != "foundation_food":
                    continue
                pub = row.get("publication_date") or ""
                existing = by_fdc.get(fdc_id)
                if not existing or pub > existing["publication_date"]:
                    by_fdc[fdc_id] = {
                        "fdc_id": fdc_id,
                        "description": row["description"],
                        "food_category_id": row.get("food_category_id") or "",
                        "publication_date": pub,
                    }

        # Prefer fdc_id rows that have energy data when duplicates exist in food.csv
        deduped: dict[str, dict] = {}
        desc_groups: dict[str, list[dict]] = {}
        for item in by_fdc.values():
            key = _normalize_desc(item["description"])
            desc_groups.setdefault(key, []).append(item)

        for _key, rows in desc_groups.items():
            with_energy = [r for r in rows if "energy" in nutrients.get(r["fdc_id"], {})]
            pool = with_energy or rows
            chosen = max(pool, key=lambda r: r["publication_date"])
            deduped[chosen["fdc_id"]] = chosen

        return deduped

    def iter_records(
        self,
        category_map: dict | None = None,
        *,
        include_excluded_categories: bool = False,
    ) -> Iterator[FdcFoodRecord]:
        category_map = category_map or load_category_map()
        foundation_ids = self.foundation_ids()
        nutrients = self.load_nutrients(foundation_ids)
        portions = self.load_portions(foundation_ids)
        foods = self.load_foods_by_fdc_id(nutrients)

        for fdc_id, food in sorted(foods.items(), key=lambda x: x[1]["description"].lower()):
            app_cat = resolve_app_category(
                food["food_category_id"],
                food["description"],
                category_map,
            )
            if app_cat is None and not include_excluded_categories:
                continue

            nut = nutrients.get(fdc_id)
            if not nut or "energy" not in nut:
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

            scaled = scaled_nutrition(nut, gram_weight)
            description = food["description"]
            yield FdcFoodRecord(
                fdc_id=fdc_id,
                description=description,
                food_category_id=food["food_category_id"],
                publication_date=food["publication_date"],
                app_category=app_cat or category_map.get("default_category", "Other"),
                calories=scaled["calories"],
                protein_g=scaled["protein_g"],
                fiber_g=scaled["fiber_g"],
                quantity=quantity,
                unit_of_measurement=unit,
                energy_per_100g=scaled["energy_per_100g"],
                gram_weight=gram_weight,
                meal_name=make_meal_name(description, fdc_id),
                source=f"USDA Foundation Foods (FDC {fdc_id})",
            )
