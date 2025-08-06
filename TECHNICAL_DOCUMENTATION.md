# Health Management System - Technical Documentation

This document provides a technical overview of the Health Management System application, focusing on the architecture, database schema, and implementation details.

## Application Architecture

The Health Management System is built using the Flask web framework with a Model-View-Controller (MVC) architecture:

- **Models**: Defined in `app/models.py`, representing database tables and relationships
- **Views**: Implemented as Flask routes in `app/routes.py`
- **Templates**: HTML templates in `app/templates/` directory
- **Forms**: Form definitions in `app/forms.py` using Flask-WTF
- **Analysis**: Data analysis and prediction functions in `app/analysis.py`

## Database Schema

The application uses SQLAlchemy ORM with the following database models:

### User Model
```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    gender = db.Column(db.String(10), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Float, nullable=True) # in cm
    weight = db.Column(db.Float, nullable=True) # in kg
    bmi = db.Column(db.Float, nullable=True)
```

### Health Tracking Models

#### SleepRecord Model
```python
class SleepRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sleep_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    wakeup_time = db.Column(db.DateTime, index=True)
    duration = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
```

#### ExerciseRecord Model
```python
class ExerciseRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise_type = db.Column(db.String(140))
    duration = db.Column(db.Float)
    calories_burned = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
```

#### DietRecord Model
```python
class DietRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_name = db.Column(db.String(140))
    portion = db.Column(db.Float)
    calories = db.Column(db.Float)
    meal_type = db.Column(db.String(50)) # e.g., Breakfast, Lunch, Dinner
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
```

### Goal Models

#### Goal Model
```python
class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_sleep_hours = db.Column(db.Float, nullable=True)
    target_calorie_intake = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
```

#### ExerciseGoal Model
```python
class ExerciseGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    goal_type = db.Column(db.String(50), nullable=False) # e.g., 'duration', 'frequency', 'distance'
    target_value = db.Column(db.Float, nullable=False)
    exercise_type = db.Column(db.String(50)) # e.g., '跑步' for a frequency goal
    time_period = db.Column(db.String(20), default='weekly') # 'weekly' or 'monthly'
```

### Social Models

#### FriendRequest Model
```python
class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
```

#### Friendship Model
```python
class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend = db.relationship('User', foreign_keys=[friend_id])
```

## Key Components

### Authentication System

The application uses Flask-Login for user authentication:

```python
login = LoginManager(app)
login.login_view = 'login'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
```

User passwords are securely hashed using Werkzeug's security functions:

```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, password):
    self.password_hash = generate_password_hash(password)

def check_password(self, password):
    return check_password_hash(self.password_hash, password)
```

### Form Handling

Forms are defined using Flask-WTF and WTForms:

```python
class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired()])
    email = StringField('电子邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    password2 = PasswordField('重复密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')
```

Form validation includes custom validators to ensure data integrity:

```python
def validate_username(self, username):
    user = User.query.filter_by(username=username.data).first()
    if user is not None:
        raise ValidationError('用户名已被使用。')
```

### Route Implementation

Routes are implemented in `app/routes.py` and follow a consistent pattern:

1. Form validation
2. Database operations
3. Flash messages for user feedback
4. Redirects to appropriate pages

Example route:

```python
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)
```

### Data Visualization

The application uses Matplotlib to generate visualizations of health data:

```python
import matplotlib.pyplot as plt
import io
import base64

# Example of creating a visualization
plt.figure(figsize=(10, 4))
plt.plot(dates, sleep_durations, marker='o')
plt.title('Sleep Duration Over Time')
plt.xlabel('Date')
plt.ylabel('Hours')
plt.grid(True)
plt.tight_layout()

# Save plot to a buffer
buf = io.BytesIO()
plt.savefig(buf, format='png')
buf.seek(0)
plot_url = base64.b64encode(buf.getvalue()).decode('utf8')
```

### Data Analysis and Prediction

The application includes advanced data analysis and prediction capabilities implemented in `app/analysis.py`:

#### Sleep Quality Prediction

The application uses linear regression to predict future sleep quality based on historical sleep data:

```python
def generate_sleep_prediction(sleep_records, days_to_predict=7):
    # Extract data and sort by date
    data = [(record.sleep_time.date(), record.duration) for record in sleep_records]
    data.sort(key=lambda x: x[0])

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=['date', 'duration'])

    # Create feature (days since first record)
    first_date = df['date'].min()
    df['days_since_start'] = df['date'].apply(lambda x: (x - first_date).days)

    # Prepare data for linear regression
    X = df[['days_since_start']].values
    y = df['duration'].values

    # Create and train the model
    model = LinearRegression()
    model.fit(X, y)

    # Predict future values
    last_day = df['days_since_start'].max()
    future_days = np.array([[last_day + i + 1] for i in range(days_to_predict)])
    future_predictions = model.predict(future_days)

    # Generate visualization and return results
    # ...
```

#### Exercise-Sleep Correlation Analysis

The application analyzes the correlation between exercise duration and sleep quality:

```python
def analyze_exercise_sleep_correlation(exercise_records, sleep_records):
    # Create DataFrames
    exercise_df = pd.DataFrame([
        {'date': record.timestamp.date(), 'duration': record.duration}
        for record in exercise_records
    ])

    sleep_df = pd.DataFrame([
        {'date': record.sleep_time.date(), 'duration': record.duration}
        for record in sleep_records
    ])

    # Merge data on date
    merged_df = pd.merge(exercise_df, sleep_df, on='date', how='inner', suffixes=('_exercise', '_sleep'))

    # Calculate correlation
    correlation = merged_df['duration_exercise'].corr(merged_df['duration_sleep'])

    # Generate visualization and interpretation
    # ...
```

These analysis functions are integrated into the report route to provide users with insights about their health data:

```python
@app.route('/report')
@login_required
def report():
    # Get all sleep records for prediction
    all_sleep_records = current_user.sleep_records.all()

    # Generate sleep prediction
    sleep_prediction = generate_sleep_prediction(all_sleep_records)

    # Analyze correlation between exercise and sleep
    all_exercise_records = current_user.exercise_records.all()
    correlation_analysis = analyze_exercise_sleep_correlation(all_exercise_records, all_sleep_records)

    # Add analysis insights to advice list
    # ...
```

## Database Migrations

The application uses Flask-Migrate (based on Alembic) for database migrations:

```python
from flask_migrate import Migrate
migrate = Migrate(app, db)
```

Migration files are stored in the `migrations/` directory and track schema changes over time.

## Application Initialization

The application is initialized in `app/__init__.py`:

```python
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-secret-key-that-you-should-change'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
```

## Entry Point

The application entry point is `run.py`:

```python
from app import app

if __name__ == '__main__':
    app.run(debug=True)
```

## Security Considerations

1. **Password Hashing**: Passwords are hashed using Werkzeug's security functions
2. **CSRF Protection**: Flask-WTF provides CSRF protection for all forms
3. **Authentication**: Flask-Login manages user sessions and authentication
4. **Input Validation**: WTForms validators ensure proper input validation
5. **Database Security**: SQLAlchemy ORM helps prevent SQL injection attacks

## Conclusion

The Health Management System is built using modern web development practices and follows the Flask application structure. The use of SQLAlchemy ORM, Flask-Login, and Flask-WTF provides a solid foundation for a secure and maintainable application.
