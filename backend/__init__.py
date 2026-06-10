import os
import json
import secrets
import uuid
import warnings
from datetime import datetime
from pathlib import Path
from flask import Flask
from flask_security.utils import hash_password
from dotenv import load_dotenv
from backend.extensions import db
from backend.security import init_security
from backend.routes import site
from backend.helpers import get_time_period_display

# Load environment variables from .env file if it exists
# This allows local development to use .env while production uses system env vars
load_dotenv()


def _load_or_create_instance_secret(instance_path, filename, env_var, nbytes=32):
    """
    Prefer env var; otherwise reuse a secret stored under instance/ so local dev
    survives restarts (rotating secrets invalidate logins and CSRF tokens).
    """
    value = os.getenv(env_var)
    if value:
        return value
    path = os.path.join(instance_path, filename)
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            stored = f.read().strip()
            if stored:
                return stored
    value = secrets.token_urlsafe(nbytes)
    with open(path, "w", encoding="utf-8") as f:
        f.write(value)
    return value


def create_app():
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
    # For local development: optional .env; otherwise secrets persist in instance/
    # For production: set SECRET_KEY and SECURITY_PASSWORD_SALT as environment variables
    secret_key = _load_or_create_instance_secret(
        app.instance_path, ".secret_key", "SECRET_KEY", nbytes=32
    )
    password_salt = _load_or_create_instance_secret(
        app.instance_path, ".password_salt", "SECURITY_PASSWORD_SALT", nbytes=16
    )
    if not os.getenv("SECRET_KEY"):
        warnings.warn(
            "SECRET_KEY not set in environment; using instance/.secret_key. "
            "For production, set SECRET_KEY in .env or environment variables.",
            UserWarning,
            stacklevel=1,
        )
    if not os.getenv("SECURITY_PASSWORD_SALT"):
        warnings.warn(
            "SECURITY_PASSWORD_SALT not set in environment; using instance/.password_salt. "
            "If login suddenly fails after an upgrade, run: "
            "python misc/scripts/reset_password.py <email> <new-password>",
            UserWarning,
            stacklevel=1,
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
        from backend.utils.meal_nutrition import meal_calories, meal_protein_g, meal_fiber_g
        from backend.utils.password_policy import PASSWORD_POLICY_REQUIREMENTS
        return dict(
            get_time_period_display=get_time_period_display,
            meal_calories=meal_calories,
            meal_protein_g=meal_protein_g,
            meal_fiber_g=meal_fiber_g,
            password_policy_requirements=PASSWORD_POLICY_REQUIREMENTS,
        )

    with app.app_context():
        db.create_all()
        from backend.utils.schema_migrations import ensure_schema_updates
        ensure_schema_updates(
            app.config['SQLALCHEMY_DATABASE_URI'],
            app.instance_path,
        )
        _ensure_users_confirmed()
        ensure_bootstrap_users()

        # Ensure standard apes exist when app starts
        ensure_standard_apes()
        
        # Ensure food categories (and staff custom names with FDC data when CSVs present)
        ensure_standard_food_data()
        ensure_custom_display_foods()

    return app


def ensure_bootstrap_users():
    """Create default roles/admin on fresh deploys; promote first user if no admin exists."""
    from backend.models.entry import User, Role

    roles_to_create = [
        ('Admin', 'Administrator with full access to all features'),
        ('Researcher', 'Can view and log feeding data for all apes'),
        ('Viewer', 'Can view data but cannot log feeding sessions'),
    ]
    created_roles = False
    for role_name, description in roles_to_create:
        if not Role.query.filter_by(name=role_name).first():
            db.session.add(Role(name=role_name, description=description))
            created_roles = True
    if created_roles:
        db.session.commit()

    admin_role = Role.query.filter_by(name='Admin').first()
    if not admin_role:
        return

    users = User.query.order_by(User.id).all()
    if not users:
        admin_user = User(
            email='admin@apeinitiative.org',
            password=hash_password('admin123'),
            active=True,
            confirmed_at=datetime.utcnow(),
            fs_uniquifier=str(uuid.uuid4()),
        )
        admin_user.roles.append(admin_role)
        db.session.add(admin_user)
        db.session.commit()
        print('[SUCCESS] Bootstrap admin created: admin@apeinitiative.org / admin123')
        return

    if not any(admin_role in user.roles for user in users):
        users[0].roles.append(admin_role)
        db.session.commit()
        print(f'[SUCCESS] Promoted {users[0].email} to Admin (no admin user existed)')


def _ensure_users_confirmed():
    """Backfill confirmed_at for accounts created before auto-confirm was enforced."""
    from datetime import datetime
    from backend.models.entry import User

    changed = False
    for user in User.query.filter(User.confirmed_at.is_(None)).all():
        user.confirmed_at = datetime.utcnow()
        user.active = True
        changed = True
    if changed:
        db.session.commit()


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


_RETIRED_STAFF_FOODS = {
    "Trash Lettuce": "Brussels sprouts, raw",
    "Cheese Toothpaste": "Cream cheese, full fat, block",
}


def _apply_fdc_record_to_recipe(recipe, record, categories) -> None:
    cat = categories.get(record.app_category)
    recipe.meal_name = record.meal_name
    recipe.description = record.description
    recipe.calories = record.calories
    recipe.protein_g = record.protein_g
    recipe.fiber_g = record.fiber_g
    recipe.quantity = record.quantity
    recipe.unit_of_measurement = record.unit_of_measurement
    recipe.source = record.source
    recipe.fdc_id = record.fdc_id
    recipe.food_category = record.app_category
    if hasattr(record, "gram_weight"):
        recipe.gram_weight = record.gram_weight
    if cat:
        recipe.category_id = cat.id


def ensure_custom_display_foods():
    """Optional staff names from custom_foods.json; restore USDA labels for retired nicknames."""
    from backend.models.entry import FoodCategory, Meals, Recipe

    custom_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "fdc", "custom_foods.json"
    )
    raw_ff = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "fdc", "raw", "foundation_food.csv"
    )
    if not os.path.isfile(raw_ff):
        return

    custom = {}
    if os.path.isfile(custom_path):
        try:
            with open(custom_path, encoding="utf-8") as f:
                custom = json.load(f).get("custom_display_names", {})
        except (OSError, json.JSONDecodeError):
            custom = {}

    try:
        from backend.utils.fdc_loader import FdcFoundationLoader, _normalize_desc, load_category_map

        loader = FdcFoundationLoader()
        category_map = load_category_map()
        categories = {c.name: c for c in FoodCategory.query.filter_by(is_active=True).all()}
        changed = False

        fdc_by_desc = {}
        for record in loader.iter_records(category_map, include_excluded_categories=True):
            fdc_by_desc[_normalize_desc(record.description)] = record

        def _remove_recipe(recipe: Recipe) -> None:
            nonlocal changed
            Meals.query.filter_by(recipe_id=recipe.id).delete(synchronize_session=False)
            db.session.delete(recipe)
            changed = True

        for staff_name, fdc_desc in _RETIRED_STAFF_FOODS.items():
            if staff_name in custom:
                continue
            record = fdc_by_desc.get(_normalize_desc(fdc_desc))
            if not record:
                continue
            staff_recipe = Recipe.query.filter_by(meal_name=staff_name).first()
            usda_recipe = Recipe.query.filter_by(fdc_id=record.fdc_id).first()
            if staff_recipe and usda_recipe and staff_recipe.id != usda_recipe.id:
                Meals.query.filter_by(recipe_id=staff_recipe.id).update(
                    {"recipe_id": usda_recipe.id},
                    synchronize_session=False,
                )
                _remove_recipe(staff_recipe)
                _apply_fdc_record_to_recipe(usda_recipe, record, categories)
            elif staff_recipe:
                _apply_fdc_record_to_recipe(staff_recipe, record, categories)
                changed = True
            elif not usda_recipe:
                cat = categories.get(record.app_category)
                recipe = Recipe(
                    meal_name=record.meal_name,
                    description=record.description,
                    calories=record.calories,
                    quantity=record.quantity,
                    unit_of_measurement=record.unit_of_measurement,
                    food_category=record.app_category,
                    protein_g=record.protein_g,
                    fiber_g=record.fiber_g,
                    source=record.source,
                    fdc_id=record.fdc_id,
                    category_id=cat.id if cat else None,
                )
                if hasattr(record, "gram_weight"):
                    recipe.gram_weight = record.gram_weight
                db.session.add(recipe)
                changed = True

        if not custom:
            if changed:
                db.session.commit()
            return

        targets = {_normalize_desc(m["fdc_description"]): (name, m) for name, m in custom.items()}
        records = {}
        for record in loader.iter_records(category_map, include_excluded_categories=True):
            key = _normalize_desc(record.description)
            if key in targets:
                records[targets[key][0]] = record

        for meal_name, meta in custom.items():
            record = records.get(meal_name)
            if not record:
                continue
            desc = meta.get("description", "")
            fdc_desc_norm = _normalize_desc(meta["fdc_description"])
            for other in Recipe.query.filter(Recipe.meal_name != meal_name).all():
                if other.fdc_id == record.fdc_id:
                    _remove_recipe(other)
                elif _normalize_desc(other.meal_name) == fdc_desc_norm:
                    _remove_recipe(other)
            recipe = Recipe.query.filter_by(meal_name=meal_name).first()
            cat = categories.get(meta["food_category"])
            if not recipe:
                recipe = Recipe(
                    meal_name=meal_name,
                    description=desc,
                    calories=record.calories,
                    quantity=record.quantity,
                    unit_of_measurement=record.unit_of_measurement,
                    food_category=meta["food_category"],
                    protein_g=record.protein_g,
                    fiber_g=record.fiber_g,
                    source=record.source,
                    fdc_id=record.fdc_id,
                    category_id=cat.id if cat else None,
                )
                if hasattr(record, "gram_weight"):
                    recipe.gram_weight = record.gram_weight
                db.session.add(recipe)
                changed = True
            else:
                if recipe.fdc_id != record.fdc_id or recipe.calories != record.calories:
                    recipe.calories = record.calories
                    recipe.protein_g = record.protein_g
                    recipe.fiber_g = record.fiber_g
                    recipe.quantity = record.quantity
                    recipe.unit_of_measurement = record.unit_of_measurement
                    recipe.source = record.source
                    recipe.fdc_id = record.fdc_id
                    changed = True
                if recipe.description != desc:
                    recipe.description = desc
                    changed = True
                if recipe.food_category != meta["food_category"]:
                    recipe.food_category = meta["food_category"]
                    changed = True
                if cat and recipe.category_id != cat.id:
                    recipe.category_id = cat.id
                    changed = True

        if changed:
            db.session.commit()
    except FileNotFoundError:
        pass
