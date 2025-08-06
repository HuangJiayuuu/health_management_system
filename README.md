# Health Management System

This is a Flask-based web application for health management, allowing users to track diet, exercise, sleep, and set health goals.

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd health_management_system
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required dependencies:
   ```
   pip install flask flask-sqlalchemy flask-migrate flask-login
   ```

## Database Setup

1. Initialize the database:
   ```
   flask db init
   ```

2. Apply the migrations:
   ```
   flask db upgrade
   ```

   Alternatively, you can run the provided initialization script:
   ```
   python init_db.py
   ```

   Note: If you encounter a "no such table: user" error during registration, it means the database tables haven't been created. Run the above command to apply all migrations and create the necessary tables.

## Running the Application

1. Run the application:
   ```
   python run.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Features

- User registration and authentication
- Track diet and nutrition
- Log exercise activities
- Monitor sleep patterns
- Set and track health goals
- Connect with friends
- Multi-dimensional data analysis and prediction:
  - Linear regression to predict changes in sleep quality
  - Correlation analysis between exercise duration and sleep quality

## Project Structure

- `app/` - Main application package
  - `__init__.py` - Application initialization
  - `models.py` - Database models
  - `routes.py` - Application routes
  - `forms.py` - Form definitions
  - `analysis.py` - Data analysis and prediction functions
  - `templates/` - HTML templates
- `migrations/` - Database migration files
- `run.py` - Application entry point
