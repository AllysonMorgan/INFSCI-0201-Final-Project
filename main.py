from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta, datetime
import os
from sqlalchemy import func, select, and_
from flask_migrate import Migrate

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)
app.permanent_session_lifetime = timedelta(days=30)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'instance/events.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Association Table
registrations = db.Table('registrations',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'), primary_key=True),
    db.Column('num_attendees', db.Integer, default=1, nullable=False),
    db.Column('registration_date', db.DateTime, default=datetime.utcnow)
)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    registered_events = db.relationship(
        'Event',
        secondary=registrations,
        backref=db.backref('attendees', lazy='dynamic')
    )
    managed_events = db.relationship('Event', backref='manager', foreign_keys='Event.manager_id')

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
    event_type = db.Column(db.String(20), nullable=False, default='other')  # New field
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def total_attendees(self):
        total = db.session.scalar(
            select(func.sum(registrations.c.num_attendees))
            .where(registrations.c.event_id == self.id)
        )
        return total if total else 0
    
    @property
    def total_attendees(self):
        total = db.session.scalar(
            select(func.sum(registrations.c.num_attendees))
            .where(registrations.c.event_id == self.id)
        )
        return total if total else 0

# Initialize Database
with app.app_context():
    db.create_all()
    
    if not User.query.first():
        # Create test users
        test_user = User(
            username='testuser',
            email='user@example.com',
            role='user'
        )
        test_user.set_password('testpass')
        
        test_manager = User(
            username='testmanager',
            email='manager@example.com',
            role='manager'
        )
        test_manager.set_password('managerpass')
        
        db.session.add_all([test_user, test_manager])
        db.session.commit()

# Routes
@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('userlogin'))
    
    if session.get('is_manager'):
        return redirect(url_for('manager_dashboard'))
    
    events = Event.query.order_by(Event.date.asc()).all()
    return render_template('landing.html', events=events)

@app.route('/manager_dashboard')
def manager_dashboard():
    if not session.get('is_manager'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    manager = User.query.filter_by(username=session['username']).first()
    events = Event.query.filter_by(manager_id=manager.id).order_by(Event.date.asc()).all()
    return render_template('manager_landing.html', manager_events=events)

@app.route('/userlogin', methods=['GET', 'POST'])
def userlogin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
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
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username, role='manager').first()
        
        if user and user.check_password(password):
            session['username'] = username
            session['is_manager'] = True
            flash('Manager login successful!', 'success')
            return redirect(url_for('home'))
        
        flash('Invalid manager credentials', 'danger')
    return render_template('managerlogin.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
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

@app.route('/usersettings', methods=['GET', 'POST'])
def usersettings():
    if 'username' not in session:
        return redirect(url_for('userlogin'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        
        if new_username and new_username != user.username:
            if User.query.filter_by(username=new_username).first():
                flash('Username already taken', 'danger')
            else:
                user.username = new_username
                flash('Username updated successfully', 'success')
        
        if new_password:
            user.set_password(new_password)
            flash('Password updated successfully', 'success')
        
        db.session.commit()
        return redirect(url_for('usersettings'))
    
    return render_template('usersettings.html', user=user)

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if not session.get('is_manager'):
        flash('Unauthorized', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            manager = User.query.filter_by(username=session['username']).first()
            
            new_event = Event(
                title=request.form['title'],
                description=request.form['description'],
                date=request.form['date'],
                time=request.form['time'],
                location=request.form['location'],
                event_type=request.form['event_type'], 
                manager_id=manager.id
            )
            db.session.add(new_event)
            db.session.commit()
            flash('Event created successfully!', 'success')
            return redirect(url_for('manager_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating event: {str(e)}', 'danger')
    
    return render_template('create_event.html')

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    if not session.get('is_manager'):
        flash('Unauthorized', 'danger')
        return redirect(url_for('home'))

    event = Event.query.get_or_404(event_id)
    current_manager = User.query.filter_by(username=session['username']).first()
    
    if event.manager_id != current_manager.id:
        flash("You can only edit your own events", 'danger')
        return redirect(url_for('manager_dashboard'))

    if request.method == 'POST':
        try:
            event.title = request.form['title']
            event.description = request.form['description']
            event.date = request.form['date']
            event.time = request.form['time']
            event.location = request.form['location']
            db.session.commit()
            flash('Event updated successfully!', 'success')
            return redirect(url_for('manager_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating event: {str(e)}', 'danger')
    
    return render_template('edit_event.html', event=event)

@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if not session.get('is_manager'):
        flash('Unauthorized', 'danger')
        return redirect(url_for('home'))

    event = Event.query.get_or_404(event_id)
    current_manager = User.query.filter_by(username=session['username']).first()
    
    if event.manager_id != current_manager.id:
        flash("You can only delete your own events", 'danger')
        return redirect(url_for('manager_dashboard'))

    try:
        db.session.delete(event)
        db.session.commit()
        flash('Event deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting event: {str(e)}', 'danger')
    
    return redirect(url_for('manager_dashboard'))

@app.route('/event/<int:event_id>')
def event_details(event_id):
    if 'username' not in session:
        return redirect(url_for('userlogin'))
    
    event = Event.query.get_or_404(event_id)
    user = User.query.filter_by(username=session['username']).first()
    
    is_registered = db.session.execute(
        select(registrations.c.user_id)
        .where(registrations.c.user_id == user.id)
        .where(registrations.c.event_id == event.id)
    ).fetchone() is not None
    
    # Changed to pass the property value directly
    return render_template('event_details.html', 
                         event=event,
                         is_registered=is_registered,
                         total_attendees=event.total_attendees) 

@app.route('/register_for_event/<int:event_id>', methods=['POST'])
def register_for_event(event_id):
    if 'username' not in session:
        return redirect(url_for('userlogin'))
    
    event = Event.query.get_or_404(event_id)
    user = User.query.filter_by(username=session['username']).first()
    
    existing_reg = db.session.execute(
        select(registrations)
        .where(registrations.c.user_id == user.id)
        .where(registrations.c.event_id == event.id)
    ).fetchone()
    
    if existing_reg:
        flash('You are already registered for this event', 'warning')
        return redirect(url_for('event_details', event_id=event.id))
    
    try:
        num_attendees = int(request.form.get('num_attendees', 1))
        if num_attendees < 1:
            flash('Number of attendees must be at least 1', 'danger')
            return redirect(url_for('event_details', event_id=event.id))
        
        db.session.execute(
            registrations.insert().values(
                user_id=user.id,
                event_id=event.id,
                num_attendees=num_attendees
            )
        )
        db.session.commit()
        flash(f'Successfully registered {num_attendees} attendee(s)!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Registration failed: {str(e)}', 'danger')
    
    return redirect(url_for('event_details', event_id=event.id))

@app.route('/unregister_from_event/<int:event_id>', methods=['POST'])
def unregister_from_event(event_id):
    if 'username' not in session:
        return redirect(url_for('userlogin'))
    
    event = Event.query.get_or_404(event_id)
    user = User.query.filter_by(username=session['username']).first()
    
    try:
        db.session.execute(
            registrations.delete()
            .where(registrations.c.user_id == user.id)
            .where(registrations.c.event_id == event.id)
        )
        db.session.commit()
        flash('Successfully unregistered from event', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to unregister: {str(e)}', 'danger')
    
    return redirect(url_for('event_details', event_id=event.id))

if __name__ == '__main__':
    app.run(debug=True)