from flask import g
from flask_restful import Resource
from flask_httpauth import HTTPBasicAuth
from ..models import Student
from . import student_api, student_api_bp

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username_or_token, password):
    student_user = Student.verify_auth_token(username_or_token)
    if not student_user:
        student_user = Student.query.filter_by(telephone=username_or_token).first()
        if not student_user or not student_user.verify_password(password):
            return False
    g.student_user = student_user
    return True


@student_api_bp.before_request
@auth.login_required
def before_request():
    pass


class GetToken(Resource):
    def get(self):
        token = g.student_user.generate_auth_token(600)
        return {'token': token, 'expiration': 600}


student_api.add_resource(GetToken, '/token')
