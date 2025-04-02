# test_models.py
def test_user_creation():
    user = User(username='test', email='test@test.com', 
               password_hash='hash', role='user')
    assert user.username == 'test'
    assert user.role == 'user'

# test_auth.py
def test_password_hashing():
    pw_hash = generate_password_hash('secret')
    assert check_password_hash(pw_hash, 'secret')
    assert not check_password_hash(pw_hash, 'wrong')