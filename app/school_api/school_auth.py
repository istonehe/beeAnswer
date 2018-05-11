from flask import url_for, g
from flask_restful import Resource, abort, marshal_with, fields as rfields
from flask_httpauth import HTTPBasicAuth
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Teacher
from .. import db
from . import school_api_bp, school_api

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username_or_token, password):
    teacher_user = Teacher.verify_auth_token(username_or_token)
    if not teacher_user:
        teacher_user = Teacher.query.filter_by(name=username_or_token).first()
        if not teacher_user or not teacher_user.verify_password(password):
            return False
    g.teacher_user = teacher_user
    return True


#@school_api_bp.before_request
#@auth.login_required
#def before_request():
#    pass


class GetToken(Resource):
    def get(self):
        token = g.teacher_user.generate_auth_token(600)
        return {'token': token, 'expiration': 600}


#use_args
teacher_reg = {
    'telephone': fields.Int(required=True),
    'nickname': fields.String(required=True),
    'tcode': fields.String(required=True),
    'password': fields.Str(required=True, validate=lambda p: len(p) >= 6)
}


#marshal_with
teacher_info = {
    'id': rfields.Integer,
    'nickname': rfields.String,
    'rename': rfields.String,
    'intro': rfields.String,
    'email': rfields.String,
    'telephone': rfields.Integer
}


class TeacherReg(Resource):
    @marshal_with(teacher_info, envelope='resource')
    @use_args(teacher_reg)
    def post(self, args):
        teacher = Teacher(telephone=args['telephone'], nickname=args['nickname'], password=args['password'])
        db.session.add(teacher)
        db.session.commit()
        result = Teacher.query.get(teacher.id)
        return result, 201


school_api.add_resource(TeacherReg, '/register')
school_api.add_resource(GetToken, '/token')
