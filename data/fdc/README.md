# USDA FoodData Central (Foundation Foods)

Place downloaded USDA CSV files here. **Do not commit** the raw zip or extracted CSVs (they are gitignored).

## Directory layout

```
data/fdc/
  README.md          ← this file (committed)
  raw/               ← extract USDA zip here (gitignored)
    food.csv
    food_nutrient.csv
    nutrient.csv
    food_portion.csv
    ...
  .gitkeep           ← optional, keeps raw/ in repo structure
```

## Download steps

1. Open [USDA FoodData Central – Downloadable Data](https://fdc.nal.usda.gov/download-datasets/).
2. Under **Foundation Foods**, download the latest **CSV** zip (e.g. `FoodData_Central_foundation_food_csv_2025-12-18.zip`).
3. Extract the zip into `data/fdc/raw/` so files like `food.csv` sit directly under `raw/`.

### Windows (PowerShell, from project root)

```powershell
New-Item -ItemType Directory -Force -Path "data\fdc\raw"
Invoke-WebRequest -Uri "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_csv_2025-12-18.zip" -OutFile "data\fdc\foundation.zip"
Expand-Archive -Path "data\fdc\foundation.zip" -DestinationPath "data\fdc\raw" -Force
```

Check [fdc.nal.usda.gov/download-datasets](https://fdc.nal.usda.gov/download-datasets/) for the current zip filename if the link above is outdated.

## Attribution

Nutrition data from [USDA FoodData Central](https://fdc.nal.usda.gov/) (public domain). Credit USDA when displaying sources in the app.

## Import into the app

After CSVs are in `data/fdc/raw/`, run from the project root:

```powershell
# Preview
python misc/scripts/import_fdc_foundation.py --dry-run --import-all

# Import full Foundation Foods catalog (~300+ items, categories mapped)
python misc/scripts/import_fdc_foundation.py --import-all

# Or only refresh foods already in your catalog
python misc/scripts/import_fdc_foundation.py
```

**Data used:** `foundation_food.csv`, `food.csv`, `food_nutrient.csv`, `food_portion.csv`, `measure_unit.csv`, and `data/fdc/category_map.json` (maps USDA categories → app food categories).

**Calories:** Nutrients are per 100 g in FDC; the importer scales to the first portion in `food_portion.csv` (e.g. 1 banana, 1 cup). Logging uses `(recipe calories / recipe quantity) × amount`.

**Skipped by default:** Restaurant, fast food, and branded FDC categories (see `exclude_fdc_category_ids` in `category_map.json`). Use `--include-excluded` to import those too.

Each imported `Recipe` gets `fdc_id`, `source` = `USDA Foundation Foods (FDC {id})`, and `food_category` / `category_id` from the map.

## Staff custom names

`data/fdc/custom_foods.json` maps display names to FDC items (e.g. **Cheese Toothpaste** → cream cheese, **Trash Lettuce** → Brussels sprouts). To drop legacy seed foods and keep only USDA + those two:

```powershell
python misc/scripts/prune_non_fdc_foods.py --dry-run
python misc/scripts/prune_non_fdc_foods.py
```
