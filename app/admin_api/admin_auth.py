from flask_restful import Resource
from flask_httpauth import HTTPBasicAuth
from flask import g
from ..models import Admin
from . import admin_api

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username_or_token, password):
    admin_user = Admin.verify_auth_token(username_or_token)
    if not admin_user:
        admin_user = Admin.query.filter_by(name=username_or_token).first()
        if not admin_user or not admin_user.verify_password(password):
            return False
    g.admin_user = admin_user
    return True


class TodoItem(Resource):
    def get(self):
        return 'This is api'

admin_api.add_resource(TodoItem, '/todo')
