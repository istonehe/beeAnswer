from flask import url_for
from flask_restful import Resource, abort, marshal_with, fields as rfields
from webargs import fields, ValidationError
from webargs.flaskparser import use_args
from sqlalchemy.exc import IntegrityError
from ..models import Admin, School
from .. import db
from . import admin_api_bp, admin_api

schoollist_get_args = {
    'page': fields.Int(),
    'per_page': fields.Int()
}

school_post_args = {
    'name': fields.Str(required = True, validate=lambda p: len(p) >= 3),
    'intro': fields.Str(required = False, default=''),
    'admin_email': fields.Email(required = True)
}


school_list={
    'schools':rfields.Nested({
        'id': rfields.Integer,
        'name': rfields.String,
        'intro': rfields.String,
        'admin': rfields.String,
        'timestamp': rfields.DateTime(dt_format='rfc822'),
        'url': rfields.Url(absolute=True, endpoint='admin_api.school')
    }),
    'prev':rfields.String,
    'next':rfields.String,
    'count': rfields.Integer
}

school_created = {
    'id': rfields.Integer,
    'name': rfields.String,
    'intro': rfields.String,
    'admin': rfields.String,
    'timestamp': rfields.DateTime(dt_format='rfc822'),
    'url': rfields.Url(absolute=True, endpoint='admin_api.schools')
}

class SchoolList(Resource):
    @marshal_with(school_list, envelope='resource')
    @use_args(schoollist_get_args)
    def get(self, args):
        pagination = School.query.paginate(
            page=args['page'], per_page=args['per_page'], error_out=True
        )
        schools = pagination.items
        prev = None
        if pagination.has_prev:
            prev = url_for('admin_api.school', id=args['page']-1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('admin_api.school', id=args['page']+1, _external=True)
        result = {
        'schools':schools,
        'prev': prev,
        'next': next,
        'count': pagination.total
        }
        return result,200


    @marshal_with(school_created, envelope='resource')
    @use_args(school_post_args)
    def post(self, args):
        school = School(name=args['name'], intro=args['intro'], admin=args['admin_email'])
        db.session.add(school)
        db.session.commit()
        result = School.query.get(school.id)
        return result, 201

class Schoolx(Resource):
    @marshal_with(school_created, envelope='resource')
    def get(self, id):
        school = School.query.get(id)
        return school, 200



admin_api.add_resource(SchoolList, '/school', endpoint='schools')
admin_api.add_resource(Schoolx, '/school/<id>', endpoint='school')
