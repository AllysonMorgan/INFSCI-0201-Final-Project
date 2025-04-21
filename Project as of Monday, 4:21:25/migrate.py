# migrate.py
from sqlalchemy import create_engine, text

def add_username_column():
    # Connect directly to the database (no Flask app needed)
    engine = create_engine('sqlite:///instance/database.db')
    
    try:
        with engine.connect() as connection:
            # Check if column exists first
            result = connection.execute(text("PRAGMA table_info(attendee)"))
            columns = [row[1] for row in result]
            
            if 'username' not in columns:
                connection.execute(text("ALTER TABLE attendee ADD COLUMN username VARCHAR(50)"))
                connection.commit()
                print("Column added successfully!")
            else:
                print("Column already exists")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        engine.dispose()

if __name__ == '__main__':
    add_username_column()