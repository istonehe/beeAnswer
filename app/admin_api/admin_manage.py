import re
from flask import url_for
from flask_restful import Resource, abort, marshal_with, fields as rfields
from webargs import fields, ValidationError
from sqlalchemy import func
from webargs.flaskparser import use_args
from sqlalchemy.exc import IntegrityError
from ..models import School, Tcode
from .. import db
from . import admin_api

# use_args
schoollist_get_args = {
    'page': fields.Int(missing=1),
    'per_page': fields.Int(missing=10)
}

school_args = {
    'name': fields.Str(required=True, validate=lambda p: len(p) >= 3),
    'intro': fields.Str(required=False, default='', missing=' '),
    'admin_phone': fields.Str(
        required=True,
        validate=lambda p: re.match('^1[34578]\\d{9}$', p) is not None
    )
}

school_search = {
    'name': fields.Str(required=True),
    'page': fields.Int(missing=1),
    'per_page': fields.Int(missing=10)
}

# marshal_with
school_paging_list = {
    'schools': rfields.Nested({
        'id': rfields.Integer,
        'name': rfields.String,
        'intro': rfields.String,
        'admin': rfields.String,
        'timestamp': rfields.DateTime(dt_format='rfc822'),
        'url': rfields.Url(absolute=True, endpoint='admin_api.school')
    }),
    'prev': rfields.String,
    'next': rfields.String,
    'count': rfields.Integer
}

school_created = {
    'id': rfields.Integer,
    'name': rfields.String,
    'intro': rfields.String,
    'admin': rfields.String,
    'timestamp': rfields.DateTime(dt_format='rfc822'),
    'url': rfields.Url(absolute=True, endpoint='admin_api.school')
}

school_test = {
    'id': rfields.Integer,
    'name': rfields.String
}


def abort_if_scholl_doesnt_exist(id):
    count = db.session.query(func.count(School.id)).scalar()
    if id < 0 or id > count:
        abort(404, error='错误的请求', message='学校不存在', code=1001)


class SchoolList(Resource):
    @marshal_with(school_paging_list, envelope='resource')
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
            'schools': schools,
            'prev': prev,
            'next': next,
            'count': pagination.total
        }
        return result, 200

    @marshal_with(school_created, envelope='resource')
    @use_args(school_args)
    def post(self, args):
        school = School(name=args['name'], intro=args['intro'], admin=args['admin_phone'])
        db.session.add(school)
        db.session.commit()
        result = School.query.get(school.id)
        Tcode.generate_code(10, school.id)
        return result, 201


class Schoolx(Resource):
    @marshal_with(school_created, envelope='resource')
    def get(self, id):
        abort_if_scholl_doesnt_exist(id)
        school = School.query.get(id)
        return school, 200

    def delete(self, id):
        abort_if_scholl_doesnt_exist(id)
        school = School.query.get(id)
        db.session.delete(school)
        db.session.commit()
        return '', 204

    @marshal_with(school_created, envelope='resource')
    @use_args(school_args)
    def put(self, args, id):
        abort_if_scholl_doesnt_exist(id)
        school = School.query.get(id)
        school.name = args['name']
        school.intro = args['intro']
        school.admin = args['admin_phone']
        db.session.add(school)
        db.session.commit()
        result = School.query.get(school.id)
        return result, 201


class SchoolSearch(Resource):
    @marshal_with(school_paging_list, envelope='resource')
    @use_args(school_search)
    def get(self, args):
        pagination = db.session.query(School).filter(School.name.like(args['name']+"%")).paginate(page=args['page'], per_page=args['per_page'], error_out=True)
        schools = pagination.items
        prev = None
        if pagination.has_prev:
            prev = url_for('admin_api.school', id=args['page']-1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('admin_api.school', id=args['page']+1, _external=True)
        result = {
            'schools': schools,
            'prev': prev,
            'next': next,
            'count': pagination.total
        }
        return result, 200


admin_api.add_resource(SchoolList, '/school', endpoint='schools')
admin_api.add_resource(Schoolx, '/school/<int:id>', endpoint='school')
admin_api.add_resource(SchoolSearch, '/school/search')
