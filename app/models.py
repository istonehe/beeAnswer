from datetime import datetime
from flask import current_app, request, url_for
from . import db

class Permission:
    CORRECT = 1
    ADMIN = 16

class School(db.Model):
    __tablename__ = 'scholls'
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(64), unique=True)
    school_intro = db.Column(db.String(256))
    admin = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    disabled = db.Column(db.Boolean, default=False)
    courses = db.relationship('Course', backref='school', lazy='dynamic')
    teachers = db.relationship('Teacher', backref='school', lazy='dynamic')

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(64))
    course_intro = db.Column(db.String(256))
    nomal_times = db.Column(db.Integer, default=5)
    vip_times = db.Column(db.Integer, default=0)
    School_id = db.Column(db.Integer, db.ForeignKey('schools.id'))

class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    teacher_nickname = db.Column(db.String(32))
    teacher_rename = ab.Column(db.String(32))
    teacher_intro = db.Column(db.String(256))
    teacher_imgurl = db.Column(db.String(256))
    email = db.Column(db.String(64), unique=True, index=True)
    telephone = db.Column(db.String(16), unique=True)
    gender = db.Column(db.Integer, default=0)
    wxopenid = db.Column(db.String(32), unique=True)
    School_id = db.Column(db.Integer, db.ForeignKey('schools.id'))

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    student_nickname = db.Column(db.String(32))
    student_rename = ab.Column(db.String(32))
    student_imgurl = db.Column(db.String(256))
    fromwhere = db.Column(db.String(32))
    vip = db.Column(db.Boolean, default=False)
    expvalue = (db.Integer)
    ask_times = db.Column(db.Integer, default=5)
    wxopenid = db.Column(db.String(32), unique=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    disabled = db.Column(db.Boolean, default=False)

class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    pre_answerid = 
