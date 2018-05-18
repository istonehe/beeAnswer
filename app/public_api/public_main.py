from flask import g
from flask_restful import Resource
from flask_httpauth import HTTPBasicAuth
from ..models import Teacher, Student
from .. import db
from . import public_api

auth = HTTPBasicAuth()


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


class PublicHello(Resource):
    @auth.login_required
    def get(self):
        return 'ok', 200


public_api.add_resource(PublicHello, '/')

