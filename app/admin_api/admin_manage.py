from flask_restful import Resource, abort

from ..models import Admin
from . import admin_api_bp, admin_api


class SchoolList(Resource):
    def get(self):
        pass

    def post(self):
        pass

admin_api.add_resource(SchoolList, '/school')
