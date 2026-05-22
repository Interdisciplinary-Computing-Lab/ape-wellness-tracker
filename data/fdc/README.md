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

## Import (planned)

A future script `misc/scripts/import_fdc_foundation.py` will read `data/fdc/raw/` and upsert `Recipe` rows with `source` like `USDA Foundation Foods (FDC {id})`.
