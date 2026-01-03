import os
import sys
import json
import secrets
import warnings
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv
from backend.extensions import db
from backend.security import init_security
from backend.routes import site
from backend.helpers import get_time_period_display

# Load environment variables from .env file if it exists
# This allows local development to use .env while production uses system env vars
load_dotenv()

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def create_app():
    # Determine template and static folder paths
    if getattr(sys, 'frozen', False):
        # When frozen, resources are in _MEIPASS or next to executable
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(sys.executable)
        
        template_folder = os.path.join(base_path, 'backend', 'templates')
        static_folder = os.path.join(base_path, 'backend', 'static')
    else:
        # Development mode - use relative paths
        template_folder = os.path.join(os.path.dirname(__file__), 'templates')
        static_folder = os.path.join(os.path.dirname(__file__), 'static')
    
    app = Flask(
        __name__, 
        instance_relative_config=True,
        template_folder=template_folder,
        static_folder=static_folder,
        static_url_path='/static'
    )
    
    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Ensure instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Ensure SQLite DB path resolves to the instance directory for cross-OS consistency
    db_path = os.path.join(app.instance_path, 'database.db').replace('\\', '/')
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Security Configuration - Load from environment variables
    # SECRET_KEY: Used for session management, CSRF protection, and signing cookies
    # SECURITY_PASSWORD_SALT: Used for password hashing to prevent rainbow table attacks
    # 
    # Best Practice: Never hardcode secrets in source code. Use environment variables
    # or a secrets management service (AWS Secrets Manager, Azure Key Vault, etc.)
    # Reference: OWASP Flask Security Cheat Sheet, 12-Factor App methodology
    # 
    # For local development: Create a .env file with these values
    # For production: Set these as environment variables on your server
    secret_key = os.getenv('SECRET_KEY')
    password_salt = os.getenv('SECURITY_PASSWORD_SALT')
    
    if not secret_key:
        # Generate a secure random key as fallback, but warn the user
        secret_key = secrets.token_urlsafe(32)
        warnings.warn(
            "SECRET_KEY not set in environment. Generated a temporary key. "
            "This key will change on each restart. Set SECRET_KEY in your .env file or "
            "environment variables for production use.",
            UserWarning
        )
    
    if not password_salt:
        # Generate a secure random salt as fallback, but warn the user
        password_salt = secrets.token_urlsafe(16)
        warnings.warn(
            "SECURITY_PASSWORD_SALT not set in environment. Generated a temporary salt. "
            "This salt will change on each restart. Set SECURITY_PASSWORD_SALT in your .env "
            "file or environment variables for production use.",
            UserWarning
        )
    
    app.config["SECRET_KEY"] = secret_key
    app.config["SECURITY_PASSWORD_SALT"] = password_salt
    app.config["SECURITY_PASSWORD_HASH"] = "bcrypt"
    app.config["SECURITY_REGISTERABLE"] = True
    app.config["SECURITY_SEND_REGISTER_EMAIL"] = False
    app.config["SECURITY_CONFIRMABLE"] = False  # Auto-confirm users on registration
    
    # Ensure CSRF protection is enabled for Flask-Security forms
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_TIME_LIMIT"] = None  # No time limit for CSRF tokens

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
    """Ensure all standard apes exist in the database - loaded from data file"""
    from backend.models.entry import Apes
    from datetime import date
    
    # Load ape data from JSON file
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'default_apes.json')
    
    try:
        with open(data_path, 'r') as f:
            standard_apes = json.load(f)
    except FileNotFoundError:
        print(f"[WARNING] Default apes data file not found at {data_path}. Skipping ape initialization.")
        return
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse default apes data file: {e}. Skipping ape initialization.")
        return
    
    created_count = 0
    for ape_data in standard_apes:
        existing_ape = Apes.query.filter_by(ape_name=ape_data['ape_name']).first()
        if not existing_ape:
            # Convert birthday string to date object
            if 'birthday' in ape_data and isinstance(ape_data['birthday'], str):
                ape_data['birthday'] = date.fromisoformat(ape_data['birthday'])
            new_ape = Apes(**ape_data)
            db.session.add(new_ape)
            created_count += 1
    
    if created_count > 0:
        db.session.commit()
        print(f"[SUCCESS] Created {created_count} standard apes for new users")

def ensure_standard_food_data():
    """Ensure comprehensive food categories and recipes exist in the database - loaded from data file"""
    from backend.models.entry import FoodCategory, Recipe
    
    # Load food data from JSON file
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'default_foods.json')
    
    try:
        with open(data_path, 'r') as f:
            food_data = json.load(f)
    except FileNotFoundError:
        print(f"[WARNING] Default foods data file not found at {data_path}. Skipping food initialization.")
        return
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse default foods data file: {e}. Skipping food initialization.")
        return
    
    # Load categories
    standard_categories = food_data.get('categories', [])
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
    
    # Load recipes
    comprehensive_recipes = food_data.get('recipes', [])
    created_recipes = 0
    for recipe_data in comprehensive_recipes:
        existing_recipe = Recipe.query.filter_by(meal_name=recipe_data['meal_name']).first()
        if not existing_recipe:
            # Ensure protein_g and fiber_g have defaults if not provided
            recipe_data.setdefault('protein_g', 2.0)
            recipe_data.setdefault('fiber_g', 1.0)
            new_recipe = Recipe(**recipe_data)
            db.session.add(new_recipe)
            created_recipes += 1
    
    if created_recipes > 0:
        db.session.commit()
        print(f"[SUCCESS] Created {created_recipes} comprehensive recipes")
