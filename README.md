# Ape Meal Tracker

A staff-facing meal logging and nutrition tracking application built for Ape Initiative’s bonobo care team, designed to produce consistent, reportable feeding data.

## Problem

Meal logging for animal care teams can become inconsistent when entries depend on memory, manual calculations, or on-the-fly notes. The goal of this project is to make logging fast for staff while keeping nutrition totals accurate and reportable.

## Solution

This application provides a structured workflow for recording meals, managing a shared food catalog, and generating nutrition summaries that can be exported for documentation and review.

## Core features

- **Fast meal logging**: log meals for multiple apes in one session using date, time period, and meal type.
- **Nutrition scaling**: calories, protein, and fiber scale from catalog defaults based on serving quantity and unit changes.
- **Shared food catalog**: kitchen cheat-sheet foods plus staff-added custom foods, with favorites for quick reuse.
- **Custom food details**: add calories, protein, fiber, and optional notes when creating custom items.
- **Reliable reporting**: view per-ape totals and meal-type breakdowns (Forage, Enrichment, Reward, Other), then export to CSV.
- **Persistent catalog edits**: staff updates to existing catalog foods remain intact across restarts.

## Technical highlights

- Implemented a **unit/quantity normalization flow** so nutrition values remain consistent when staff change servings.
- Added a **meal-type taxonomy migration path** that maps legacy labels to current labels without breaking historical records.
- Introduced **versioned startup data migration logic** for targeted catalog corrections while preserving user edits.
- Built a **role-aware staff workflow** with authentication and shared catalog management.

## Tech stack

- **Languages**: Python, HTML, CSS, JavaScript
- **Backend**: Flask, SQLAlchemy
- **Frontend**: Jinja templates, Bootstrap, vanilla JavaScript
- **Database**: SQLite
- **Authentication**: `flask-security-too`

## Running locally

- Install dependencies from `requirements.txt`
- Run the app: `python run.py`

