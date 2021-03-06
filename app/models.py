import string
import random
import json
from datetime import datetime
from flask import current_app
from flask_restful import abort
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import db


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
    wx_openid = db.Column(db.String(32), unique=True)
    wx_sessionkey = db.Column(db.String(32))

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
    admin = db.Column(db.String(16))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    disabled = db.Column(db.Boolean, default=False)
    wx_appid = db.Column(db.String(32))
    wx_appsecret = db.Column(db.String(32))
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
    asks = db.relationship(
        'Ask',
        backref='school',
        lazy='dynamic'
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
    telephone = db.Column(db.String(16), unique=True, index=True)
    gender = db.Column(db.Integer, default=0)
    wx_openid = db.Column(db.String(32), unique=True)
    wx_unionid = db.Column(db.String(32), unique=True)
    wx_sessionkey = db.Column(db.String(32))
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
        return s.dumps({'id': self.id, 'generate_time': json.dumps(datetime.utcnow(), default=lambda d: d.__str__())}).decode('utf-8')

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
    telephone = db.Column(db.String(16), unique=True)
    password_hash = db.Column(db.String(128))
    imgurl = db.Column(db.String(256))
    fromwhere = db.Column(db.String(128))
    expevalue = db.Column(db.Integer)
    gender = db.Column(db.String(8))
    province = db.Column(db.String(16))
    country = db.Column(db.String(16))
    city = db.Column(db.String(16))
    wx_unionid = db.Column(db.String(32), unique=True)
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
        return s.dumps({'id': self.id, 'generate_time': json.dumps(datetime.utcnow(), default=lambda d: d.__str__())}).decode('utf-8')

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
        # 将课程属性取出附给每个学校对应的学生
        course = school.courses.first()
        vip_times = course.vip_times
        nomal_times = course.nomal_times
        s_and_s = SchoolStudent(
            student=self,
            school=school,
            vip_times=vip_times,
            nomal_times=nomal_times
        )
        db.session.add(s_and_s)
        db.session.commit()

    def is_school_joined(self, school_id):
        school = School.query.get(school_id)
        if school is None:
            return False
        return school.students.filter_by(id=self.id).first() is not None

    def can_ask(self, school_id):
        school = School.query.get(school_id)
        if school is None:
            return False
        member_info = SchoolStudent.query.filter_by(
            school_id=school_id,
            student_id=self.id
        ).first()
        if member_info is None:
            return False
        if member_info.vip_expire > datetime.utcnow():
            if member_info.vip_times == -1 or member_info.vip_times > 0:
                return True
        if member_info.nomal_times > 0:
            return True
        return False


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
    be_answered = db.Column(db.Boolean, default=False)
    img_ids = db.Column(db.String(256))
    answer_grate = db.Column(db.Integer, default=0)
    answers = db.relationship(
        'Answer',
        backref='ask',
        lazy='select',
        cascade="all, delete, delete-orphan"
    )
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'))

    # 当增加或移除答案时，都要对be_answered值进行设置
    @staticmethod
    def be_answered_listener_append(target, value, initiator):
            target.be_answered = True

    def be_answered_listener_remove(target, value, initiator):
        if len(target.answers):
            target.be_answered = True
        else:
            target.be_answered = False


db.event.listen(Ask.answers, 'append', Ask.be_answered_listener_append)
db.event.listen(Ask.answers, 'remove', Ask.be_answered_listener_remove)


class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    answer_text = db.Column(db.Text)
    voice_url = db.Column(db.String(256))
    voice_duration = db.Column(db.String(16))
    img_ids = db.Column(db.String(256))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    ask_id = db.Column(db.Integer, db.ForeignKey('asks.id'))


class Topicimage(db.Model):
    __tablename__ = 'topicimages'
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    img_url = db.Column(db.String(256))
    auth_telephone = db.Column(db.String(16))
    img_sort = db.Column(db.Integer)


class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    fb_text = db.Column(db.Text)
    fb_contact = db.Column(db.String(64))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
