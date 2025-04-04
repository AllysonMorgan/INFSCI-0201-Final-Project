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

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Routes
@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('userlogin'))

    if session.get('is_manager'):
        return redirect(url_for('manager_dashboard'))
    events=Event.query.all()

    return render_template('landing.html',events=events)

@app.route('/manager_dashboard')
def manager_dashboard():
    if not session.get('is_manager'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    manager = User.query.filter_by(username=session['username']).first()
    events = Event.query.filter_by(manager_id=manager.id).all()
    return render_template('manager_landing.html', manager_events=events)

@app.route('/userlogin', methods=['GET', 'POST'])
def userlogin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            if user.role == 'manager':
                flash('Managers cannot log in here. Please use the manager login.', 'warning')
                return redirect(url_for('userlogin'))
            
            if user.check_password(password):
                session['username'] = username
                session['is_manager'] = False  
                
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
            return redirect(url_for('userlogin'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('userlogin'))

@app.route('/create_event', methods=['POST'])
def create_event():
    if not session.get('is_manager'):
        flash('Unauthorized', 'danger')
        return redirect(url_for('home'))

    title = request.form['title']
    description = request.form['description']
    date = request.form['date']
    time = request.form['time']
    location = request.form['location']

    manager = User.query.filter_by(username=session['username']).first()
    new_event = Event(
        title=title,
        description=description,
        date=date,
        time=time,
        location=location,
        manager_id=manager.id
    )
    db.session.add(new_event)
    db.session.commit()
    flash('Event created successfully!', 'success')
    return redirect(url_for('manager_dashboard'))

@app.route('/usersettings', methods=['GET', 'POST'])
def usersettings():
    return render_template("usersettings.html")

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    if 'username' not in session or not session.get('is_manager'):
        flash('Only managers can edit events.', 'danger')
        return redirect(url_for('home'))

    event = Event.query.get_or_404(event_id)

    if request.method == 'POST':
        event.title = request.form.get('title')
        event.description = request.form.get('description')
        event.datetime = request.form.get('datetime')
        event.location = request.form.get('location')
        
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('edit_event.html', event=event)

@app.route('/delete_event/<int:event_id>', methods=['POST', 'GET'])
def delete_event(event_id):
    if 'username' not in session or not session.get('is_manager'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('manager_dashboard'))

# Initialize database and create test users
def initialize_database():
    db_file = 'events.db'
    if not os.path.exists(db_file):
        with app.app_context():
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
    else:
        print("Database already exists. No need to initialize.")

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)