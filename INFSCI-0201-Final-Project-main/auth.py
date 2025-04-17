from werkzeug.security import generate_password_hash, check_password_hash

def register_user(username, email, password, is_manager=False):
    hashed_pw = generate_password_hash(password)
    role = 'manager' if is_manager else 'user'
    new_user = User(username=username, email=email, 
                   password_hash=hashed_pw, role=role)
    db.session.add(new_user)
    db.session.commit()

def verify_login(username, password):
    user = User.query.filter_by(username=username).first()
    return user if user and check_password_hash(user.password_hash, password) else None