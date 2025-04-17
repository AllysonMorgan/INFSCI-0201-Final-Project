import unittest
from main import app, db, User

class FlaskAppTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_events.db'
        cls.app = app
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            db.create_all()
            test_user = User(username='testuser', email='testuser@example.com', role='user')
            test_user.set_password('testpassword')
            db.session.add(test_user)
            db.session.commit()

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            db.drop_all()

    def test_user_registration(self):
        response = self.client.post('/register', data={
            'username': 'newuser',
            'password': 'newpassword'
        })
        self.assertEqual(response.status_code, 302)

    def test_user_login(self):
        response = self.client.post('/userlogin', data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 302) 

if __name__ == '__main__':
    unittest.main()

#If everything is working properly, running this file will not return any error messages