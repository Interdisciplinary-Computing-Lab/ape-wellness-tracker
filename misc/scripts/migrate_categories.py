#!/usr/bin/env python3
"""
Migration script to add FoodCategory table and populate with default categories.
Run this script to set up the food category management system.
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend import create_app
from backend.extensions import db
from backend.models.entry import FoodCategory

def create_default_categories():
    """Create default food categories"""
    default_categories = [
        {
            'name': 'Fruits',
            'description': 'Fresh fruits and berries',
            'icon': 'fas fa-apple-alt',
            'color': 'badge-success',
            'sort_order': 1
        },
        {
            'name': 'Vegetables',
            'description': 'Fresh vegetables and greens',
            'icon': 'fas fa-carrot',
            'color': 'badge-info',
            'sort_order': 2
        },
        {
            'name': 'Grains & Starches',
            'description': 'Bread, rice, pasta, and other grains',
            'icon': 'fas fa-bread-slice',
            'color': 'badge-warning',
            'sort_order': 3
        },
        {
            'name': 'Protein Sources',
            'description': 'Meat, fish, eggs, and other protein-rich foods',
            'icon': 'fas fa-egg',
            'color': 'badge-danger',
            'sort_order': 4
        },
        {
            'name': 'Nuts & Seeds',
            'description': 'Nuts, seeds, and legumes',
            'icon': 'fas fa-seedling',
            'color': 'badge-primary',
            'sort_order': 5
        },
        {
            'name': 'Dairy & Alternatives',
            'description': 'Milk, cheese, yogurt, and dairy alternatives',
            'icon': 'fas fa-cheese',
            'color': 'badge-info',
            'sort_order': 6
        },
        {
            'name': 'Dried Fruits',
            'description': 'Dried fruits and fruit snacks',
            'icon': 'fas fa-apple-alt',
            'color': 'badge-secondary',
            'sort_order': 7
        },
        {
            'name': 'Enrichment Treats',
            'description': 'Special treats for enrichment and training',
            'icon': 'fas fa-ice-cream',
            'color': 'badge-secondary',
            'sort_order': 8
        },
        {
            'name': 'Mixed Meals & Combinations',
            'description': 'Combined meals and prepared dishes',
            'icon': 'fas fa-utensils',
            'color': 'badge-dark',
            'sort_order': 9
        }
    ]
    
    created_count = 0
    for category_data in default_categories:
        # Check if category already exists
        existing = FoodCategory.query.filter_by(name=category_data['name']).first()
        if not existing:
            category = FoodCategory(**category_data)
            db.session.add(category)
            created_count += 1
            print(f"Created category: {category_data['name']}")
        else:
            print(f"Category already exists: {category_data['name']}")
    
    return created_count

def main():
    """Main migration function"""
    print("Starting FoodCategory migration...")
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Create tables
            print("Creating database tables...")
            db.create_all()
            print(" Database tables created successfully")
            
            # Create default categories
            print("\nCreating default food categories...")
            created_count = create_default_categories()
            
            # Commit changes
            db.session.commit()
            print(f" Migration completed successfully!")
            print(f" Created {created_count} new categories")
            
            # Show all categories
            print("\nCurrent food categories:")
            categories = FoodCategory.query.order_by(FoodCategory.sort_order).all()
            for category in categories:
                print(f"  - {category.name} (ID: {category.id}, Order: {category.sort_order})")
            
        except Exception as e:
            db.session.rollback()
            print(f" Migration failed: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    main() 