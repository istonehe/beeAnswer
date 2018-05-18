from flask import g, url_for
from flask_restful import Resource, marshal_with, abort, fields as rfields
from flask_httpauth import HTTPBasicAuth
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Teacher, School, Student, SchoolStudent
from .. import db
from . import school_api

auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username_or_token, password):
    teacher_user = Teacher.verify_auth_token(username_or_token)
    if not teacher_user:
        teacher_user = Teacher.query.filter_by(telephone=username_or_token).first()
        if not teacher_user or not teacher_user.verify_password(password):
            return False
    g.teacher_user = teacher_user
    return True


# use_args
course_set = {
    'school_id': fields.Int(required=True),
    'course_name': fields.Str(required=True),
    'course_intro': fields.Str(missing=' '),
    'nomal_times': fields.Int(missing=5, validate=lambda x: x >= 0),
    'vip_times': fields.Int(missing=-1, validate=lambda x: x >= -1)
}

course_get = {
    'school_id': fields.Int(required=True)
}

dismiss_teacher = {
    'school_id': fields.Int(required=True),
    'teacher_id': fields.Int(required=True)
}

teacher_dismiss = {
    'school_id': fields.Int(required=True)
}

student_list = {
    'page': fields.Int(missing=1),
    'per_page': fields.Int(missing=10)
}


# marshal_with
course_info = {
    'id': rfields.Integer,
    'course_name': rfields.String,
    'course_intro': rfields.String,
    'nomal_times': rfields.Integer,
    'vip_times': rfields.Integer
}

school_info = {
    'id': rfields.Integer,
    'name': rfields.String,
    'intro': rfields.String,
    'teachercount': rfields.Integer,
    'studentcount': rfields.Integer,
    'teacherslist': rfields.Nested({
        'id': rfields.Integer,
        'nickname': rfields.String,
        'rename': rfields.String,
        'intro': rfields.String,
        'imgurl': rfields.String,
        'email': rfields.String,
        'telephone': rfields.Integer,
        'gender': rfields.Integer
    })
}

