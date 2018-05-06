from flask import Blueprint
from flask_restful import Api

admin_api_bp = Blueprint('admin_api', __name__)
admin_api = Api(admin_api_bp)

from . import admin_auth
