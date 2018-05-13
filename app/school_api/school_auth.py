import re
from flask import url_for, g, request
from flask_restful import Resource, abort, marshal_with, fields as rfields
from flask_httpauth import HTTPBasicAuth
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Teacher, School, Tcode
from .. import db
from . import school_api_bp, school_api

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


# @school_api_bp.before_request
# @auth.login_required
# def before_request():
#    pass


class GetToken(Resource):
    def get(self):
        token = g.teacher_user.generate_auth_token(600)
        return {'token': token, 'expiration': 600}


# use_args
teacher_reg = {
    'telephone': fields.String(
        required=True,
        validate=lambda p: re.match('^1[34578]\\d{9}$', p) is not None
    ),
    'nickname': fields.String(required=True),
    'tcode': fields.String(required=True),
    'password': fields.String(required=True, validate=lambda p: len(p) >= 6)
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
        print(request.args)
        # 通过邀请码匹配学校并删除已经被使用的邀请码
        tcode = args['tcode']
        school = db.session.query(School).filter(
            School.tcodes.any(Tcode.code == tcode)).first()
        if not school:
            abort(404, message="邀请码不正确，请联系您的机构或学校", code='2001')
        teacher = Teacher(
            telephone=args['telephone'],
            nickname=args['nickname'],
            password=args['password']
        )
        teacher.schools.append(school)
        db.session.add(teacher)
        code = db.session.query(Tcode).filter_by(code=tcode).first()
        db.session.delete(code)
        db.session.commit()
        result = Teacher.query.get(teacher.id)
        return result, 201


school_api.add_resource(TeacherReg, '/register', endpoint='register')
school_api.add_resource(GetToken, '/token')
