from flask import g, url_for
from datetime import datetime
from flask_restful import Resource, marshal_with, abort, fields as rfields
from webargs import fields, validate
from webargs.flaskparser import use_args
from ..models import Teacher, School, Student, SchoolStudent, Ask, Answer, Topicimage
from .. import db
from . import school_api


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

student_update = {
    'vip_times': fields.Int(missing=-1, validate=lambda x: x >= -1),
    'nomal_times': fields.Int(missing=0, validate=lambda x: x >= 0),
    'vip_expire': fields.DateTime(missing=datetime.utcnow().isoformat())
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
        'telephone': rfields.String,
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
    'telephone': rfields.String,
    'gender': rfields.Integer,
    'answercount': rfields.Integer
}

student_paging_list = {
    'students': rfields.Nested({
        'id': rfields.Integer,
        'nickname': rfields.String,
        'rename': rfields.String,
        'telephone': rfields.String,
        'imgurl': rfields.String,
        'fromwhere': rfields.String,
        'timestamp': rfields.DateTime(dt_format='iso8601'),
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
    'telephone': rfields.String,
    'imgurl': rfields.String,
    'fromwhere': rfields.String,
    'timestamp': rfields.DateTime(dt_format='iso8601'),
    'disabled': rfields.Boolean,
    'expevalue': rfields.Integer,
    'vip_times': rfields.Integer,
    'nomal_times': rfields.Integer,
    'vip_expire': rfields.DateTime(dt_format='iso8601'),
    'join_timestamp': rfields.DateTime(dt_format='iso8601')
}


def abort_if_school_doesnt_exist(id):
    if School.query.get(id) is None:
        abort(404, message='学校不存在')


def abort_if_teacher_doesnt_exist(id):
    if Teacher.query.get(id) is None:
        abort(404, message='教师不存在')


def abort_if_student_doesnt_exist(id):
    if Student.query.get(id) is None:
        abort(404, message='学生不存在')


def abort_if_ask_doesnt_exist(id):
    if Ask.query.get(id) is None:
        abort(404, message='问题不存在')


def abort_if_answer_doesnt_exist(id):
    if Answer.query.get(id) is None: 
        abort(404, message='答案不存在')


class Coursex(Resource):
    @marshal_with(course_info, envelope='resource')
    @use_args(course_set)
    def put(self, args):
        s_id = args['school_id']
        c_name = args['course_name']
        c_intro = args['course_intro']
        n_times = args['nomal_times']
        v_times = args['vip_times']
        abort_if_school_doesnt_exist(s_id)
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

    @marshal_with(course_info, envelope='resource')
    @use_args(course_get)
    def get(self, args):
        s_id = args['school_id']
        abort_if_school_doesnt_exist(s_id)
        if g.teacher_user.is_employ(s_id) is False:
            abort(401, message='你不是这个学校的老师')
        course = School.query.get(9).courses.first()
        return course, 200


class SchoolDetail(Resource):
    @marshal_with(school_info, envelope='resource')
    def get(self, s_id):
        abort_if_school_doesnt_exist(s_id)
        if g.teacher_user.is_employ(s_id) is False:
            abort(401, message='不是这个学校的老师')
        school = School.query.get(s_id)
        school.teacherslist = school.teachers.all()
        school.teachercount = school.teachers.count()
        school.studentcount = school.students.count()
        return school, 200


class TeacherDetail(Resource):
    @marshal_with(teacher_info, envelope='resource')
    def get(self, s_id, t_id):
        abort_if_teacher_doesnt_exist(t_id)
        abort_if_school_doesnt_exist(s_id)
        if g.teacher_user.is_employ(s_id) is False:
            abort(401, message='你不是这个学校的老师')
        teacher = Teacher.query.get(t_id)
        if teacher.is_employ(s_id) is False:
            abort(401, message='他/她不是这里的老师')
        teacher.answerscount = teacher.answers.count()
        return teacher, 200


class DismissTeacher(Resource):
    @use_args(dismiss_teacher)
    def delete(self, args):
        s_id = args['school_id']
        t_id = args['teacher_id']
        abort_if_school_doesnt_exist(s_id)
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
    @use_args(teacher_dismiss)
    def delete(self, args):
        s_id = args['school_id']
        abort_if_school_doesnt_exist(s_id)
        if g.teacher_user.is_employ(s_id) is False:
            abort(401, message='你不是这里的老师')
        g.teacher_user.dismiss_school(s_id)
        return '', 204


class StudentList(Resource):
    @marshal_with(student_paging_list, envelope='resource')
    @use_args(student_list)
    def get(self, args, s_id):
        abort_if_school_doesnt_exist(s_id)
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
            prev = url_for('school_api.studentlist', s_id=s_id, page=page-1, per_page=per_page)
        next = None
        if pagination.has_next:
            next = url_for('school_api.studentlist', s_id=s_id, page=page+1, per_page=per_page)
        result = {
            'students': students,
            'prev': prev,
            'next': next,
            'count': pagination.total
        }
        return result, 200


class Studentx(Resource):
    @marshal_with(student_info, envelope='resource')
    def get(self, school_id, student_id):
        if g.teacher_user.is_employ(school_id) is False:
            abort(401, message='你不是这里的老师')
        abort_if_school_doesnt_exist(school_id)
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

    @marshal_with(student_info, envelope='resource')
    @use_args(student_update)
    def put(self, args, school_id, student_id):
        if g.teacher_user.is_employ(school_id) is False:
            abort(401, message='你不是这里的老师')
        abort_if_school_doesnt_exist(school_id)
        abort_if_student_doesnt_exist(student_id)
        student = Student.query.get(student_id)
        if student.is_school_joined is False:
            abort(401, message='该学校没有此学生')
        member_info = SchoolStudent.query.filter_by(
            school_id=school_id,
            student_id=student_id
        ).first()
        member_info.vip_times = args['vip_times']
        member_info.nomal_times = args['nomal_times']
        member_info.vip_expire = args['vip_expire']
        db.session.add(member_info)
        db.session.commit()
        student.vip_times = member_info.vip_times
        student.nomal_times = member_info.nomal_times
        student.vip_expire = member_info.vip_expire
        student.join_timestamp = member_info.timestamp
        return student, 201


class Questions(Resource):

    ask_list_args = {
        'school_id': fields.Int(required=True),
        'student_id': fields.Int(missing='0'),
        'page': fields.Int(missing=1),
        'per_page': fields.Int(missing=10),
        'answered': fields.Int(validate=validate.OneOf([0, 1, 2]), missing=0)
    }

    answer_info = {
        'id': rfields.Integer,
        'student_id': rfields.Integer,
        'school_id': rfields.Integer,
        'teacher_id': rfields.Integer,
        'ask_id': rfields.Integer,
        'timestamp': rfields.DateTime(dt_format='iso8601'),
        'ask_text': rfields.String,
        'voice_url': rfields.String,
        'voice_duration': rfields.String,
        'imgs': rfields.List(rfields.String)
    }

    ask_info = {
        'id': rfields.Integer,
        'student_id': rfields.Integer,
        'school_id': rfields.Integer,
        'timestamp': rfields.DateTime(dt_format='iso8601'),
        'ask_text': rfields.String,
        'voice_url': rfields.String,
        'voice_duration': rfields.String,
        'imgs': rfields.List(rfields.String),
        'answers': rfields.Nested(answer_info),
        'be_answered': rfields.Boolean,
        'answer_grate': rfields.Integer
    }

    ask_list_info = {
        'asks': rfields.Nested(ask_info),
        'prev': rfields.String,
        'next': rfields.String,
        'count': rfields.Integer
    }

    @marshal_with(ask_list_info)
    @use_args(ask_list_args)
    def get(self, args):
        sc_id = args['school_id']
        st_id = args['student_id']
        page = args['page']
        per_page = args['per_page']
        answered = args['answered']
        abort_if_school_doesnt_exist(sc_id)
        if g.teacher_user.is_employ(sc_id) is False:
            abort(401, message='你不是这里的老师')
        if st_id == 0:
            if answered == 0:
                pagination = Ask.query.filter_by(school_id=sc_id).paginate(
                    page=page, per_page=per_page, error_out=True
                )
            if answered == 1:
                pagination = Ask.query.filter_by(
                    school_id=sc_id, be_answered=False
                ).paginate(
                    page=page, per_page=per_page, error_out=True
                )
            if answered == 2:
                pagination = Ask.query.filter_by(
                    school_id=sc_id, be_answered=True
                ).paginate(
                    page=page, per_page=per_page, error_out=True
                )
        else:
            abort_if_student_doesnt_exist(st_id)
            student = Student.query.get(st_id)
            if student.is_school_joined(sc_id) is False:
                abort(401, message='不是这个学校/机构的学生')
            if answered == 0:
                pagination = Ask.query.filter_by(
                    school_id=sc_id,
                    student_id=st_id
                ).paginate(
                    page=page, per_page=per_page, error_out=True
                )
            if answered == 1:
                pagination = Ask.query.filter_by(
                    school_id=sc_id,
                    student_id=st_id,
                    be_answered=False
                ).paginate(
                    page=page, per_page=per_page, error_out=True
                )
            if answered == 2:
                pagination = Ask.query.filter_by(
                    school_id=sc_id,
                    student_id=st_id,
                    be_answered=True
                ).paginate(
                    page=page, per_page=per_page, error_out=True
                )
        asks = pagination.items
        prev = None
        if pagination.has_prev:
            prev = url_for('school_api.asks', sc_id=sc_id, st_id=st_id, page=page-1, per_page=per_page)
        next = None
        if pagination.has_next:
            next = url_for('school_api.asks', sc_id=sc_id, st_id=st_id, page=page+1, per_page=per_page)
        for ask in asks:
            img_ids = ask.img_ids
            img_list = img_ids.rsplit(',')
            imgs = []
            for i in img_list:
                img = Topicimage.query.get(i)
                imgs.append(img.img_url)
            ask.imgs = imgs
        result = {
            'asks': asks,
            'prev': prev,
            'next': next,
            'count': pagination.total
        }
        return result, 200


class Question(Resource):

    answer_info = {
        'id': rfields.Integer,
        'student_id': rfields.Integer,
        'school_id': rfields.Integer,
        'teacher_id': rfields.Integer,
        'ask_id': rfields.Integer,
        'timestamp': rfields.DateTime(dt_format='iso8601'),
        'ask_text': rfields.String,
        'voice_url': rfields.String,
        'voice_duration': rfields.String,
        'imgs': rfields.List(rfields.String)
    }

    ask_info = {
        'id': rfields.Integer,
        'student_id': rfields.Integer,
        'school_id': rfields.Integer,
        'timestamp': rfields.DateTime(dt_format='iso8601'),
        'ask_text': rfields.String,
        'voice_url': rfields.String,
        'voice_duration': rfields.String,
        'imgs': rfields.List(rfields.String),
        'answers': rfields.Nested(answer_info),
        'be_answered': rfields.Boolean,
        'answer_grate': rfields.Integer
    }

    @marshal_with(ask_info)
    def get(self, id):
        abort_if_ask_doesnt_exist(id)
        ask = Ask.query.get(id)
        if g.teacher_user.is_employ(ask.school_id) is False:
            abort(401, message='你不是这里的老师')
        img_ids = ask.img_ids
        img_list = img_ids.rsplit(',')
        imgs = []
        for i in img_list:
            img = Topicimage.query.get(i)
            imgs.append(img.img_url)
        ask.imgs = imgs
        return ask, 200


class TeacherAnswers(Resource):

    answer_args = {
        'answer_text': fields.Str(required=True),
        'voice_url': fields.Str(missing=None),
        'voice_duration': fields.Str(missing=None),
        'img_ids': fields.Str(missing=None)
    }

    answer_info = {
        'id': rfields.Integer,
        'student_id': rfields.Integer,
        'teacher_id': rfields.Integer,
        'ask_id': rfields.Integer,
        'timestamp': rfields.DateTime(dt_format='iso8601'),
        'answer_text': rfields.String,
        'voice_url': rfields.String,
        'voice_duration': rfields.String,
        'imgs': rfields.List(rfields.String)
    }

    @marshal_with(answer_info)
    @use_args(answer_args)
    def post(self, args, ask_id):
        a_id = ask_id
        abort_if_ask_doesnt_exist(a_id)
        ask = Ask.query.get(a_id)
        sc_id = ask.school_id
        if g.teacher_user.is_employ(sc_id) is False:
            abort(401, message='没有权限')
        img_ids = args['img_ids']
        img_list = img_ids.rsplit(',')
        imgs = []
        for i in img_list:
            img = Topicimage.query.get(i)
            if img is None:
                abort(401, message='图片不存在')
            imgs.append(img.img_url)
        answer = Answer(
            teacher_id=g.teacher_user.id,
            answer_text=args['answer_text'],
            voice_url=args['voice_url'],
            voice_duration=args['voice_duration'],
            img_ids=img_ids
        )
        ask.answers.append(answer)
        db.session.add(answer)
        db.session.commit()
        answer.imgs = imgs
        return answer, 200

    @marshal_with(answer_info)
    def get(self, ask_id):
        abort_if_ask_doesnt_exist(ask_id)
        answers = Ask.query.get(ask_id).answers
        ask = Ask.query.get(ask_id)
        sc_id = ask.school_id
        if g.teacher_user.is_employ(sc_id) is False:
            abort(401, message='没有权限')
        for answer in answers:
            img_ids = answer.img_ids
            img_list = img_ids.rsplit(',')
            imgs = []
            for i in img_list:
                img = Topicimage.query.get(i)
                imgs.append(img.img_url)
            answer.imgs = imgs
        return answers, 200

    def delete(self, answer_id):
        abort_if_answer_doesnt_exist(answer_id)
        answer = Answer.query.get(answer_id)
        if g.teacher_user.id != answer.teacher_id:
            abort(401, message='没有权限')
        ask = Ask.query.get(answer.ask_id)
        ask.answers.remove(answer)
        db.session.delete(answer)
        db.session.commit()
        return '', 204


school_api.add_resource(Coursex, '/course', endpoint='course')

school_api.add_resource(SchoolDetail, '/<s_id>', endpoint='school')
school_api.add_resource(TeacherDetail, '/<s_id>/teacher/<t_id>', endpoint='teacher')
school_api.add_resource(DismissTeacher, '/dismiss')
school_api.add_resource(TeacherDismiss, '/teacher/dismiss')

school_api.add_resource(StudentList, '/<s_id>/students', endpoint='studentlist')
school_api.add_resource(Studentx, '/<school_id>/student/<student_id>', endpoint='student')

school_api.add_resource(Questions, '/student/asks', endpoint='asks')
school_api.add_resource(Question, '/student/ask/<id>', endpoint='ask')

school_api.add_resource(TeacherAnswers, '/student/ask/<ask_id>/answers', endpoint='answers')
school_api.add_resource(TeacherAnswers, '/student/answers/<answer_id>')
