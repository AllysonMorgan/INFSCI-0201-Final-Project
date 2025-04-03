from newmain1 import app, db

with app.app_context():
    db.create_all() 