import string
import random
from datetime import datetime
from flask import current_app
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


class SchoolStudent(db.Model):
    __tablename__ = 'school_student'
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), primary_key=True)
    vip_expire = db.Column(db.DateTime, default=datetime.utcnow)
    vip_times = db.Column(db.Integer, default=0)
    nomal_times = db.Column(db.Integer, default=5)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    school = db.relationship(
        "School",
        backref=db.backref(
            "schools_students",
            cascade="all, delete-orphan"
        )
    )

    student = db.relationship(
        "Student",
        backref=db.backref(
            "schools_students",
            cascade="all,delete-orphan"
        )
    )


class School(db.Model):
    __tablename__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    intro = db.Column(db.Text)
    admin = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    disabled = db.Column(db.Boolean, default=False)
    courses = db.relationship(
        'Course',
        backref='school',
        lazy='dynamic',
        cascade="all, delete, delete-orphan"
    )
    tcodes = db.relationship(
        'Tcode',
        backref='school',
        lazy='dynamic',
        cascade="all, delete, delete-orphan"
    )
    students = db.relationship(
        'Student',
        secondary="school_student",
        lazy='dynamic'
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
    telephone = db.Column(db.Integer, unique=True, index=True)
    gender = db.Column(db.Integer, default=0)
    wxopenid = db.Column(db.String(32), unique=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.relationship('Answer', backref='teacher', lazy='dynamic')
    schools = db.relationship(
        'School',
        secondary=employs,
        backref=db.backref('teachers', lazy='dynamic'),
        lazy='select'
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

    def is_employ(self, school_id):
        school = School.query.get(school_id)
        if school is None:
            return False
        return school.teachers.filter_by(id=self.id).first() is not None

    def is_teacher_admin(self, school_id):
        school = School.query.get(school_id)
        return self.telephone == school.admin and self.is_employ(school_id)

    def bind_school(self, tcode):
        school = db.session.query(School).filter(
            School.tcodes.any(Tcode.code == tcode)).first()
        if not school:
            abort(404, message="邀请码不正确，请联系您的机构或学校")
        if self.is_employ(school.id):
            abort(401, message="你已经是这个学校的老师")
        self.schools.append(school)
        db.session.add(self)
        db.session.commit()
        code = db.session.query(Tcode).filter_by(code=tcode).first()
        db.session.delete(code)
        db.session.commit()
        return True

    def dismiss_school(self, school_id):
        school = School.query.get(school_id)
        if self.is_employ(school_id):
            self.schools.remove(school)
            db.session.commit()
            return True
        abort(401, message='该学校没有这个教师', code=1001)


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
    telephone = db.Column(db.Integer, unique=True)
    password_hash = db.Column(db.String(128))
    imgurl = db.Column(db.String(256))
    fromwhere = db.Column(db.String(128))
    expevalue = db.Column(db.Integer)
    wxopenid = db.Column(db.String(32), unique=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    disabled = db.Column(db.Boolean, default=False)
    asks = db.relationship('Ask', backref='student', lazy='dynamic')
    feedbacks = db.relationship('Feedback', backref='student', lazy='dynamic')
    schools = db.relationship(
        'School',
        secondary="school_student",
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
        student_user = Student.query.get(data['id'])
        return student_user

    def join_school(self, school_id):
        school = School.query.get(school_id)
        course = school.courses.first()
        vip_times = course.vip_times
        nomal_times = course.nomal_times
        s_and_s = SchoolStudent(student=self, school=school, vip_times=vip_times, nomal_times=nomal_times)
        db.session.add(s_and_s)
        db.session.commit()

    def is_school_joined(self, school_id):
        school = School.query.get(school_id)
        if school is None:
            return False
        return school.students.filter_by(id=self.id).first() is not None


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(64))
    course_intro = db.Column(db.String(256))
    nomal_times = db.Column(db.Integer, default=5)
    vip_times = db.Column(db.Integer, default=-1)
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
