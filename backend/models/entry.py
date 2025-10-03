from backend.extensions import db
import sqlalchemy as sa
from flask_security import UserMixin, RoleMixin
from datetime import datetime, date
from flask import url_for
import uuid

class Apes(db.Model):
    """
    Represents an ape in the wellness tracker.
    Fields:
        id (int): Primary key.
        ape_name (str): Unique name of the ape.
        birthday (date): Birthday of the ape.
        weight (float): Current weight in kg.
        mother (str): Mother's name if known.
        image_filename (str): Filename of the image (for backward compatibility).
        image_data (bytes): BLOB data of the actual image.
        image_mime_type (str): MIME type of the image (e.g., 'image/jpeg').
    """
    __tablename__ = 'apes'
    id = db.Column(db.Integer, primary_key=True)
    ape_name = db.Column(db.String(90), unique=True, nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    weight = db.Column(db.Float, nullable=True)  # in kg
    mother = db.Column(db.String(90), nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)  # For backward compatibility
    image_data = db.Column(db.LargeBinary, nullable=True)  # BLOB for image data
    image_mime_type = db.Column(db.String(100), nullable=True)  # MIME type of image
    
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
        """Get the URL for the ape's image"""
        if self.has_image():
            return url_for('site.ape_image', ape_id=self.id)
        elif self.image_filename:
            return url_for('static', filename='images/' + self.image_filename)
        else:
            return url_for('static', filename='images/bonobo-placeholder.jpg')

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
        food_category (str): Category of food (fruits, vegetables, protein, etc.).
        category_id (int): Foreign key to FoodCategory.
    """
    __tablename__ = 'recipe'
    id = db.Column(db.Integer, primary_key=True)
    meal_name = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.String)
    calories = db.Column(db.Integer, nullable=False)
    food_category = db.Column(db.String(50), nullable=True, default='Other')  # Legacy field for backward compatibility
    category_id = db.Column(db.Integer, sa.ForeignKey('food_categories.id'), nullable=True)

    # Example constraint: calories must be >=0
    __table_args__ = (
        sa.CheckConstraint('calories >= 0', name='check_calories_non_negative'),
    )

class Meals(db.Model):
    """
    Represents a meal entry for an ape, linking an ape to a recipe on a specific date.
    Fields:
        id (int): Primary key.
        ape_id (int): Foreign key to Apes.
        recipe_id (int): Foreign key to Recipe.
        date (datetime): Date and time of the meal.
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
    user_id = db.Column(db.Integer, sa.ForeignKey('user.id'), nullable=False)

    # Relationships
    ape = db.relationship('Apes', backref='meals')
    recipe = db.relationship('Recipe', backref='meals')
    user = db.relationship('User', backref='meals')


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