from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
db = SQLAlchemy(app)

with app.app_context():
    # Add the missing email column
    try:
        db.session.execute(text('ALTER TABLE user ADD COLUMN email VARCHAR(120)'))
        db.session.commit()
        print("Successfully added email column")
    except Exception as e:
        print(f"Error: {e}")
        db.session.rollback()