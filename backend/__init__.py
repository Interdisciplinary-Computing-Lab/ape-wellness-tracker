from flask import Flask
import os
from backend.extensions import db
from backend.security import init_security
from backend.routes.main import site
from backend.helpers import get_time_period_display

def create_app():
    app = Flask(__name__, instance_relative_config=True, static_folder='static', static_url_path='/static')

    # Ensure instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Ensure SQLite DB path resolves to the instance directory for cross-OS consistency
    db_path = os.path.join(app.instance_path, 'database.db').replace('\\', '/')
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "super-secret-key"
    app.config["SECURITY_PASSWORD_SALT"] = "super-salty-salt"
    app.config["SECURITY_PASSWORD_HASH"] = "bcrypt"
    app.config["SECURITY_REGISTERABLE"] = True
    app.config["SECURITY_SEND_REGISTER_EMAIL"] = False


    db.init_app(app)
    init_security(app)

    app.register_blueprint(site)
    
    # Add helper functions to template context
    @app.context_processor
    def utility_processor():
        return dict(get_time_period_display=get_time_period_display)

    with app.app_context():
        db.create_all()
        
        # Ensure standard apes exist when app starts
        ensure_standard_apes()
        
        # Ensure standard food categories and recipes exist
        ensure_standard_food_data()

    return app

def ensure_standard_apes():
    """Ensure all standard apes exist in the database"""
    from backend.models.entry import Apes
    from datetime import date
    
    standard_apes = [
        {
            'ape_name': 'MAISHA',
            'birthday': date(2000, 5, 28),
            'weight': 42.5,
            'mother': 'Matata',
            'image_filename': 'maisha.jpg'
        },
        {
            'ape_name': 'TECO',
            'birthday': date(2010, 6, 1),
            'weight': 38.2,
            'mother': None,
            'image_filename': 'teco.jpg'
        },
        {
            'ape_name': 'NYOTA',
            'birthday': date(1998, 4, 4),
            'weight': 45.8,
            'mother': None,
            'image_filename': 'nyota.jpg'
        },
        {
            'ape_name': 'CLARA',
            'birthday': date(2010, 5, 27),
            'weight': 39.1,
            'mother': None,
            'image_filename': 'clara.jpg'
        },
        {
            'ape_name': 'MALI',
            'birthday': date(2007, 9, 4),
            'weight': 41.3,
            'mother': None,
            'image_filename': 'mali.jpg'
        },
        {
            'ape_name': 'ELIKYA',
            'birthday': date(1997, 6, 28),
            'weight': 44.7,
            'mother': 'Matata',
            'image_filename': 'elikya.jpg'
        }
    ]
    
    created_count = 0
    for ape_data in standard_apes:
        existing_ape = Apes.query.filter_by(ape_name=ape_data['ape_name']).first()
        if not existing_ape:
            new_ape = Apes(**ape_data)
            db.session.add(new_ape)
            created_count += 1
    
    if created_count > 0:
        db.session.commit()
        print(f"[SUCCESS] Created {created_count} standard apes for new users")

def ensure_standard_food_data():
    """Ensure standard food categories and recipes exist in the database"""
    from backend.models.entry import FoodCategory, Recipe
    
    # Standard food categories
    standard_categories = [
        {'name': 'Fruits', 'description': 'Fresh and dried fruits', 'icon': 'fas fa-apple-alt', 'color': 'badge-success', 'sort_order': 1},
        {'name': 'Vegetables', 'description': 'Fresh vegetables and greens', 'icon': 'fas fa-carrot', 'color': 'badge-success', 'sort_order': 2},
        {'name': 'Protein', 'description': 'Meat, fish, eggs, and plant proteins', 'icon': 'fas fa-drumstick-bite', 'color': 'badge-danger', 'sort_order': 3},
        {'name': 'Grains', 'description': 'Rice, bread, cereals, and pasta', 'icon': 'fas fa-bread-slice', 'color': 'badge-warning', 'sort_order': 4},
        {'name': 'Dairy', 'description': 'Milk, cheese, and dairy products', 'icon': 'fas fa-cheese', 'color': 'badge-info', 'sort_order': 5},
        {'name': 'Treats', 'description': 'Special treats and snacks', 'icon': 'fas fa-cookie-bite', 'color': 'badge-secondary', 'sort_order': 6},
        {'name': 'Other', 'description': 'Miscellaneous food items', 'icon': 'fas fa-utensils', 'color': 'badge-light', 'sort_order': 7}
    ]
    
    created_categories = 0
    for cat_data in standard_categories:
        existing_category = FoodCategory.query.filter_by(name=cat_data['name']).first()
        if not existing_category:
            new_category = FoodCategory(**cat_data)
            db.session.add(new_category)
            created_categories += 1
    
    if created_categories > 0:
        db.session.commit()
        print(f"[SUCCESS] Created {created_categories} standard food categories")
    
    # Standard recipes
    standard_recipes = [
        {'meal_name': 'Banana', 'description': 'Fresh banana', 'calories': 105, 'food_category': 'Fruits'},
        {'meal_name': 'Apple', 'description': 'Fresh apple', 'calories': 95, 'food_category': 'Fruits'},
        {'meal_name': 'Orange', 'description': 'Fresh orange', 'calories': 62, 'food_category': 'Fruits'},
        {'meal_name': 'Carrot', 'description': 'Fresh carrot', 'calories': 25, 'food_category': 'Vegetables'},
        {'meal_name': 'Lettuce', 'description': 'Fresh lettuce', 'calories': 5, 'food_category': 'Vegetables'},
        {'meal_name': 'Chicken', 'description': 'Cooked chicken breast', 'calories': 165, 'food_category': 'Protein'},
        {'meal_name': 'Egg', 'description': 'Hard-boiled egg', 'calories': 70, 'food_category': 'Protein'},
        {'meal_name': 'Rice', 'description': 'Cooked white rice', 'calories': 130, 'food_category': 'Grains'},
        {'meal_name': 'Bread', 'description': 'Slice of bread', 'calories': 80, 'food_category': 'Grains'},
        {'meal_name': 'Milk', 'description': 'Whole milk', 'calories': 150, 'food_category': 'Dairy'},
        {'meal_name': 'Popcorn', 'description': 'Air-popped popcorn', 'calories': 31, 'food_category': 'Treats'},
        {'meal_name': 'Crackers', 'description': 'Plain crackers', 'calories': 20, 'food_category': 'Treats'}
    ]
    
    created_recipes = 0
    for recipe_data in standard_recipes:
        existing_recipe = Recipe.query.filter_by(meal_name=recipe_data['meal_name']).first()
        if not existing_recipe:
            new_recipe = Recipe(**recipe_data)
            db.session.add(new_recipe)
            created_recipes += 1
    
    if created_recipes > 0:
        db.session.commit()
        print(f"[SUCCESS] Created {created_recipes} standard recipes")