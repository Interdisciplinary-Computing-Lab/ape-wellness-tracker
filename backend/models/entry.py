from backend.extensions import db
import sqlalchemy as sa
from flask_security import UserMixin, RoleMixin
from datetime import datetime, date
from flask import url_for
import uuid

# Feeding period constants - loaded from config (with fallback defaults)
# Loaded lazily to avoid circular import issues
FEEDING_PERIODS_DEFAULT = {
    'morning': 'Morning (6 AM - 12 PM)',
    'afternoon': 'Afternoon (12 PM - 6 PM)', 
    'evening': 'Evening (6 PM - 12 AM)',
}

def get_feeding_periods():
    """Get feeding periods from config file, with fallback to defaults"""
    try:
        from backend.utils.config_loader import get_feeding_periods as _get_feeding_periods
        return _get_feeding_periods()
    except (ImportError, AttributeError):
        return FEEDING_PERIODS_DEFAULT

FEEDING_PERIODS = get_feeding_periods()

# Static asset used when an ape has no uploaded profile photo
DEFAULT_APE_IMAGE = 'images/ape-default.png'


class Apes(db.Model):
    """
    Represents an ape in the wellness tracker.
    Fields:
        id (int): Primary key.
        ape_name (str): Unique name of the ape.
        birthday (date): Birthday of the ape.
        weight (float): Current weight in kg (UI displays lb).
        image_filename (str): Filename of the image (for backward compatibility).
        image_data (bytes): BLOB data of the actual image.
        image_mime_type (str): MIME type of the image (e.g., 'image/jpeg').
        is_archived (bool): Whether the ape is archived (default: False).
        archived_at (datetime): When the ape was archived (None if not archived).
    """
    __tablename__ = 'apes'
    id = db.Column(db.Integer, primary_key=True)
    ape_name = db.Column(db.String(90), unique=True, nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    weight = db.Column(db.Float, nullable=True)  # stored in kg; UI uses lb
    mother = db.Column(db.String(90), nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)  # For backward compatibility
    image_data = db.Column(db.LargeBinary, nullable=True)  # BLOB for image data
    image_mime_type = db.Column(db.String(100), nullable=True)  # MIME type of image
    is_archived = db.Column(db.Boolean, default=False, nullable=False)  # Archive status
    archived_at = db.Column(db.DateTime, nullable=True)  # When the ape was archived
    
    @property
    def age(self):
        """Calculate age based on birthday"""
        today = date.today()
        age = today.year - self.birthday.year
        if today < date(today.year, self.birthday.month, self.birthday.day):
            age -= 1
        return age
    
    @property
    def is_birthday_today(self):
        """Check if today is the ape's birthday"""
        today = date.today()
        return today.month == self.birthday.month and today.day == self.birthday.day
    
    @property
    def days_until_birthday(self):
        """Calculate days until next birthday"""
        today = date.today()
        next_birthday = date(today.year, self.birthday.month, self.birthday.day)
        
        if next_birthday < today:
            next_birthday = date(today.year + 1, self.birthday.month, self.birthday.day)
        
        return (next_birthday - today).days
    
    def has_image(self):
        """Check if the ape has an uploaded image"""
        return self.image_data is not None
    
    def get_image_url(self):
        """Get the URL for the ape's profile image (uploaded or default avatar)."""
        if self.has_image():
            return url_for('site.ape_image', ape_id=self.id)
        if self.image_filename:
            return url_for('static', filename='images/' + self.image_filename)
        return url_for('static', filename=DEFAULT_APE_IMAGE)

    def profile_photo_class(self):
        """CSS classes for profile images (default avatar gets centered icon styling)."""
        if self.has_image() or self.image_filename:
            return 'ape-profile-photo'
        return 'ape-profile-photo ape-profile-photo--default'

class FoodCategory(db.Model):
    """
    Represents a food category in the wellness tracker.
    Fields:
        id (int): Primary key.
        name (str): Unique name of the category.
        description (str): Description of the category.
        icon (str): FontAwesome icon class for the category.
        color (str): Bootstrap color class for the category.
        is_active (bool): Whether the category is active.
        sort_order (int): Order for displaying categories.
    """
    __tablename__ = 'food_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    icon = db.Column(db.String(50), nullable=True, default='fas fa-tag')
    color = db.Column(db.String(20), nullable=True, default='badge-secondary')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=sa.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=sa.func.now(), onupdate=sa.func.now(), nullable=False)

    # Relationships
    recipes = db.relationship('Recipe', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<FoodCategory {self.name}>'

class Recipe(db.Model):
    """
    Represents a recipe or meal option in the wellness tracker.
    Fields:
        id (int): Primary key.
        meal_name (str): Unique name of the meal.
        description (str): Description of the meal.
        calories (int): Calorie count (must be non-negative).
        quantity (float): Base quantity for which calories are calculated (default: 1.0).
        unit_of_measurement (str): Unit indicating what quantity=1 means (e.g., "1 cup", "1 piece", "100g").
        source (str): Data source for the nutritional information (e.g., "USDA Foundation Foods").
        fdc_id (str): USDA FoodData Central ID when sourced from Foundation Foods CSV.
        food_category (str): Category of food (fruits, vegetables, protein, etc.).
        category_id (int): Foreign key to FoodCategory.
        protein_g (float): Protein content in grams (default: 2.0).
        fiber_g (float): Fiber content in grams (default: 1.0).
        gram_weight (float): Gram weight of one catalog serving (FDC portion); enables g/oz conversions.
        is_favorite (bool): Whether staff marked this food as a favorite for quick access.
    """
    __tablename__ = 'recipe'
    id = db.Column(db.Integer, primary_key=True)
    meal_name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String)
    calories = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1.0)
    unit_of_measurement = db.Column(db.String(50), nullable=True)
    source = db.Column(db.String(200), nullable=True)
    fdc_id = db.Column(db.String(20), unique=True, nullable=True, index=True)
    food_category = db.Column(db.String(50), nullable=True, default='Other')  # Legacy field for backward compatibility
    category_id = db.Column(db.Integer, sa.ForeignKey('food_categories.id'), nullable=True)
    protein_g = db.Column(db.Float, nullable=True, default=2.0)  # Protein in grams
    fiber_g = db.Column(db.Float, nullable=True, default=1.0)  # Fiber in grams
    gram_weight = db.Column(db.Float, nullable=True)  # FDC portion weight in grams
    is_favorite = db.Column(db.Boolean, default=False, nullable=False)

    # Example constraint: calories must be >=0
    __table_args__ = (
        sa.CheckConstraint('calories >= 0', name='check_calories_non_negative'),
    )

    @property
    def is_custom_food(self):
        """True for staff custom/quick-add foods (not kitchen cheat sheet or USDA)."""
        if self.fdc_id:
            return False
        source = (self.source or '').strip()
        if source == 'Kitchen cheat sheet':
            return False
        return True

    
    def format_quantity(self):
        """
        Format quantity to avoid displaying too many decimal places.
        Returns a string representation of the quantity with appropriate precision.
        """
        if self.quantity is None:
            return "1"
        # If it's a whole number, display without decimals
        if self.quantity == int(self.quantity):
            return str(int(self.quantity))
        # Otherwise, display with up to 2 decimal places, removing trailing zeros
        formatted = f"{self.quantity:.2f}".rstrip('0').rstrip('.')
        return formatted

    def catalog_serving_label(self):
        """Label for one catalog serving shown on food cards (e.g. '1 cup', '1 whole', '100 g')."""
        import re
        unit_raw = (self.unit_of_measurement or '').strip()
        if not unit_raw:
            return '1 serving'

        qty = self.quantity if self.quantity is not None else 1.0
        unit_part = unit_raw

        leading = re.match(r'^(\d+(?:\.\d+)?)\s+(.+)$', unit_raw)
        if leading:
            embedded = float(leading.group(1))
            unit_part = leading.group(2).strip()
            if qty in (None, 1, 1.0):
                qty = embedded

        normalized = unit_part.lower().replace(' ', '')
        if normalized in ('100g',) or (
            normalized in ('g', 'gram', 'grams') and qty >= 100
        ):
            return '100 g'

        if qty == int(qty):
            qty_str = str(int(qty))
        else:
            qty_str = f'{qty:.2f}'.rstrip('0').rstrip('.')
        return f'{qty_str} {unit_part}'

