# Ape Diet & Wellness Tracker

Flask-based web application for logging dietary meals and tracking nutrition totals for bonobo apes at Ape Initiative.

## What’s inside

- **Meal logging** for staff across multiple apes
- **Food catalog** (kitchen cheat-sheet) with **staff favorites**
- **Custom foods** with nutrition inputs (calories, protein, fiber) and optional notes
- **Reports** with meal and feeding-purpose breakdowns, plus CSV export

## Staff workflow

### 1) Log meals

1. Choose a **date**.
2. Choose a **time period** (Morning / Afternoon / Evening).
3. Select a **meal type** (Forage / Enrichment / Reward / Other).
4. Select one or more apes.
5. Add foods from the catalog:
   - Quantity can be adjusted per item.
   - For supported foods, unit changes keep nutrition consistent.
6. Review the on-screen totals.
7. Click **Save Meals** to persist the log to the database.

**Save behavior**
- Meal entries are **saved only when you click Save Meals**.
- Quick-added custom foods are **saved to the catalog immediately**.

### 2) Edit foods

Use **Manage Foods** to update catalog entries:
- calories
- serving quantity + unit
- protein (g) and fiber (g)
- description/notes and category
- favorites

Changes made in **Manage Foods** persist across restarts.

## Catalog + custom foods

### Kitchen cheat-sheet foods

The default food catalog is seeded from `data/kitchen_foods.json`.
If a kitchen food already exists in the database, staff edits are authoritative.

### Custom foods

When staff quick-add a custom food, the form captures:
- **Calories**
- **Protein (g)**
- **Fiber (g)**
- **Notes** (optional)
- Serving **quantity** and **unit**

Protein and fiber values are included in meal reports and CSV exports.

## Meal types (feeding purposes)

Meal type values used throughout the UI and reports:
- **Forage**
- **Enrichment**
- **Reward**
- **Other**

Time-of-day defaults map to feeding purposes, but staff can override the meal type per log.

## Development

### Requirements

Python dependencies are listed in `requirements.txt`.

### Run locally

From the project root:

```bash
pip install -r requirements.txt
python run.py
```

`run.py` starts the Flask app in debug mode (default port `5003`).

