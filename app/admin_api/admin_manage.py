import re
from flask import url_for
from flask_restful import Resource, abort, marshal_with, fields as rfields
from webargs import fields, ValidationError
from webargs.flaskparser import use_args
from sqlalchemy.exc import IntegrityError
from ..models import School, Tcode, Teacher, Course, Student, SchoolStudent
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

student_list = {
    'school_id': fields.Int(missing=0),
    'page': fields.Int(missing=1),
    'per_page': fields.Int(missing=10)
}

student_args = {
    'nickname': fields.Str(missing=' '),
    'rename': fields.Str(missing=' '),
    'intro': fields.Str(missing=' '),
    'disabled': fields.Bool(missing=False),
    'password': fields.Str(required=True, validate=lambda p: len(p) >= 6),
    'telephone': fields.Int(
        required=True,
        validate=lambda p: re.match('^1[34578]\\d{9}$', str(p)) is not None
    )
}

student_search = {
    'telephone': fields.Str(
        required=True,
        validate=lambda p: re.match('^1[34578]\\d{9}$', p) is not None
    )
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
        'url': rfields.Url(absolute=True, endpoint='admin_api.teacher')
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

student_paging_list = {
    'students': rfields.Nested({
        'id': rfields.Integer,
        'nickname': rfields.String,
        'rename': rfields.String,
        'telephone': rfields.Integer,
        'imgurl': rfields.String,
        'fromwhere': rfields.String,
        'timestamp': rfields.DateTime(dt_format='rfc822'),
        'disabled': rfields.Boolean,
        'expevalue': rfields.Integer
    }),
    'prev': rfields.String,
    'next': rfields.String,
    'count': rfields.Integer
}

scstudent_info = {
    'id': rfields.Integer,
    'nickname': rfields.String,
    'rename': rfields.String,
    'telephone': rfields.Integer,
    'imgurl': rfields.String,
    'fromwhere': rfields.String,
    'timestamp': rfields.DateTime(dt_format='rfc822'),
    'disabled': rfields.Boolean,
    'expevalue': rfields.Integer,
    'vip_times': rfields.Integer,
    'nomal_times': rfields.Integer,
    'vip_expire': rfields.DateTime(dt_format='rfc822'),
    'join_timestamp': rfields.DateTime(dt_format='rfc822')
}

student_info = {
    'id': rfields.Integer,
    'nickname': rfields.String,
    'rename': rfields.String,
    'telephone': rfields.Integer,
    'imgurl': rfields.String,
    'fromwhere': rfields.String,
    'timestamp': rfields.DateTime(dt_format='rfc822'),
    'disabled': rfields.Boolean
}


def abort_if_scholl_doesnt_exist(id):
    if School.query.get(id) is None:
        abort(404, message='学校不存在')


def abort_if_teacher_doesnt_exist(id):
    if Teacher.query.get(id) is None:
        abort(404, message='教师不存在')


def abort_if_student_doesnt_exist(id):
    if Student.query.get(id) is None:
        abort(404, message='学生不存在')


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
        course = Course(
            course_name='这是一个课程案例',
            course_intro='请填写一些课程介绍',
            nomal_times=5,
            vip_times=0,
            school_id=school.id
        )
        db.session.add(course)
        db.session.commit()
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
        page = args['page']
        per_page = args['per_page']
        abort_if_scholl_doesnt_exist(s_id)
        if s_id == 0:
            pagination = Teacher.query.paginate(
                page=page,
                per_page=per_page,
                error_out=True
            )
        else:
            pagination = School.query.get(s_id).teachers.paginate(
                page=page,
                per_page=per_page,
                error_out=True
            )

        teachers = pagination.items
        prev = None
        if pagination.has_prev:
            prev = url_for('admin_api.teachers', s_id=s_id, page=page-1, per_page=per_page, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('admin_api.teachers', s_id=s_id, page=page+1, per_page=per_page, _external=True)
        result = {
            'teachers': teachers,
            'prev': prev,
            'next': next,
            'count': pagination.total
        }
        return result, 200


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
            abort(404, message='教师不存在')
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


class StudentList(Resource):
    @marshal_with(student_paging_list, envelope='resource')
    @use_args(student_list)
    def get(self, args):
        s_id = args['school_id']
        page = args['page']
        per_page = args['per_page']
        if s_id == 0:
            pagination = Student.query.paginate(
                page=page, per_page=per_page, error_out=True
            )
        else:
            abort_if_scholl_doesnt_exist(s_id)
            school = School.query.get(s_id)
            pagination = school.students.paginate(
                page=page, per_page=per_page, error_out=True
            )
        students = pagination.items
        prev = None
        if pagination.has_prev:
            prev = url_for('admin_api.studentlist', s_id=s_id, page=page-1, per_page=per_page, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('admin_api.studentlist', s_id=s_id, page=page+1, per_page=per_page, _external=True)
        result = {
            'students': students,
            'prev': prev,
            'next': next,
            'count': pagination.total,
            'school_id': s_id
        }
        return result, 200


# 某学校的学生
class ScStudent(Resource):
    @marshal_with(scstudent_info, envelope='resource')
    def get(self, school_id, student_id):
        abort_if_scholl_doesnt_exist(school_id)
        abort_if_student_doesnt_exist(student_id)
        student = Student.query.get(student_id)
        if student.is_school_joined(school_id) is False:
            abort(404, message='该学校没有此学生')
        member_info = SchoolStudent.query.filter_by(
            school_id=school_id,
            student_id=student_id
        ).first()
        student.vip_times = member_info.vip_times
        student.nomal_times = member_info.nomal_times
        student.vip_expire = member_info.vip_expire
        student.join_timestamp = member_info.timestamp
        return student, 200


class Studentx(Resource):
    @marshal_with(student_info, envelope='resource')
    def get(self, id):
        student = Student.query.get(id)
        if student is None:
            abort(404, message='没有这个学生')
        return student, 200

    @marshal_with(student_info, envelope='resource')
    @use_args(student_args)
    def put(self, args, id):
        student = Student.query.get(id)
        if student is None:
            abort(404, message='没有这个学生')
        student.telephone = args['telephone']
        student.nickname = args['nickname']
        student.rename = args['rename']
        student.disabled = args['disabled']
        student.password = args['password']
        db.session.add(student)
        db.session.commit()
        return student, 201


class StudentSearch(Resource):
    @marshal_with(student_info, envelope='resource')
    @use_args(student_search)
    def get(self, args):
        student = Student.query.filter_by(telephone=args['telephone']).first()
        if student is None:
            abort(404, message='学生不存在')
        return student, 200


admin_api.add_resource(SchoolList, '/schools', endpoint='schools')
admin_api.add_resource(Schoolx, '/school/<int:id>', endpoint='school')
admin_api.add_resource(SchoolSearch, '/schools/search')

admin_api.add_resource(TeacherList, '/teachers', endpoint='teachers')
admin_api.add_resource(Teacherx, '/teacher/<int:id>', endpoint='teacher')
admin_api.add_resource(TeacherSearch, '/teachers/search')
admin_api.add_resource(DismissTeacher, '/dismiss')

admin_api.add_resource(StudentList, '/students', endpoint='studentlist')
admin_api.add_resource(ScStudent, '/<school_id>/student/<student_id>', endpoint='scstudent')
admin_api.add_resource(Studentx, '/student/<id>', endpoint='student')
admin_api.add_resource(StudentSearch, '/student/search')