class Meals(db.Model):
    """
    Represents a meal entry for an ape, linking an ape to a recipe on a specific date.
    Fields:
        id (int): Primary key.
        ape_id (int): Foreign key to Apes.
        recipe_id (int): Foreign key to Recipe.
        date (datetime): Date and time of the meal (feeding date / period).
        logged_at (datetime): When this entry was saved in the app.
        feeding_period (str): Time period when feeding occurred (morning, afternoon, evening).
        meal_type (str): Meal type (Forage, Enrichment, Reward, Other); defaults from period.
        calories_logged (int): Actual calories for this feeding (scaled portion); null uses recipe.calories.
        user_id (int): Foreign key to User - tracks who entered the data.
    Relationships:
        ape: The associated Apes object.
        recipe: The associated Recipe object.
        user: The associated User object who entered the data.
    """
    __tablename__ = 'meals'
    id = db.Column(db.Integer, primary_key=True)
    ape_id = db.Column(db.Integer, sa.ForeignKey('apes.id'), nullable=False)
    recipe_id = db.Column(db.Integer, sa.ForeignKey('recipe.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=sa.func.now())
    logged_at = db.Column(db.DateTime, nullable=False, default=sa.func.now())
    feeding_period = db.Column(db.String(20), nullable=True)  # morning, afternoon, evening
    meal_type = db.Column(db.String(20), nullable=True)  # Forage, Enrichment, Reward, Other
    calories_logged = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, sa.ForeignKey('user.id'), nullable=False)

    # Relationships
    ape = db.relationship('Apes', backref='meals')
    recipe = db.relationship('Recipe', backref='meals')
    user = db.relationship('User', backref='meals')

    @property
    def resolved_meal_type(self):
        """Meal type for this meal (stored or derived from the feeding period)."""
        from backend.utils.meal_types import normalize_meal_type

        stored = (self.meal_type or '').strip()
        if stored:
            return normalize_meal_type(stored)
        period = self.feeding_period or ''
        if period == 'night':
            period = 'evening'
        try:
            from backend.utils.config_loader import get_meal_type_for_period
            return get_meal_type_for_period(period)
        except Exception:
            return 'Forage'
    
    @property
    def feeding_period_display(self):
        """Get the display name for the feeding period (with meal type)."""
        period = self.feeding_period or ''
        if period == 'night':
            period = 'evening'
        if not period:
            return "Not specified"
        periods = get_feeding_periods()
        time_label = periods.get(period, period)
        return f"{self.resolved_meal_type} — {time_label}"


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)

class Role(db.Model, RoleMixin):
    """
    Represents a user role for authentication and authorization.
    Fields:
        id (int): Primary key.
        name (str): Unique name of the role.
        description (str): Description of the role.
    """
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    """
    Represents a user of the wellness tracker application.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True)
    confirmed_at = db.Column(db.DateTime)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)
    
    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic')
    )