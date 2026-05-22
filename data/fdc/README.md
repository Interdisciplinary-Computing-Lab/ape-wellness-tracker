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
python misc/scripts/import_fdc_foundation.py --dry-run
python misc/scripts/import_fdc_foundation.py
```

This updates **existing** food catalog (`Recipe`) rows when a Foundation Foods match exists. Values are scaled from FDC per-100g data using the first listed portion weight (e.g. one medium banana). Unmatched catalog items are left unchanged.

`source` is set to `USDA Foundation Foods (FDC {id})`.
