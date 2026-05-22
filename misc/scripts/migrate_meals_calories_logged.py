#!/usr/bin/env python3
"""Add meals.calories_logged and backfill from recipe.calories."""

import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from backend.utils.schema_migrations import ensure_meals_calories_logged


def main():
    instance_path = os.path.join(project_root, 'instance')
    db_path = os.path.join(instance_path, 'database.db').replace('\\', '/')
    db_uri = f'sqlite:///{db_path}'
    ensure_meals_calories_logged(db_uri, instance_path)
    print('Migration complete (meals.calories_logged).')


if __name__ == '__main__':
    main()
