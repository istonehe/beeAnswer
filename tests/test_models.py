import unittest
from app.models import Admin

class ModelTestCase(unittest.TestCase):
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
