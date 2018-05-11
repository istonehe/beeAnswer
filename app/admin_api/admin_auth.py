from flask_restful import Resource
from flask_httpauth import HTTPBasicAuth
from flask import g
from ..models import Admin
from . import admin_api_bp, admin_api

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


@admin_api_bp.before_request
@auth.login_required
def before_request():
    pass


class GetToken(Resource):
    def get(self):
        token = g.admin_user.generate_auth_token(600)
        return {'token': token, 'expiration': 600}


admin_api.add_resource(GetToken, '/token')
