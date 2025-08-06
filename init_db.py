from app import app, db
from flask_migrate import upgrade

# Create the application context
with app.app_context():
    # Apply all migrations
    upgrade()
    
    print("Database initialized successfully!")