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
    """Ensure comprehensive food categories and recipes exist in the database"""
    from backend.models.entry import FoodCategory, Recipe
    
    # Comprehensive food categories based on the full seed data
    standard_categories = [
        {'name': 'Fruits', 'description': 'Fresh and dried fruits', 'icon': 'fas fa-apple-alt', 'color': 'badge-success', 'sort_order': 1},
        {'name': 'Vegetables', 'description': 'Fresh vegetables and greens', 'icon': 'fas fa-carrot', 'color': 'badge-success', 'sort_order': 2},
        {'name': 'Grains & Starches', 'description': 'Rice, oats, quinoa, and starchy vegetables', 'icon': 'fas fa-bread-slice', 'color': 'badge-warning', 'sort_order': 3},
        {'name': 'Protein Sources', 'description': 'Legumes, eggs, and plant proteins', 'icon': 'fas fa-drumstick-bite', 'color': 'badge-danger', 'sort_order': 4},
        {'name': 'Nuts & Seeds', 'description': 'Almonds, walnuts, seeds, and nuts', 'icon': 'fas fa-seedling', 'color': 'badge-warning', 'sort_order': 5},
        {'name': 'Dairy & Alternatives', 'description': 'Yogurt, milk alternatives, and dairy products', 'icon': 'fas fa-cheese', 'color': 'badge-info', 'sort_order': 6},
        {'name': 'Dried Fruits', 'description': 'Dried fruits and fruit preserves', 'icon': 'fas fa-apple-alt', 'color': 'badge-success', 'sort_order': 7},
        {'name': 'Enrichment Treats', 'description': 'Special treats and enrichment items', 'icon': 'fas fa-cookie-bite', 'color': 'badge-secondary', 'sort_order': 8},
        {'name': 'Mixed Meals & Combinations', 'description': 'Combined meals and mixed dishes', 'icon': 'fas fa-utensils', 'color': 'badge-primary', 'sort_order': 9}
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
        print(f"[SUCCESS] Created {created_categories} comprehensive food categories")
    
    # Comprehensive recipes from the full seed data
    comprehensive_recipes = [
        # Fruits (primary staple)
        {'meal_name': 'Banana', 'description': 'Fresh banana', 'calories': 105, 'food_category': 'Fruits'},
        {'meal_name': 'Apple', 'description': 'Fresh apple', 'calories': 95, 'food_category': 'Fruits'},
        {'meal_name': 'Grapes', 'description': 'Fresh grapes', 'calories': 62, 'food_category': 'Fruits'},
        {'meal_name': 'Blueberries', 'description': 'Fresh blueberries', 'calories': 85, 'food_category': 'Fruits'},
        {'meal_name': 'Strawberries', 'description': 'Fresh strawberries', 'calories': 49, 'food_category': 'Fruits'},
        {'meal_name': 'Watermelon', 'description': 'Fresh watermelon', 'calories': 30, 'food_category': 'Fruits'},
        {'meal_name': 'Cantaloupe', 'description': 'Fresh cantaloupe', 'calories': 34, 'food_category': 'Fruits'},
        {'meal_name': 'Papaya', 'description': 'Fresh papaya', 'calories': 43, 'food_category': 'Fruits'},
        {'meal_name': 'Orange', 'description': 'Fresh orange', 'calories': 62, 'food_category': 'Fruits'},
        {'meal_name': 'Pear', 'description': 'Fresh pear', 'calories': 57, 'food_category': 'Fruits'},
        {'meal_name': 'Peach', 'description': 'Fresh peach', 'calories': 59, 'food_category': 'Fruits'},
        {'meal_name': 'Plum', 'description': 'Fresh plum', 'calories': 46, 'food_category': 'Fruits'},
        
        # Vegetables
        {'meal_name': 'Carrot', 'description': 'Fresh carrot', 'calories': 41, 'food_category': 'Vegetables'},
        {'meal_name': 'Sweet Potato', 'description': 'Cooked sweet potato', 'calories': 103, 'food_category': 'Vegetables'},
        {'meal_name': 'Cucumber', 'description': 'Fresh cucumber', 'calories': 16, 'food_category': 'Vegetables'},
        {'meal_name': 'Bell Pepper', 'description': 'Fresh bell pepper', 'calories': 31, 'food_category': 'Vegetables'},
        {'meal_name': 'Kale', 'description': 'Fresh kale', 'calories': 33, 'food_category': 'Vegetables'},
        {'meal_name': 'Romaine Lettuce', 'description': 'Fresh romaine lettuce', 'calories': 17, 'food_category': 'Vegetables'},
        {'meal_name': 'Collard Greens', 'description': 'Fresh collard greens', 'calories': 32, 'food_category': 'Vegetables'},
        {'meal_name': 'Spinach', 'description': 'Fresh spinach', 'calories': 23, 'food_category': 'Vegetables'},
        {'meal_name': 'Broccoli', 'description': 'Fresh broccoli', 'calories': 34, 'food_category': 'Vegetables'},
        {'meal_name': 'Cauliflower', 'description': 'Fresh cauliflower', 'calories': 25, 'food_category': 'Vegetables'},
        {'meal_name': 'Green Beans', 'description': 'Fresh green beans', 'calories': 31, 'food_category': 'Vegetables'},
        {'meal_name': 'Zucchini', 'description': 'Fresh zucchini', 'calories': 17, 'food_category': 'Vegetables'},
        {'meal_name': 'Tomato', 'description': 'Fresh tomato', 'calories': 22, 'food_category': 'Vegetables'},
        {'meal_name': 'Cabbage', 'description': 'Fresh cabbage', 'calories': 22, 'food_category': 'Vegetables'},
        
        # Grains & Starches
        {'meal_name': 'Cooked Rice', 'description': 'White rice, cooked', 'calories': 130, 'food_category': 'Grains & Starches'},
        {'meal_name': 'Brown Rice', 'description': 'Brown rice, cooked', 'calories': 111, 'food_category': 'Grains & Starches'},
        {'meal_name': 'Oatmeal', 'description': 'Cooked oatmeal', 'calories': 68, 'food_category': 'Grains & Starches'},
        {'meal_name': 'Quinoa', 'description': 'Cooked quinoa', 'calories': 120, 'food_category': 'Grains & Starches'},
        {'meal_name': 'Regular Potato', 'description': 'Boiled potato', 'calories': 77, 'food_category': 'Grains & Starches'},
        
        # Protein Sources
        {'meal_name': 'Lentils', 'description': 'Cooked lentils', 'calories': 116, 'food_category': 'Protein Sources'},
        {'meal_name': 'Boiled Egg', 'description': 'Hard boiled egg', 'calories': 78, 'food_category': 'Protein Sources'},
        {'meal_name': 'Chickpeas', 'description': 'Cooked chickpeas', 'calories': 134, 'food_category': 'Protein Sources'},
        {'meal_name': 'Black Beans', 'description': 'Cooked black beans', 'calories': 114, 'food_category': 'Protein Sources'},
        {'meal_name': 'Tofu', 'description': 'Firm tofu', 'calories': 76, 'food_category': 'Protein Sources'},
        
        # Nuts & Seeds
        {'meal_name': 'Almonds', 'description': 'Raw almonds (small portion)', 'calories': 164, 'food_category': 'Nuts & Seeds'},
        {'meal_name': 'Peanuts', 'description': 'Raw peanuts (small portion)', 'calories': 166, 'food_category': 'Nuts & Seeds'},
        {'meal_name': 'Sunflower Seeds', 'description': 'Raw sunflower seeds (small portion)', 'calories': 164, 'food_category': 'Nuts & Seeds'},
        {'meal_name': 'Walnuts', 'description': 'Raw walnuts (small portion)', 'calories': 185, 'food_category': 'Nuts & Seeds'},
        {'meal_name': 'Pumpkin Seeds', 'description': 'Raw pumpkin seeds (small portion)', 'calories': 151, 'food_category': 'Nuts & Seeds'},
        {'meal_name': 'Cashews', 'description': 'Raw cashews (small portion)', 'calories': 157, 'food_category': 'Nuts & Seeds'},
        
        # Dairy & Alternatives
        {'meal_name': 'Yogurt', 'description': 'Plain yogurt', 'calories': 59, 'food_category': 'Dairy & Alternatives'},
        {'meal_name': 'Cottage Cheese', 'description': 'Low-fat cottage cheese', 'calories': 98, 'food_category': 'Dairy & Alternatives'},
        {'meal_name': 'Almond Milk', 'description': 'Unsweetened almond milk', 'calories': 30, 'food_category': 'Dairy & Alternatives'},
        {'meal_name': 'Soy Milk', 'description': 'Unsweetened soy milk', 'calories': 80, 'food_category': 'Dairy & Alternatives'},
        
        # Dried Fruits
        {'meal_name': 'Dried Apricots', 'description': 'Dried apricots', 'calories': 48, 'food_category': 'Dried Fruits'},
        {'meal_name': 'Dried Cranberries', 'description': 'Dried cranberries', 'calories': 46, 'food_category': 'Dried Fruits'},
        {'meal_name': 'Raisins', 'description': 'Dried raisins', 'calories': 85, 'food_category': 'Dried Fruits'},
        {'meal_name': 'Dried Figs', 'description': 'Dried figs', 'calories': 107, 'food_category': 'Dried Fruits'},
        {'meal_name': 'Dried Mango', 'description': 'Dried mango', 'calories': 319, 'food_category': 'Dried Fruits'},
        {'meal_name': 'Dried Pineapple', 'description': 'Dried pineapple', 'calories': 245, 'food_category': 'Dried Fruits'},
        
        # Enrichment Treats
        {'meal_name': 'Fruit Smoothie', 'description': 'Blended fruit smoothie', 'calories': 120, 'food_category': 'Enrichment Treats'},
        {'meal_name': 'Popcorn', 'description': 'Plain air-popped popcorn', 'calories': 31, 'food_category': 'Enrichment Treats'},
        {'meal_name': 'Fruit Juice Ice Pop', 'description': 'Natural fruit juice ice pop', 'calories': 45, 'food_category': 'Enrichment Treats'},
        {'meal_name': 'Frozen Grapes', 'description': 'Frozen grapes', 'calories': 62, 'food_category': 'Enrichment Treats'},
        {'meal_name': 'Frozen Banana', 'description': 'Frozen banana', 'calories': 105, 'food_category': 'Enrichment Treats'},
        {'meal_name': 'Fruit Popsicle', 'description': 'Homemade fruit popsicle', 'calories': 50, 'food_category': 'Enrichment Treats'},
        
        # Mixed Meals & Combinations
        {'meal_name': 'Fruit Salad', 'description': 'Mixed fresh fruit salad', 'calories': 85, 'food_category': 'Mixed Meals & Combinations'},
        {'meal_name': 'Vegetable Mix', 'description': 'Mixed fresh vegetables', 'calories': 45, 'food_category': 'Mixed Meals & Combinations'},
        {'meal_name': 'Rice and Vegetables', 'description': 'Cooked rice with mixed vegetables', 'calories': 175, 'food_category': 'Mixed Meals & Combinations'},
        {'meal_name': 'Oatmeal with Fruit', 'description': 'Oatmeal topped with fresh fruit', 'calories': 125, 'food_category': 'Mixed Meals & Combinations'},
        {'meal_name': 'Egg and Vegetables', 'description': 'Boiled egg with fresh vegetables', 'calories': 120, 'food_category': 'Mixed Meals & Combinations'},
        {'meal_name': 'Quinoa Bowl', 'description': 'Quinoa with vegetables and nuts', 'calories': 200, 'food_category': 'Mixed Meals & Combinations'},
        {'meal_name': 'Fruit and Nut Mix', 'description': 'Mixed dried fruits and nuts', 'calories': 180, 'food_category': 'Mixed Meals & Combinations'},
        {'meal_name': 'Yogurt Parfait', 'description': 'Yogurt with fruit and granola', 'calories': 150, 'food_category': 'Mixed Meals & Combinations'},
    ]
    
    created_recipes = 0
    for recipe_data in comprehensive_recipes:
        existing_recipe = Recipe.query.filter_by(meal_name=recipe_data['meal_name']).first()
        if not existing_recipe:
            new_recipe = Recipe(**recipe_data)
            db.session.add(new_recipe)
            created_recipes += 1
    
    if created_recipes > 0:
        db.session.commit()
        print(f"[SUCCESS] Created {created_recipes} comprehensive recipes")