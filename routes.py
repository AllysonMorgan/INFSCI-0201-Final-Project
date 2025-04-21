from main import app
from models import db, User, Event
from flask import render_template, request, redirect, url_for, session, flash

@app.route('/manager_dashboard')
def manager_dashboard():
    if not session.get('is_manager'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('home'))
    
    manager = User.query.filter_by(username=session['username']).first()
    events = Event.query.filter_by(manager_id=manager.id).all()
    return render_template('manager_landing.html', manager_events=events)
