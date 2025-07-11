from backend.extensions import db
import sqlalchemy as sa

class Apes(db.Model):
    __tablename__ = 'apes'
    id = db.Column(db.Integer, primary_key=True)
    ape_name = db.Column(db.String(90), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False)

class Recipe(db.Model):
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
    __tablename__ = 'meals'
    id = db.Column(db.Integer, primary_key=True)
    ape_id = db.Column(db.Integer, sa.ForeignKey('apes.id'), nullable=False)
    recipe_id = db.Column(db.Integer, sa.ForeignKey('recipe.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=sa.func.now())

    # Relationships
    ape = db.relationship('Apes', backref='meals')
    recipe = db.relationship('Recipe', backref='meals')
