import re
from flask import g
from flask_restful import Resource, marshal_with, fields as rfields
from flask_httpauth import HTTPBasicAuth
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Student
from .. import db
from . import student_api

auth = HTTPBasicAuth()


# use_args
student_reg = {
    'telephone': fields.Int(
        required=True,
        validate=lambda p: re.match('^1[34578]\\d{9}$', str(p)) is not None
    ),
    'nickname': fields.Str(required=True),
    'password': fields.Str(required=True, validate=lambda p: len(p) >= 6)
}

# marshal_with
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
    student_user = Student.verify_auth_token(username_or_token)
    if not student_user:
        student_user = Student.query.filter_by(telephone=username_or_token).first()
        if not student_user or not student_user.verify_password(password):
            return False
    g.student_user = student_user
    return True


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


class GetToken(Resource):
    @auth.login_required
    def get(self):
        token = g.student_user.generate_auth_token(600)
        return {'token': token, 'expiration': 600}


student_api.add_resource(StudentReg, '/register')
student_api.add_resource(GetToken, '/token')
