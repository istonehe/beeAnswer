import string
import random
from datetime import datetime
from flask import current_app, g
from flask_restful import abort
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import db


class Permission:
    CORRECT = 1
    ADMIN = 16


class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True)
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

# 验证密码哈希串
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

# 生成token
    def generate_auth_token(self, expiration=600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        admin_user = Admin.query.get(data['id'])
        return admin_user


employs = db.Table(
    'employs',
    db.Column(
        'school_id',
        db.Integer,
        db.ForeignKey('schools.id'),
        primary_key=True
        ),
    db.Column(
        'teacher_id',
        db.Integer,
        db.ForeignKey('teachers.id'),
        primary_key=True
        )
)

customers = db.Table(
    'customers',
    db.Column(
        'school_id',
        db.Integer,
        db.ForeignKey('schools.id'),
        primary_key=True
    ),
    db.Column(
        'teacher_id',
        db.Integer,
        db.ForeignKey('students.id'),
        primary_key=True
    )
)


class School(db.Model):
    __tablename__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    intro = db.Column(db.Text)
    admin = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    disabled = db.Column(db.Boolean, default=False)
    courses = db.relationship(
        'Course',
        backref='school',
        lazy='dynamic'
    )
    tcodes = db.relationship(
        'Tcode',
        backref='school',
        lazy='dynamic',
        cascade="all, delete, delete-orphan"
    )


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(128))
    rename = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))
    intro = db.Column(db.Text)
    imgurl = db.Column(db.String(256))
    email = db.Column(db.String(64), unique=True)
    telephone = db.Column(db.String(16), unique=True, index=True)
    gender = db.Column(db.Integer, default=0)
    wxopenid = db.Column(db.String(32), unique=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.relationship('Answer', backref='teacher', lazy='dynamic')
    schools = db.relationship(
        'School',
        secondary=employs,
        backref=db.backref('teachers', lazy='dynamic'),
        lazy='dynamic'
    )

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    # 验证密码哈希串
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 生成token
    def generate_auth_token(self, expiration=600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        teacher_user = Teacher.query.get(data['id'])
        return teacher_user

    def is_teacher_admin(school_id):
        school = School.query.get(school_id)
        return school.admin == g.teacher_user.telephone


class Tcode(db.Model):
    __tablename__ = 'tcodes'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(16),  unique=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))

    @staticmethod
    def generate_code(quantity, school_id):
        school = School.query.get(school_id)
        if school.tcodes.count() > 0:
            abort(403, message="邀请码使用完才能重新生成", code='2003')

        stringbase = string.ascii_letters + string.digits

        def random_code(x, y):
            return ''.join([random.choice(x) for i in range(y)])

        for index in range(quantity):
            c = random_code(stringbase, 12)
            c = Tcode(code=c, school_id=school_id)
            db.session.add(c)

        db.session.commit()


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(128))
    rename = db.Column(db.String(128))
    password_hash = db.Column(db.String(128))
    imgurl = db.Column(db.String(256))
    fromwhere = db.Column(db.String(128))
    vip = db.Column(db.Boolean, default=False)
    expvalue = (db.Integer)
    ask_times = db.Column(db.Integer, default=5)
    wxopenid = db.Column(db.String(32), unique=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    disabled = db.Column(db.Boolean, default=False)
    asks = db.relationship('Ask', backref='student', lazy='dynamic')
    feedbacks = db.relationship('Feedback', backref='student', lazy='dynamic')
    schools = db.relationship(
        'School',
        secondary=customers,
        backref=db.backref('students', lazy='dynamic'),
        lazy='dynamic'
    )


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(64))
    course_intro = db.Column(db.String(256))
    nomal_times = db.Column(db.Integer, default=5)
    vip_times = db.Column(db.Integer, default=0)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))


class Ask(db.Model):
    __tablename__ = 'asks'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ask_text = db.Column(db.Text)
    voice_url = db.Column(db.String(256))
    voice_duration = db.Column(db.String(16))
    topicimages = db.relationship('Topicimage', backref='ask', lazy='dynamic')
    answers = db.relationship('Answer', backref='ask', lazy='dynamic')
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))


class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    ask_text = db.Column(db.Text)
    voice_url = db.Column(db.String(256))
    voice_duration = db.Column(db.String(16))
    topicimages = db.relationship('Topicimage', backref='answer', lazy='dynamic')
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    ask_id = db.Column(db.Integer, db.ForeignKey('asks.id'))
    answer_rate = db.Column(db.Integer, default=0)


class Topicimage(db.Model):
    __tablename__ = 'topicimages'
    id = db.Column(db.Integer, primary_key=True)
    img_url = db.Column(db.String(256))
    img_title = db.Column(db.String(128))
    img_sort = db.Column(db.Integer)
    ask_id = db.Column(db.Integer, db.ForeignKey('asks.id'))
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'))


class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    fb_text = db.Column(db.Text)
    fb_contact = db.Column(db.String(64))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
