from flask_restful import Resource, abort, marshal_with, fields as rfields
from webargs import fields, ValidationError
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
    'name': fields.Str(required = True, validate=lambda p: len(p) >= 3),
    'intro': fields.Str(required = False, default=''),
    'admin_email': fields.Email(required = True)
}

schoollist_outputs={

}

school_outputs = {
    'name': rfields.String,
    'intro': rfields.String,
    'admin': rfields.String,
    'url': rfields.Url(absolute=True)
}

class SchoolList(Resource):
    @use_args(hello_args)
    def get(self, args):
        return 'Hello' + args['name'] + args['age']

    @marshal_with(school_outputs, envelope='resource')
    @use_args(school_args)
    def post(self, args):
        school = School(name=args['name'], intro=args['intro'], admin=args['admin_email'])
        db.session.add(school)
        db.session.commit()
        result = School.query.get(school.id)
        return result,201

admin_api.add_resource(SchoolList, '/school')
