from main import app, db, User, Event

with app.app_context():
    # Drop all tables (just in case)
    db.drop_all()
    
    # Create all tables with current schema
    db.create_all()
    
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
    
    print("Database successfully recreated with:")
    print(f"- Users: {User.query.count()}")
    print(f"- Events: {Event.query.count()}")
