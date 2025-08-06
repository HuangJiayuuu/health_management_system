# Health Management System - User Documentation and Critical Functions

This document provides a comprehensive overview of the user-related functionality and critical functions implemented in the Health Management System application.

## User Model Structure

The User model is the core component of the application, handling authentication, profile information, and relationships with other data models.

### User Fields

#### Authentication Fields
- **id**: Primary key for user identification
- **username**: Unique username for login (required)
- **email**: Unique email address (required)
- **password_hash**: Securely stored password hash (not the actual password)

#### Profile Fields
- **gender**: User's gender (optional)
- **age**: User's age (optional)
- **height**: User's height in centimeters (optional)
- **weight**: User's weight in kilograms (optional)
- **bmi**: Body Mass Index calculated from height and weight (optional)

### User Relationships

The User model maintains relationships with several other models:

- **Goal**: One-to-one relationship for tracking health goals
- **SleepRecord**: One-to-many relationship for tracking sleep patterns
- **ExerciseRecord**: One-to-many relationship for tracking exercise activities
- **DietRecord**: One-to-many relationship for tracking diet and nutrition
- **FriendRequest**: Relationships for sent and received friend requests
- **Friendship**: Relationship for managing friendships between users

## User Authentication and Registration

### Registration Process
1. Users register by providing a unique username, email address, and password
2. The system validates that the username and email are not already in use
3. The password is securely hashed before storage (never stored in plain text)
4. A new user account is created in the database

### Login Process
1. Users log in with their username and password
2. The system verifies the credentials by comparing the password hash
3. Upon successful authentication, a user session is created
4. The "remember me" option allows for persistent sessions

### Security Features
- Password hashing using Werkzeug's security functions
- User session management with Flask-Login
- Form validation to prevent common security issues

## User Profile Management

Users can manage their profile information through the profile page:

1. Edit basic information (username, gender, age, height, weight)
2. BMI is automatically calculated when height and weight are provided
3. Profile information is used to personalize health recommendations

## Health Tracking Features

### Goal Setting
Users can set various health goals:
- Sleep goals (target hours per day)
- Exercise goals (by duration, frequency, or calories)
- Diet goals (target calorie intake)

### Sleep Tracking
- Record sleep time and wake-up time
- View sleep duration statistics
- Track progress against sleep goals

### Exercise Tracking
- Log different types of exercises (running, swimming, yoga, cycling)
- Record duration and calculate calories burned
- Monitor progress against exercise goals

### Diet Tracking
- Log food intake with portion sizes
- Calculate calorie consumption
- Track meals (breakfast, lunch, dinner, snacks)
- Monitor progress against calorie intake goals

### Health Reports
- View comprehensive reports of health data
- Visualize trends in sleep, exercise, and diet
- Compare actual performance against goals
- Access advanced data analysis features:
  - Sleep quality prediction using linear regression
  - Correlation analysis between exercise duration and sleep quality
  - Visual representations of data trends and predictions

## Social Features

### Friend Management
- Search for other users by username
- Send friend requests
- Accept or reject incoming friend requests
- View a list of current friends

### Friend Interaction
- View friends' profiles
- See friends' health statistics (if shared)
- Compare progress with friends

## Critical Functions Implementation

### Password Security
```python
def set_password(self, password):
    self.password_hash = generate_password_hash(password)

def check_password(self, password):
    return check_password_hash(self.password_hash, password)
```
These methods ensure passwords are never stored in plain text and are securely verified.

### User Authentication
```python
@login.user_loader
def load_user(id):
    return User.query.get(int(id))
```
This function loads a user from the database based on the ID stored in the session.

### BMI Calculation
BMI is calculated automatically when a user updates their height and weight, providing an important health metric.

### Data Visualization
The application generates visualizations of health data to help users understand trends and patterns in their health metrics.

### Friend Request System
The application implements a comprehensive friend request system with proper status tracking (pending, accepted, rejected) to manage user connections.

## Security Considerations

1. **Password Security**: Passwords are hashed using Werkzeug's security functions, never stored in plain text
2. **Form Validation**: All forms include validation to prevent common security issues
3. **Authentication Required**: Sensitive routes are protected with the `@login_required` decorator
4. **CSRF Protection**: Forms are protected against Cross-Site Request Forgery attacks
5. **User Data Privacy**: Users can only access their own data or data shared by friends

## Conclusion

The Health Management System provides a comprehensive set of features for users to track and improve their health. The application's architecture ensures security, privacy, and a seamless user experience while managing health data.
