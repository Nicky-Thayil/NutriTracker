from datetime import datetime, date
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)
    
    # User profile fields
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    height = db.Column(db.Float, nullable=True)  # in cm
    activity_level = db.Column(db.String(20), nullable=True)
    goal = db.Column(db.String(20), nullable=True)  # lose_weight, maintain, gain_weight
    daily_calorie_goal = db.Column(db.Integer, default=2000)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    food_logs = db.relationship('FoodLog', backref='user', lazy=True, cascade='all, delete-orphan')
    weight_entries = db.relationship('WeightEntry', backref='user', lazy=True, cascade='all, delete-orphan')

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

class Food(db.Model):
    __tablename__ = 'foods'
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(20), unique=True, nullable=True)
    name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(100), nullable=True)
    
    # Nutrition per 100g
    calories_per_100g = db.Column(db.Float, nullable=True)
    protein_per_100g = db.Column(db.Float, nullable=True)
    carbs_per_100g = db.Column(db.Float, nullable=True)
    fat_per_100g = db.Column(db.Float, nullable=True)
    fiber_per_100g = db.Column(db.Float, nullable=True)
    sugar_per_100g = db.Column(db.Float, nullable=True)
    sodium_per_100g = db.Column(db.Float, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    food_logs = db.relationship('FoodLog', backref='food', lazy=True)

class FoodLog(db.Model):
    __tablename__ = 'food_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    
    quantity = db.Column(db.Float, nullable=False, default=100)  # in grams
    meal_type = db.Column(db.String(20), nullable=False)  # breakfast, lunch, dinner, snack
    logged_at = db.Column(db.DateTime, default=datetime.now)
    log_date = db.Column(db.Date, default=date.today)
    
    # Calculated nutrition values based on quantity
    calories = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    fat = db.Column(db.Float, nullable=True)
    fiber = db.Column(db.Float, nullable=True)
    sugar = db.Column(db.Float, nullable=True)
    sodium = db.Column(db.Float, nullable=True)

class WeightEntry(db.Model):
    __tablename__ = 'weight_entries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    
    weight = db.Column(db.Float, nullable=False)  # in kg
    entry_date = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (UniqueConstraint('user_id', 'entry_date', name='uq_user_date_weight'),)
