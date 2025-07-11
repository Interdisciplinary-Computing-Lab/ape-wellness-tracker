from backend.extensions import db
import sqlalchemy as sa
from flask_security import UserMixin, RoleMixin

class Apes(db.Model):
    """
    Represents an ape in the wellness tracker.
    Fields:
        id (int): Primary key.
        ape_name (str): Unique name of the ape.
        age (int): Age of the ape.
    """
    __tablename__ = 'apes'
    id = db.Column(db.Integer, primary_key=True)
    ape_name = db.Column(db.String(90), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False)

class Recipe(db.Model):
    """
    Represents a recipe or meal option in the wellness tracker.
    Fields:
        id (int): Primary key.
        meal_name (str): Unique name of the meal.
        description (str): Description of the meal.
        calories (int): Calorie count (must be non-negative).
    """
    __tablename__ = 'recipe'
    id = db.Column(db.Integer, primary_key=True)
    meal_name = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.String)
    calories = db.Column(db.Integer, nullable=False)

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
    Relationships:
        ape: The associated Apes object.
        recipe: The associated Recipe object.
    """
    __tablename__ = 'meals'
    id = db.Column(db.Integer, primary_key=True)
    ape_id = db.Column(db.Integer, sa.ForeignKey('apes.id'), nullable=False)
    recipe_id = db.Column(db.Integer, sa.ForeignKey('recipe.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=sa.func.now())

    # Relationships
    ape = db.relationship('Apes', backref='meals')
    recipe = db.relationship('Recipe', backref='meals')


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
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    """
    Represents a user of the wellness tracker application.
    Fields:
        id (int): Primary key.
        email (str): Unique email address.
        password (str): Encrypted password.
        active (bool): Whether the user is active.
        confirmed_at (datetime): Timestamp of confirmation.
        roles: List of associated roles (many-to-many).
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)
    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic')
    )