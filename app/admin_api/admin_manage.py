from flask_restful import Resource, abort
from webargs import fields
from webargs.flaskparser import use_args
from sqlalchemy.exc import IntegrityError
from ..models import Admin, School
from .. import db
from . import admin_api_bp, admin_api


hello_args = {
    'name': fields.Str(required = True),
    'age': fields.Str(required = True)
}

school_args = {
    'name': fields.Str(required = True),
    'intro': fields.Str(required = False, default=''),
    'admin': fields.Str(required = True)
}

class SchoolList(Resource):
    @use_args(hello_args)
    def get(self, args):
        return 'Hello' + args['name'] + args['age']

    @use_args(school_args)
    def post(self, args):
        if School.query.filter_by(name=args['name']).first():
            return {'message': '学校名称已经存在', 'status': 409 },409
        school = School(name=args['name'], intro=args['intro'], admin=args['admin'])
        db.session.add(school)
        db.session.commit()
        return 'ok'

admin_api.add_resource(SchoolList, '/school')
