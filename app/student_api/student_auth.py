from flask import g
from flask_httpauth import HTTPBasicAuth
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Student
from .. import db
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
