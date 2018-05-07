import unittest
import time
from app import create_app, db
from app.models import Admin

class ModelTestCase(unittest.TestCase):
    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.drop_all()

    def test_admin_password_setter(self):
        u = Admin(password = 'cat')
        self.assertTrue(u.password_hash is not None)

    def test_admin_no_password_getter(self):
        u = Admin(password = 'cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_admin_password_verification(self):
        u = Admin(password = 'cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        u = Admin(password = 'cat')
        u2 = Admin(password = 'cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_admin_valid_confirmation_token(self):
        u = Admin(password = 'cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_auth_token()
        self.assertTrue(u.verify_auth_token(token) == u)

    def test_admin_invalid_confirmation_token(self):
        u1 = Admin(password = 'cat')
        u2 = Admin(password = 'dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_auth_token()
        self.assertFalse(u2.verify_auth_token(token) == u2)

    def test_admin_expired_confirmation_token(self):
        u = Admin(password = 'cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_auth_token(1)
        time.sleep(2)
        self.assertFalse(u.verify_auth_token(token) == u)

        
