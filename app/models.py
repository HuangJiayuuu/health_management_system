from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    # New profile fields
    gender = db.Column(db.String(10), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Float, nullable=True) # in cm
    weight = db.Column(db.Float, nullable=True) # in kg
    bmi = db.Column(db.Float, nullable=True)

    goal = db.relationship('Goal', backref='user', uselist=False) # One-to-one relationship

    sleep_records = db.relationship('SleepRecord', backref='author', lazy='dynamic')
    exercise_records = db.relationship('ExerciseRecord', backref='author', lazy='dynamic')
    diet_records = db.relationship('DietRecord', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class SleepRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sleep_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    wakeup_time = db.Column(db.DateTime, index=True)
    duration = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<SleepRecord {self.sleep_time} to {self.wakeup_time}>'

class ExerciseRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise_type = db.Column(db.String(140))
    duration = db.Column(db.Float)
    calories_burned = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<ExerciseRecord {self.exercise_type}>'

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_sleep_hours = db.Column(db.Float, nullable=True)
    # target_exercise_minutes and target_calorie_intake will be moved
    target_calorie_intake = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Goal for user {self.user_id}>'

class ExerciseGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goal_type = db.Column(db.String(50), nullable=False) # e.g., 'duration', 'frequency', 'distance'
    
    # Target values
    target_value = db.Column(db.Float, nullable=False)
    
    # Optional fields for specific goal types
    exercise_type = db.Column(db.String(50)) # e.g., '跑步' for a frequency goal
    time_period = db.Column(db.String(20), default='weekly') # 'weekly' or 'monthly'

    user = db.relationship('User', backref=db.backref('exercise_goals', lazy='dynamic'))

    def __repr__(self):
        return f'<ExerciseGoal {self.goal_type} for user {self.user_id}>'

class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    calories_per_100g = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<FoodItem {self.name}>'

class DietRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(140))
    portion = db.Column(db.Float)
    calories = db.Column(db.Float)
    meal_type = db.Column(db.String(50)) # e.g., Breakfast, Lunch, Dinner
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<DietRecord {self.food_name}>'
