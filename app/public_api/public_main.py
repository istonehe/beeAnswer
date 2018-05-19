import os
import re
from flask import g, request, current_app, url_for
from flask_restful import Resource, abort, marshal_with, fields as rfields
from flask_httpauth import HTTPBasicAuth
from werkzeug.utils import secure_filename
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Teacher, Student
from .. import db
from . import public_api

auth = HTTPBasicAuth()

basedir = os.path.dirname(os.path.realpath(__file__))

# use_args
teacher_reg = {
    'telephone': fields.Int(
        required=True,
        validate=lambda p: re.match('^1[34578]\\d{9}$', str(p)) is not None
    ),
    'nickname': fields.Str(required=True),
    'tcode': fields.Str(required=True),
    'password': fields.Str(required=True, validate=lambda p: len(p) >= 6)
}

student_reg = {
    'telephone': fields.Int(
        required=True,
        validate=lambda p: re.match('^1[34578]\\d{9}$', str(p)) is not None
    ),
    'nickname': fields.Str(required=True),
    'password': fields.Str(required=True, validate=lambda p: len(p) >= 6)
}

# marshal_with
uploadfile_info = {
    'url': rfields.String,
}

teacher_info = {
    'id': rfields.Integer,
    'nickname': rfields.String,
    'rename': rfields.String,
    'intro': rfields.String,
    'telephone': rfields.Integer
}

student_info = {
    'id': rfields.Integer,
    'nickname': rfields.String,
    'rename': rfields.String,
    'imgurl': rfields.String,
    'telephone': rfields.Integer,
    'fromwhere': rfields.String,
    'wxopenid': rfields.String,
    'timestamp': rfields.DateTime(dt_format='iso8601'),
    'disabled': rfields.Boolean,
    'expevalue': rfields.Integer
}


@auth.verify_password
def verify_password(username_or_token, password):
    teacher_user = Teacher.verify_auth_token(username_or_token)
    student_user = Student.verify_auth_token(username_or_token)
    if not (teacher_user or student_user):
        teacher_user = Teacher.query.filter_by(telephone=username_or_token).first()
        student_user = Student.query.filter_by(telephone=username_or_token).first()
        if teacher_user:
            t = teacher_user.verify_password(password)
        if student_user:
            s = student_user.verify_password(password)
        if (not teacher_user or not t) and (not student_user or not s):
            return False
    g.user = teacher_user or student_user
    return True


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


class UploadFile(Resource):
    @auth.login_required
    @marshal_with(uploadfile_info, envelope='resource')
    def post(self):
        if 'file' not in request.files:
            abort(400, message='没有文件')
        file = request.files['file']
        if file.filename == '':
            abort(400, message='No selected file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            result = {
                'url': url_for('public_api.uploadfile', filename=filename, _external=True),
            }
            return result, 200


class TeacherReg(Resource):
    @marshal_with(teacher_info, envelope='resource')
    @use_args(teacher_reg)
    def post(self, args):
        tcode = args['tcode']
        teacher = Teacher(
            telephone=args['telephone'],
            nickname=args['nickname'],
            password=args['password']
        )
        db.session.add(teacher)
        # 通过邀请码匹配学校并删除已经被使用的邀请码
        if teacher.bind_school(tcode):
            result = Teacher.query.get(teacher.id)
            return result, 201


class StudentReg(Resource):
    @marshal_with(student_info, envelope='resource')
    @use_args(student_reg)
    def post(self, args):
        student = Student(
            telephone=args['telephone'],
            nickname=args['nickname'],
            password=args['password']
        )
        db.session.add(student)
        db.session.commit()
        return student, 201


public_api.add_resource(UploadFile, '/uploads')

public_api.add_resource(StudentReg, '/student/register')
public_api.add_resource(TeacherReg, '/teacher/register')