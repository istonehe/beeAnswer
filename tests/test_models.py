import unittest
import time
from app import create_app, db
from app.models import Admin, School, Teacher, Tcode, Student


class ModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.drop_all()
        self.app_context.pop()

    # admin
    def test_admin_password_setter(self):
        u = Admin(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_admin_no_password_getter(self):
        u = Admin(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_admin_password_verification(self):
        u = Admin(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_admin_password_salts_are_random(self):
        u = Admin(password='cat')
        u2 = Admin(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_admin_valid_confirmation_token(self):  
        u = Admin(password='cat')
        db.session.add(u)                                     
        db.session.commit()
        token = u.generate_auth_token()
        self.assertTrue(u.verify_auth_token(token) == u)

    def test_admin_invalid_confirmation_token(self):
        u1 = Admin(password='cat')
        u2 = Admin(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_auth_token()
        self.assertFalse(u2.verify_auth_token(token) == u2)

    def test_admin_expired_confirmation_token(self):
        u = Admin(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_auth_token(1)
        time.sleep(2)
        self.assertFalse(u.verify_auth_token(token) == u)

    # teacher
    def test_teacher_password_setter(self):
        u = Teacher(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_teacher_no_password_getter(self):
        u = Teacher(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_teacher_password_verification(self):
        u = Teacher(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_teacher_password_salts_are_random(self):
        u = Teacher(password='cat')
        u2 = Teacher(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_teacher_valid_confirmation_token(self):
        u = Teacher(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_auth_token()
        self.assertTrue(u.verify_auth_token(token) == u)

    def test_teacher_invalid_confirmation_token(self):
        u1 = Teacher(password='cat')
        u2 = Teacher(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_auth_token()
        self.assertFalse(u2.verify_auth_token(token) == u2)

    def test_teacher_expired_confirmation_token(self):
        u = Teacher(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_auth_token(1)
        time.sleep(2)
        self.assertFalse(u.verify_auth_token(token) == u)

    # school test
    def test_generate_tcode(self):
        s = School(name='aschool')
        db.session.add(s)
        db.session.commit()
        Tcode.generate_code(10, s.id)
        self.assertTrue(s.tcodes.count() == 10)
        try:
            Tcode.generate_code(10, s.id)
        except Exception as e:
            print("是的，拒绝生成新邀请码")
        self.assertTrue(s.tcodes.count() == 10)
 
    def test_teacher_is_employ_and_dissmiss(self):
        t = Teacher(telephone='13700000000')
        s = School(name='aschool')
        t.schools.append(s)
        db.session.add_all([t, s])
        db.session.commit()
        self.assertTrue(t.is_employ(s.id))
        t.dismiss_school(s.id)
        self.assertFalse(t.is_employ(s.id))

    def test_teacher_bind_school(self):
        t = Teacher(telephone='13700000000')
        s = School(name='aschool')
        db.session.add_all([t, s])
        db.session.commit()
        Tcode.generate_code(10, s.id)
        tcode = Tcode.query.all()[0].code
        t.bind_school(tcode)
        self.assertTrue(t.schools[0].id == s.id)
        self.assertTrue(Tcode.query.filter_by(code=tcode).first() is None)

    def test_teacher_is_school_admin(self):
        t = Teacher(telephone='13700000001')
        s = School(name='aschool', admin='13700000001')
        db.session.add_all([t, s])
        db.session.commit()
        self.assertFalse(t.is_teacher_admin(s.id))
        t.schools.append(s)
        db.session.commit()
        self.assertTrue(t.is_teacher_admin(s.id))

    # student
    def test_student_password_setter(self):
        u = Student(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_student_no_password_getter(self):
        u = Student(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_student_password_verification(self):
        u = Student(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_student_password_salts_are_random(self):
        u = Student(password='cat')
        u2 = Student(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_student_valid_confirmation_token(self):
        u = Student(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_auth_token()
        self.assertTrue(u.verify_auth_token(token) == u)

    def test_student_invalid_confirmation_token(self):
        u1 = Student(password='cat')
        u2 = Student(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_auth_token()
        self.assertFalse(u2.verify_auth_token(token) == u2)

    def test_student_expired_confirmation_token(self):
        u = Student(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_auth_token(1)
        time.sleep(2)
        self.assertFalse(u.verify_auth_token(token) == u)


