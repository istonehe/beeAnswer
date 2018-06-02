from flask import g
from flask_restful import Resource, abort
from flask_httpauth import HTTPBasicAuth
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Teacher
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


@school_api_bp.before_request
@auth.login_required
def before_request():
    pass


@auth.error_handler
def auth_error():
    abort(401, code=4, message='未授权')


class GetToken(Resource):
    def get(self):
        token = g.teacher_user.generate_auth_token(600)
        return {'code': 1, 'token': token, 'expiration': 600}


# use_args
teacher_tcode = {
    'tcode': fields.Str(required=True)
}


class TeacherBindSchool(Resource):
    @use_args(teacher_tcode)
    def put(self, args):
        tcode = args['tcode']
        if g.teacher_user.bind_school(tcode):
            return '已加入学校', 201


school_api.add_resource(GetToken, '/token')
school_api.add_resource(TeacherBindSchool, '/bind')
