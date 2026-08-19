import os
import json
import secrets
import uuid
import warnings
from datetime import datetime
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


def _env_flag(name, default=False):
    """Parse a boolean environment flag (1/true/yes/on)."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


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


def create_app(*, sync_fdc_catalog: bool = False, testing: bool = False, config_overrides=None):
    template_folder = os.path.join(os.path.dirname(__file__), 'templates')
    static_folder = os.path.join(os.path.dirname(__file__), 'static')

    app = Flask(
        __name__, 
        instance_relative_config=True,
        template_folder=template_folder,
        static_folder=static_folder,
        static_url_path='/static'
    )
    
    os.makedirs(app.instance_path, exist_ok=True)

    if config_overrides:
        app.config.update(config_overrides)
    testing = testing or bool(app.config.get("TESTING"))

    db_path = os.path.join(app.instance_path, 'database.db').replace('\\', '/')
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", f"sqlite:///{db_path}")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    if testing:
        app.config["TESTING"] = True
        if not app.config.get("SECRET_KEY"):
            app.config["SECRET_KEY"] = "test-secret-key"
        if not app.config.get("SECURITY_PASSWORD_SALT"):
            app.config["SECURITY_PASSWORD_SALT"] = "test-password-salt"
        app.config.setdefault("WTF_CSRF_ENABLED", False)
    else:
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
        app.config.setdefault("WTF_CSRF_ENABLED", True)

    app.config["SECURITY_PASSWORD_HASH"] = "bcrypt"
    app.config["SECURITY_REGISTERABLE"] = _env_flag("SECURITY_REGISTERABLE", default=False)
    app.config["SECURITY_SEND_REGISTER_EMAIL"] = False
    app.config["SECURITY_CONFIRMABLE"] = False
    app.config["WTF_CSRF_TIME_LIMIT"] = None

    db.init_app(app)
    init_security(app)

    app.register_blueprint(site)
    
    # Add helper functions to template context
    @app.context_processor
    def utility_processor():
        from backend.utils.authz import (
            can_create_foods,
            can_export_reports,
            can_log_meals,
            can_manage_apes,
            can_manage_catalog,
            is_admin,
        )
        from backend.utils.meal_nutrition import meal_calories, meal_protein_g, meal_fiber_g
        from backend.utils.password_policy import PASSWORD_POLICY_REQUIREMENTS
        from backend.utils.weight_units import kg_to_lb
        return dict(
            get_time_period_display=get_time_period_display,
            meal_calories=meal_calories,
            meal_protein_g=meal_protein_g,
            meal_fiber_g=meal_fiber_g,
            password_policy_requirements=PASSWORD_POLICY_REQUIREMENTS,
            kg_to_lb=kg_to_lb,
            can_log_meals=can_log_meals,
            can_manage_apes=can_manage_apes,
            can_manage_catalog=can_manage_catalog,
            can_create_foods=can_create_foods,
            can_export_reports=can_export_reports,
            is_admin=is_admin,
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
        _ensure_default_staff_roles()

        if not testing:
            ensure_standard_apes()
            ensure_standard_food_data()
            ensure_kitchen_foods()
            remove_fdc_foods()
            if sync_fdc_catalog:
                warnings.warn(
                    "sync_fdc_catalog=True is ignored; food catalog is kitchen cheat sheet only.",
                    UserWarning,
                    stacklevel=2,
                )

    return app


def ensure_bootstrap_users():
    """Create roles and an optional first admin from environment variables."""
    from backend.models.entry import User, Role
    from backend.utils.password_policy import validate_password

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
    if users:
        if not any(admin_role in user.roles for user in users):
            print(
                '[WARNING] No Admin user exists. Create one with: '
                'python misc/scripts/create_admin.py --email <email> --password <password>'
            )
        return

    bootstrap_password = os.getenv('BOOTSTRAP_ADMIN_PASSWORD')
    if not bootstrap_password:
        print(
            '[WARNING] No users exist. Set BOOTSTRAP_ADMIN_PASSWORD to create the '
            'initial admin, or run: python misc/scripts/create_admin.py --email '
            '<email> --password <password>'
        )
        return

    policy_errors = validate_password(bootstrap_password)
    if policy_errors:
        print(
            '[ERROR] BOOTSTRAP_ADMIN_PASSWORD does not meet the password policy: '
            + '; '.join(policy_errors)
        )
        return

    bootstrap_email = (
        os.getenv('BOOTSTRAP_ADMIN_EMAIL', 'admin@apeinitiative.org').strip()
        or 'admin@apeinitiative.org'
    )
    admin_user = User(
        email=bootstrap_email,
        password=hash_password(bootstrap_password),
        active=True,
        confirmed_at=datetime.utcnow(),
        fs_uniquifier=str(uuid.uuid4()),
    )
    admin_user.roles.append(admin_role)
    db.session.add(admin_user)
    db.session.commit()
    print(f'[SUCCESS] Bootstrap admin created: {bootstrap_email}')


def _ensure_default_staff_roles():
    """Give existing accounts Researcher if they were created without a role."""
    from backend.models.entry import User, Role

    researcher = Role.query.filter_by(name='Researcher').first()
    if not researcher:
        return

    changed = False
    for user in User.query.all():
        if not user.roles:
            user.roles.append(researcher)
            changed = True
    if changed:
        db.session.commit()


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
    """Ensure food categories exist in the database (recipes come from USDA FDC import)."""
    from backend.models.entry import FoodCategory
    
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


KITCHEN_CHEAT_SHEET_SOURCE = "Kitchen cheat sheet"


def _load_kitchen_foods_json():
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "kitchen_foods.json"
    )
    try:
        with open(data_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse kitchen foods data file: {e}. Skipping.")
        return []


def ensure_kitchen_foods():
    """Create missing kitchen foods without overwriting staff catalog edits."""
    from backend.models.entry import FoodCategory, Recipe
    from backend.helpers import sync_recipe_category

    foods = _load_kitchen_foods_json()
    if not foods:
        return

    categories = {c.name: c for c in FoodCategory.query.filter_by(is_active=True).all()}
    created_count = 0
    updated_count = 0

    for item in foods:
        meal_name = item["meal_name"]
        cat_name = item.get("food_category", "Other")
        cat = categories.get(cat_name)
        calories = int(round(float(item["calories"])))
        quantity = float(item.get("quantity", 1))
        unit = item.get("unit_of_measurement") or "serving"
        description = item.get("description", meal_name)
        source = item.get("source", KITCHEN_CHEAT_SHEET_SOURCE)

        existing = Recipe.query.filter_by(meal_name=meal_name).first()
        if existing:
            # One-time legacy conversion is still needed before remove_fdc_foods().
            # Once a row belongs to the app catalog, the database is authoritative.
            is_fdc = bool(existing.fdc_id) or (existing.source or '').startswith(
                "USDA Foundation Foods"
            )
            if is_fdc:
                existing.calories = calories
                existing.quantity = quantity
                existing.unit_of_measurement = unit
                existing.description = description
                existing.source = source
                existing.fdc_id = None
                existing.gram_weight = None
                if hasattr(existing, "is_favorite") and existing.is_favorite is None:
                    existing.is_favorite = False
                sync_recipe_category(existing, cat_name)
                updated_count += 1
            continue

        recipe = Recipe(
            meal_name=meal_name,
            description=description,
            calories=calories,
            quantity=quantity,
            unit_of_measurement=unit,
            food_category=cat_name,
            source=source,
            fdc_id=None,
            gram_weight=None,
            category_id=cat.id if cat else None,
        )
        db.session.add(recipe)
        created_count += 1

    if created_count or updated_count:
        db.session.commit()
        print(
            f"[SUCCESS] Kitchen cheat sheet: {created_count} created, "
            f"{updated_count} updated"
        )


def remove_fdc_foods():
    """Delete all USDA FDC catalog foods (and their meal log rows)."""
    from backend.models.entry import Meals, Recipe
    from sqlalchemy import or_

    fdc_recipes = Recipe.query.filter(
        or_(
            Recipe.fdc_id.isnot(None),
            Recipe.source.like("USDA Foundation Foods%"),
        )
    ).all()

    if not fdc_recipes:
        return 0

    removed = 0
    for recipe in fdc_recipes:
        Meals.query.filter_by(recipe_id=recipe.id).delete(synchronize_session=False)
        db.session.delete(recipe)
        removed += 1

    db.session.commit()
    print(f"[SUCCESS] Removed {removed} USDA FDC food(s); catalog is kitchen cheat sheet only")
    return removed
