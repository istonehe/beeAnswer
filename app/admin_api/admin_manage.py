import re
from flask import url_for
from flask_restful import Resource, abort, marshal_with, fields as rfields
from webargs import fields, ValidationError
from sqlalchemy import func
from webargs.flaskparser import use_args
from sqlalchemy.exc import IntegrityError
from ..models import School, Tcode, Teacher
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

teacher_list_args = {
    'school_id': fields.Int(missing='0'),
    'page': fields.Int(missing=1),
    'per_page': fields.Int(missing=20)
}

teacher_args = {
    'nickname': fields.Str(missing=' '),
    'rename': fields.Str(missing=' '),
    'intro': fields.Str(missing=' '),
    'imgurl': fields.Str(missing=' '),
    'telephone': fields.Str(
        missing=' ',
        validate=lambda p: re.match('^1[34578]\\d{9}$', p) is not None
    ),
    'gender': fields.Int(missing=0)
}

teacher_search = {
    'telephone': fields.Str(
        required=True,
        validate=lambda p: re.match('^1[34578]\\d{9}$', p) is not None
    )
}

dismiss_teacher = {
    'school_id': fields.Int(required=True),
    'teacher_id': fields.Int(required=True)
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

teacher_paging_list = {
    'teachers': rfields.Nested({
        'id': rfields.Integer,
        'nickname': rfields.String,
        'rename': rfields.String,
        'imgurl': rfields.String,
        'telephone': rfields.String,
        'gender': rfields.String,
        'wxopenid': rfields.String,
        'timestamp': rfields.DateTime(dt_format='rfc822'),
        'url': rfields.Url(absolute=True, endpoint='admin_api.school')
    }),
    'prev': rfields.String,
    'next': rfields.String,
    'count': rfields.Integer
}

teacher_created = {
    'id': rfields.Integer,
    'nickname': rfields.String,
    'rename': rfields.String(default=' '),
    'imgurl': rfields.String(default=' '),
    'telephone': rfields.String,
    'gender': rfields.String,
    'wxopenid': rfields.String,
    'schools': rfields.Nested({
        'id': rfields.Integer,
        'name': rfields.String,
        'url': rfields.Url(absolute=True, endpoint='admin_api.school')
    }),
    'timestamp': rfields.DateTime(dt_format='rfc822'),
    'url': rfields.Url(absolute=True, endpoint='admin_api.teacher')
}


def abort_if_scholl_doesnt_exist(id):
    if School.query.get(id) is None:
        abort(404, message='学校不存在', code=1001)


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
        pagination = db.session.query(School).filter(
            School.name.like(args['name']+"%")
        ).paginate(
            page=args['page'],
            per_page=args['per_page'],
            error_out=True
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


class TeacherList(Resource):
    @marshal_with(teacher_paging_list, envelope='resource')
    @use_args(teacher_list_args)
    def get(self, args):
        s_id = args['school_id']
        abort_if_scholl_doesnt_exist(s_id)
        if s_id == 0:
            pagination = Teacher.query.paginate(
                page=s_id,
                per_page=s_id,
                error_out=True
            )
        else:
            pagination = School.query.get(s_id).teachers.paginate(
                page=s_id,
                per_page=s_id,
                error_out=True
            )
        
        teachers = pagination.items
        prev = None
        if pagination.has_prev:
            prev = url_for('admin_api.teachers', id=s_id-1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('admin_api.teachers', id=s_id+1, _external=True)
        result = {
            'teachers': teachers,
            'prev': prev,
            'next': next,
            'count': pagination.total
        }
        return result, 200


def abort_if_teacher_doesnt_exist(id):
    if Teacher.query.get(id) is None:
        abort(404, message='教师不存在', code=1001)


class Teacherx(Resource):
    @marshal_with(teacher_created, envelope='resource')
    def get(self, id):
        abort_if_teacher_doesnt_exist(id)
        teacher = Teacher.query.get(id)
        return teacher, 200

    def delete(self, id):
        abort_if_teacher_doesnt_exist(id)
        teacher = Teacher.query.get(id)
        db.session.delete(teacher)
        db.session.commit()
        return '', 204

    @marshal_with(teacher_created, envelope='resource')
    @use_args(teacher_args)
    def put(self, args, id):
        abort_if_teacher_doesnt_exist(id)
        teacher = Teacher.query.get(id)
        teacher.nickname = args['nickname']
        teacher.rename = args['rename']
        teacher.intro = args['intro']
        teacher.imgurl = args['imgurl']
        teacher.telephone = args['telephone']
        teacher.gender = args['gender']
        db.session.add(teacher)
        db.session.commit()
        result = Teacher.query.get(teacher.id)
        return result, 201


class TeacherSearch(Resource):
    @marshal_with(teacher_created, envelope='resource')
    @use_args(teacher_search)
    def get(self, args):
        teacher = Teacher.query.filter_by(telephone=args['telephone']).first()
        if teacher is None:
            abort(404, message='教师不存在', code=1001)
        return teacher, 200


class DismissTeacher(Resource):
    @use_args(dismiss_teacher)
    def delete(self, args):
        s_id = args['school_id']
        t_id = args['teacher_id']
        abort_if_scholl_doesnt_exist(s_id)
        abort_if_teacher_doesnt_exist(t_id)
        teacher = Teacher.query.get(t_id)
        teacher.dismiss_school(s_id)
        return '', 204


admin_api.add_resource(SchoolList, '/school', endpoint='schools')
admin_api.add_resource(Schoolx, '/school/<int:id>', endpoint='school')
admin_api.add_resource(SchoolSearch, '/school/search')

admin_api.add_resource(TeacherList, '/teacher', endpoint='teachers')
admin_api.add_resource(Teacherx, '/teacher/<int:id>', endpoint='teacher')
admin_api.add_resource(TeacherSearch, '/teacher/search')
admin_api.add_resource(DismissTeacher, '/dismiss')
