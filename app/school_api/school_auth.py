import re
from flask import g, request, current_app
from flask_restful import Resource, marshal_with, fields as rfields
from flask_httpauth import HTTPBasicAuth
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Teacher
from .. import db
from . import school_api, school_api_bp

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username_or_token, password):
    teacher_user = Teacher.verify_auth_token(username_or_token)
    if not teacher_user:
        teacher_user = Teacher.query.filter_by(telephone=username_or_token).first()
        if not teacher_user or not teacher_user.verify_password(password):
            return False
    g.teacher_user = teacher_user
    return True


class GetToken(Resource):
    @auth.login_required
    def get(self):
        token = g.teacher_user.generate_auth_token(600)
        return {'token': token, 'expiration': 600}


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

teacher_tcode = {
    'tcode': fields.Str(required=True)
}


# marshal_with
teacher_info = {
    'id': rfields.Integer,
    'nickname': rfields.String,
    'rename': rfields.String,
    'intro': rfields.String,
    'telephone': rfields.Integer
}


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


class TeacherBindSchool(Resource):
    @auth.login_required
    @use_args(teacher_tcode)
    def put(self, args):
        tcode = args['tcode']
        if g.teacher_user.bind_school(tcode):
            return '已加入学校', 201


school_api.add_resource(TeacherReg, '/register')
school_api.add_resource(GetToken, '/token')
school_api.add_resource(TeacherBindSchool, '/bind')
