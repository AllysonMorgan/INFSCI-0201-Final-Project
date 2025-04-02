from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secure-key-123'  # Change this for production!
app.permanent_session_lifetime = timedelta(days=30)  # Session expiration

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' or 'manager'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Routes
@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('userlogin'))

    if session.get('is_manager'):
        return render_template('manager_landing.html')
    return render_template('landing.html')

@app.route('/userlogin', methods=['GET', 'POST'])
def userlogin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['username'] = username
            session['is_manager'] = (user.role == 'manager')
            
            if remember:
                session.permanent = True
            
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        flash('Invalid username or password', 'danger')
    return render_template('userlogin.html')

@app.route('/managerlogin', methods=['GET', 'POST'])
def managerlogin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        # Only allow manager role to login
        user = User.query.filter_by(username=username, role='manager').first()
        
        if user and user.check_password(password):
            session['username'] = username
            session['is_manager'] = True
            
            if remember:
                session.permanent = True
            
            flash('Manager login successful!', 'success')
            return redirect(url_for('home'))
        flash('Invalid manager credentials', 'danger')
    return render_template('managerlogin.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_manager = request.form.get('is_manager') == 'on'
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        try:
            new_user = User(
                username=username,
                email=f"{username}@example.com",
                role='manager' if is_manager else 'user'
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('userlogin'))

# Initialize database and create test users
def initialize_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Create test users if none exist
        if not User.query.first():
            test_users = [
                {'username': 'user', 'email': 'user@example.com', 'role': 'user', 'password': 'user123'},
                {'username': 'manager', 'email': 'manager@example.com', 'role': 'manager', 'password': 'manager123'}
            ]
            
            for user_data in test_users:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    role=user_data['role']
                )
                user.set_password(user_data['password'])
                db.session.add(user)
            
            db.session.commit()
            print("Created test users:")
            print("- Regular: user/user123")
            print("- Manager: manager/manager123")

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)