teacher_info = {
    'id': rfields.Integer,
    'nickname': rfields.String,
    'rename': rfields.String,
    'intro': rfields.String,
    'imgurl': rfields.String,
    'email': rfields.String,
    'telephone': rfields.Integer,
    'gender': rfields.Integer,
    'answercount': rfields.Integer
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

student_info = {
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


def abort_if_scholl_doesnt_exist(id):
    if School.query.get(id) is None:
        abort(404, message='学校不存在')


def abort_if_teacher_doesnt_exist(id):
    if Teacher.query.get(id) is None:
        abort(404, message='教师不存在')


def abort_if_student_doesnt_exist(id):
    if Student.query.get(id) is None:
        abort(404, message='学生不存在')


class Coursex(Resource):
    @auth.login_required
    @marshal_with(course_info, envelope='resource')
    @use_args(course_set)
    def put(self, args):
        s_id = args['school_id']
        c_name = args['course_name']
        c_intro = args['course_intro']
        n_times = args['nomal_times']
        v_times = args['vip_times']
        abort_if_scholl_doesnt_exist(s_id)
        if g.teacher_user.is_teacher_admin(s_id) is False:
            abort(401, message='没有学校管理员权限')
        course = School.query.get(9).courses.first()
        course.course_name = c_name
        course.course_intro = c_intro
        course.nomal_times = n_times
        course.vip_times = v_times
        db.session.add(course)
        db.session.commit()
        return course, 201

    @auth.login_required
    @marshal_with(course_info, envelope='resource')
    @use_args(course_get)
    def get(self, args):
        s_id = args['school_id']
        abort_if_scholl_doesnt_exist(s_id)
        if g.teacher_user.is_employ(s_id) is False:
            abort(401, message='你不是这个学校的老师')
        course = School.query.get(9).courses.first()
        return course, 200


class SchoolDetail(Resource):
    @auth.login_required
    @marshal_with(school_info, envelope='resource')
    def get(self, s_id):
        abort_if_scholl_doesnt_exist(s_id)
        if g.teacher_user.is_employ(s_id) is False:
            abort(401, message='不是这个学校的老师')
        school = School.query.get(s_id)
        school.teacherslist = school.teachers.all()
        school.teachercount = school.teachers.count()
        school.studentcount = school.students.count()
        return school, 200


class TeacherDetail(Resource):
    @auth.login_required
    @marshal_with(teacher_info, envelope='resource')
    def get(self, s_id, t_id):
        abort_if_teacher_doesnt_exist(t_id)
        abort_if_scholl_doesnt_exist(s_id)
        if g.teacher_user.is_employ(s_id) is False:
            abort(401, message='你不是这个学校的老师')
        teacher = Teacher.query.get(t_id)
        if teacher.is_employ(s_id) is False:
            abort(401, message='他/她不是这里的老师')
        teacher.answerscount = teacher.answers.count()
        return teacher, 200


class DismissTeacher(Resource):
    @auth.login_required
    @use_args(dismiss_teacher)
    def delete(self, args):
        s_id = args['school_id']
        t_id = args['teacher_id']
        abort_if_scholl_doesnt_exist(s_id)
        abort_if_teacher_doesnt_exist(t_id)
        school = School.query.get(s_id)
        if g.teacher_user.is_teacher_admin(s_id) is False:
            abort(401, message='没有学校管理员权限')
        teacher = Teacher.query.get(t_id)
        if teacher.telephone == school.admin:
            abort(401, message='不能移除自己')
        if teacher.is_employ(s_id) is False:
            abort(401, message='他/她不是这里的老师')
        teacher.dismiss_school(s_id)
        return '', 204


class TeacherDismiss(Resource):
    @auth.login_required
    @use_args(teacher_dismiss)
    def delete(self, args):
        s_id = args['school_id']
        abort_if_scholl_doesnt_exist(s_id)
        if g.teacher_user.is_employ(s_id) is False:
            abort(401, message='你不是这里的老师')
        g.teacher_user.dismiss_school(s_id)
        return '', 204


class StudentList(Resource):
    @auth.login_required
    @marshal_with(student_paging_list, envelope='resource')
    @use_args(student_list)
    def get(self, args, s_id):
        abort_if_scholl_doesnt_exist(s_id)
        page = args['page']
        per_page = args['per_page']
        if g.teacher_user.is_employ(s_id) is False:
            abort(401, message='你不是这里的老师')
        school = School.query.get(s_id)
        pagination = school.students.paginate(
            page=page, per_page=per_page, error_out=True
        )
        students = pagination.items
        prev = None
        if pagination.has_prev:
            prev = url_for('school_api.studentlist', s_id=s_id, page=page-1, per_page=per_page, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('school_api.studentlist', s_id=s_id, page=page+1, per_page=per_page, _external=True)
        result = {
            'students': students,
            'prev': prev,
            'next': next,
            'count': pagination.total
        }
        return result, 200


class Studentx(Resource):
    @auth.login_required
    @marshal_with(student_info, envelope='resource')
    def get(self, school_id, student_id):
        if g.teacher_user.is_employ(school_id) is False:
            abort(401, message='你不是这里的老师')
        abort_if_scholl_doesnt_exist(school_id)
        abort_if_student_doesnt_exist(student_id)
        student = Student.query.get(student_id)
        if student.is_school_joined is False:
            abort(401, message='该学校没有此学生')
        member_info = SchoolStudent.query.filter_by(
            school_id=school_id,
            student_id=student_id
        ).first()
        student.vip_times = member_info.vip_times
        student.nomal_times = member_info.nomal_times
        student.vip_expire = member_info.vip_expire
        student.join_timestamp = member_info.timestamp
        return student, 200


school_api.add_resource(Coursex, '/course', endpoint='course')

school_api.add_resource(SchoolDetail, '/<s_id>', endpoint='school')
school_api.add_resource(TeacherDetail, '/<s_id>/teacher/<t_id>', endpoint='teacher')
school_api.add_resource(DismissTeacher, '/dismiss')
school_api.add_resource(TeacherDismiss, '/teacher/dismiss')

school_api.add_resource(StudentList, '/<s_id>/students', endpoint='studentlist')
school_api.add_resource(Studentx, '/<school_id>/student/<student_id>', endpoint='student')
