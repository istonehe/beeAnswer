from flask_restful import Resource, abort
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Admin
from . import admin_api_bp, admin_api

hello_args = {
    'name': fields.Str(required = True),
    'age': fields.Str(required = True)
}

school_args = {
    'name': fields.Str(required = True)
}


class SchoolList(Resource):
    @use_args(hello_args)
    def get(self, args):
        return 'Hello' + args['name'] + args['ages']

    @use_args(school_args)
    def post(self):
        pass

admin_api.add_resource(SchoolList, '/school')
