from datetime import datetime
from flask import current_app, request, url_for
from . import db

class Permission:
    CORRECT = 1
    ADMIN = 16

employs = db.Table('employs',
    db.Column('school_id', db.Integer, db.ForeignKey('schools.id'), primary_key=True),
    db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id'), primary_key=True)
)

customers = db.Table('customers',
    db.Column('school_id', db.Integer, db.ForeignKey('schools.id'), primary_key=True),
    db.Column('teacher_id', db.Integer, db.ForeignKey('students.id'), primary_key=True)
)

class School(db.Model):
    __tablename__ = 'schools'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True)
    intro = db.Column(db.Text)
    admin = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    disabled = db.Column(db.Boolean, default=False)
    courses = db.relationship('Course', backref='school', lazy='dynamic')


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(256))
    rename = db.Column(db.String(256))
    intro = db.Column(db.Text)
    imgurl = db.Column(db.String(256))
    email = db.Column(db.String(64), unique=True, index=True)
    telephone = db.Column(db.String(16), unique=True)
    gender = db.Column(db.Integer, default=0)
    wxopenid = db.Column(db.String(32), unique=True)
    answers = db.relationship('Answer', backref='teacher', lazy='dynamic')
    schools = db.relationship('School',
                                secondary=employs,
                                backref=db.backref('teachers', lazy='dynamic'),
                                lazy='dynamic')


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(256))
    rename = db.Column(db.String(256))
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
    schools = db.relationship('School',
                                secondary=customers,
                                backref=db.backref('students', lazy='dynamic'),
                                lazy='dynamic')


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
    answer_rate = db.Column(db.Integer, default = 0)

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
