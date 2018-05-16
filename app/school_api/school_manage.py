from flask import g
from flask_restful import Resource, marshal_with, abort, fields as rfields
from flask_httpauth import HTTPBasicAuth
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Teacher, School
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

# marshal_with
course_info = {
    'id': rfields.Integer,
    'course_name': rfields.String,
    'course_intro': rfields.String,
    'nomal_times': rfields.Integer,
    'vip_times': rfields.Integer
}


def abort_if_scholl_doesnt_exist(id):
    if School.query.get(id) is None:
        abort(404, message='学校不存在')


class Coursex(Resource):
    @auth.login_required
    @marshal_with(course_info, envelope='resource')
    @use_args(course_set)
    def put(self, args):
        s_id = args['school_id']
        c_name = args['course_id']
        c_intro = args['course_intro']
        n_times = args['nomal_times']
        v_times = args['vip_times']
        abort_if_scholl_doesnt_exist(s_id)
        if g.current_user.is_teacher_admin(s_id) is False:
            abort(401, message='没有学校管理员权限')
        course = School.query.get(9).courses.first()
        course.course_name = c_name
        course.course_intro = c_intro
        course.nomal_times = n_times
        course.vip_times = v_times
        db.session.add(course)
        db.session.commit()
        return course, 201


school_api.add_resource(Coursex, '/course', endpoint='coures')