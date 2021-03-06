from datetime import datetime
from flask import g, url_for
from flask_restful import Resource, marshal_with, abort, fields as rfields
from webargs import fields, validate
from webargs.flaskparser import use_args
from ..models import Student, School, Ask, Answer, Topicimage, SchoolStudent, Teacher
from .. import db
from . import student_api


def abort_if_school_doesnt_exist(id):
    if School.query.get(id) is None:
        abort(404, code=0, message='学校不存在')


def abort_if_student_doesnt_exist(id):
    if Student.query.get(id) is None:
        abort(404, code=0, message='学生不存在')


def abort_if_ask_doesnt_exist(id):
    if Ask.query.get(id) is None:
        abort(404, code=0, message='问题不存在')


def abort_if_answer_doesnt_exist(id):
    if Answer.query.get(id) is None:
        abort(404, code=0, message='答案不存在')


def imgidsToimgs(o):
    imgs = []
    img_ids = o.img_ids
    if img_ids:
        img_list = img_ids.rsplit(',')
        for i in img_list:
            img = Topicimage.query.get(i)
            imgs.append(img.img_url)
    o.imgs = imgs
    return o


class Questions(Resource):
    ask_args = {
        'school_id': fields.Int(required=True),
        'ask_text': fields.Str(missing=None),
        'voice_url': fields.Str(missing=None),
        'voice_duration': fields.Int(missing=0),
        'img_ids': fields.Str(missing=None)
    }

    ask_list_args = {
        'school_id': fields.Int(required=True),
        'page': fields.Int(missing=1),
        'per_page': fields.Int(missing=10),
        'answered': fields.Int(validate=validate.OneOf([0, 1, 2]), missing=0)
    }

    answer_info = {
        'code': rfields.Integer,
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
        'code': rfields.Integer,
        'ask': rfields.Nested({
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
        })
    }

    ask_list_info = {
        'code': rfields.Integer,
        'asks': rfields.Nested({
            'id': rfields.Integer,
            'student_id': rfields.Integer,
            'school_id': rfields.Integer,
            'timestamp': rfields.DateTime(dt_format='iso8601'),
            'ask_text': rfields.String,
            'voice_url': rfields.String,
            'voice_duration': rfields.String,
            'imgs': rfields.List(rfields.String),
            'be_answered': rfields.Boolean,
            'answer_grate': rfields.Integer
        }),
        'prev': rfields.String(default=''),
        'next': rfields.String(default=''),
        'count': rfields.Integer
    }

    @marshal_with(ask_info)
    @use_args(ask_args)
    def post(self, args):
        s_id = args['school_id']
        abort_if_school_doesnt_exist(s_id)
        if g.student_user.is_school_joined(s_id) is False:
            abort(403, code=0, message='不是这个学校/机构的学生')
        if g.student_user.can_ask(s_id) is False:
            abort(403, code=0, message='你的提问次数已经用完了')
        imgs = []
        img_ids = args['img_ids']
        if img_ids:
            img_list = img_ids.rsplit(',')
            for i in img_list:
                img = Topicimage.query.get(i)
                if img is None:
                    abort(401, message='图片不存在')
                imgs.append(img.img_url)
        if not(args['ask_text'] or args['voice_url'] or img_ids):
            abort(400, code=0, message='没有提问任何问题')
        ask = Ask(
            school_id=s_id,
            student_id=g.student_user.id,
            ask_text=args['ask_text'],
            voice_url=args['voice_url'],
            voice_duration=args['voice_duration'],
            img_ids=img_ids
        )
        db.session.add(ask)
        db.session.commit()
        ask.imgs = imgs
        member_info = SchoolStudent.query.filter_by(
            school_id=s_id,
            student_id=g.student_user.id
        ).first()
        if member_info.vip_times > 0:
            member_info.vip_times -= 1
        else:
            member_info.nomal_times -= 1
        db.session.add(member_info)
        db.session.commit()
        result = {
            'code': 1,
            'ask': ask
        }
        return result, 200

    @marshal_with(ask_list_info)
    @use_args(ask_list_args)
    def get(self, args):
        s_id = args['school_id']
        page = args['page']
        per_page = args['per_page']
        answered = args['answered']
        abort_if_school_doesnt_exist(s_id)
        if g.student_user.is_school_joined(s_id) is False:
            abort(403, code=0, message='不是这个学校/机构的学生')
        # 全部
        if answered == 0:
            pagination = Ask.query.filter_by(
                school_id=s_id,
                student_id=g.student_user.id
            ).order_by(Ask.id.desc()).paginate(
                page=page, per_page=per_page, error_out=True
            )
        # 已回答
        if answered == 1:
            pagination = Ask.query.filter_by(
                school_id=s_id,
                student_id=g.student_user.id,
                be_answered=True
            ).order_by(Ask.id.desc()).paginate(
                page=page, per_page=per_page, error_out=True
            )
        # 未回答
        if answered == 2:
            pagination = Ask.query.filter_by(
                school_id=s_id,
                student_id=g.student_user.id,
                be_answered=False
            ).order_by(Ask.id.desc()).paginate(
                page=page, per_page=per_page, error_out=True
            )
        asks = pagination.items
        prev = None
        if pagination.has_prev:
            prev = url_for('student_api.asks', s_id=s_id, page=page-1, per_page=per_page)
        next = None
        if pagination.has_next:
            next = url_for('student_api.asks', s_id=s_id, page=page+1, per_page=per_page)

        for ask in asks:
            ask = imgidsToimgs(ask)
            '''
            imgs = []
            img_ids = ask.img_ids
            if img_ids:
                img_list = img_ids.rsplit(',')
                for i in img_list:
                    img = Topicimage.query.get(i)
                    imgs.append(img.img_url)
            ask.imgs = imgs
            '''

        result = {
            'code': 1,
            'asks': asks,
            'prev': prev,
            'next': next,
            'count': pagination.total
        }
        return result, 200


class Question(Resource):
    img_list = {
        'id': rfields.Integer,
        'img_url': rfields.String
    }

    answer_info = {
        'id': rfields.Integer,
        'student_id': rfields.Integer,
        'school_id': rfields.Integer,
        'teacher_id': rfields.Integer,
        'teacher_nickname': rfields.String,
        'teacher_imgurl': rfields.String(default=''),
        'student_nickname': rfields.String,
        'student_imgurl': rfields.String(default=''),
        'ask_id': rfields.Integer,
        'timestamp': rfields.DateTime(dt_format='iso8601'),
        'answer_text': rfields.String,
        'voice_url': rfields.String,
        'voice_duration': rfields.String,
        'imgs': rfields.List(rfields.String)
    }

    ask_info = {
        'code': rfields.Integer,
        'ask': rfields.Nested({
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
        })
    }

    @marshal_with(ask_info)
    def get(self, id):
        abort_if_ask_doesnt_exist(id)
        ask = Ask.query.get(id)
        if g.student_user.id != ask.student_id:
            abort(401, code=0, message='没有权限')
        ask = imgidsToimgs(ask)
        for answer in ask.answers:
            answer = imgidsToimgs(answer)
            teacher_id = answer.teacher_id
            if teacher_id:
                teacher = Teacher.query.get(teacher_id)
                answer.teacher_nickname = teacher.nickname
                answer.teacher_imgurl = teacher.imgurl
            student_id = answer.student_id
            if student_id:
                student = Student.query.get(student_id)
                answer.student_nickname = student.nickname
                answer.student_imgurl = student.imgurl
        result = {
            'code': 1,
            'ask': ask
        }
        return result, 200

    def delete(self, id):
        abort_if_ask_doesnt_exist(id)
        ask = Ask.query.get(id)
        if g.student_user.id != ask.student_id:
            abort(401, code=0, message='没有权限')
        db.session.delete(ask)
        db.session.commit()
        return '', 204


class StudentAnswers(Resource):
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
        st_id = ask.student_id
        if g.student_user.id != st_id:
            abort(401, code=0, message='没有权限')
        if ask.be_answered is False:
            abort(401, code=0, message='老师没有回答')
        imgs = []
        img_ids = args['img_ids']
        if img_ids:
            img_list = img_ids.rsplit(',')
            for i in img_list:
                img = Topicimage.query.get(i)
                if img is None:
                    abort(404, code=0, message='图片不存在')
                imgs.append(img.img_url)
        answer = Answer(
            student_id=g.student_user.id,
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
        st_id = ask.student_id
        if g.student_user.id != st_id:
            abort(401, code=0, message='没有权限')
        for answer in answers:
            answer = imgidsToimgs(answer)
            '''imgs = []
            img_ids = answer.img_ids
            if img_ids:
                img_list = img_ids.rsplit(',') 
                for i in img_list:
                    img = Topicimage.query.get(i)
                    imgs.append(img.img_url)
            answer.imgs = imgs'''
        return answers, 200

    def delete(self, answer_id):
        abort_if_answer_doesnt_exist(answer_id)
        answer = Answer.query.get(answer_id)
        if g.student_user.id != answer.student_id:
            abort(401, code=0, message='没有权限')
        ask = Ask.query.get(answer.ask_id)
        ask.answers.remove(answer)
        db.session.delete(answer)
        db.session.commit()
        return '', 204


class JoinSchool(Resource):
    def post(self, school_id):
        abort_if_school_doesnt_exist(school_id)
        if g.student_user.is_school_joined(school_id) is False:
            g.student_user.join_school(school_id)
            return '加入学校成功', 200
        return '用户已经是这个学校学生', 200


class AnswerGrate(Resource):

    grate_args = {
        'grate': fields.Int(validate=validate.OneOf([0, 1, 2]), required=True)
    }

    def get(self, ask_id):
        abort_if_ask_doesnt_exist(ask_id)
        ask = Ask.query.get(ask_id)
        if g.student_user.id != ask.student_id:
            abort(403, code=0, message='没有权限')
        grate_value = ask.answer_grate
        return {'code': 1, 'grate_value': grate_value}, 200

    @use_args(grate_args)
    def put(self, args, ask_id):
        abort_if_ask_doesnt_exist(ask_id)
        ask = Ask.query.get(ask_id)
        if g.student_user.id != ask.student_id:
            abort(403, code=0, message='没有权限')
        if not ask.be_answered:
            abort(400, code=0, message='没有被回答')
        ask.answer_grate = args['grate']
        db.session.add(ask)
        db.session.commit()
        return {'code': 1}, 201


class SchoolInfo(Resource):

    school_info = {
        'code': rfields.Integer,
        'school': rfields.Nested({
            'id': rfields.Integer,
            'name': rfields.String,
            'intro': rfields.String
        }),
        'course': rfields.Nested({
            'id': rfields.Integer,
            'course_name': rfields.String,
            'course_intro': rfields.String
        })
    }

    @marshal_with(school_info)
    def get(self, school_id):
        abort_if_school_doesnt_exist(school_id)
        if g.student_user.is_school_joined(school_id) is False:
            abort(403, code=0, message='不是这个学校/机构的学生')
        school = School.query.get(school_id)
        course = school.courses.all()[0]
        result = {
            'code': 1,
            'school': school,
            'course': course
        }
        return result, 200


class StudentInSchoolInfo(Resource):

    school_args = {
        'school_id': fields.Int(required=True)
    }

    student_info = {
        'code': rfields.Integer,
        'student_id': rfields.Integer,
        'nickname': rfields.String,
        'imgurl': rfields.String,
        'vip_expire': rfields.DateTime(dt_format='iso8601'),
        'vip_status': rfields.Boolean,
        'real_times': rfields.Integer,
        'asks_count': rfields.Integer,
        'vip_times': rfields.Integer,
        'nomal_times': rfields.Integer,
        'timestamp': rfields.DateTime(dt_format='iso8601')
    }

    @marshal_with(student_info)
    @use_args(school_args)
    def get(self, args, student_id):
        school_id = args['school_id']
        abort_if_student_doesnt_exist(student_id)
        abort_if_school_doesnt_exist(school_id)
        student = Student.query.get(student_id)
        if student.is_school_joined(school_id) is False:
            abort(403, code=0, message='不是这个学校/机构的学生')
        member_info = SchoolStudent.query.filter_by(
            school_id=school_id,
            student_id=student_id
        ).first()
        vip_expire = member_info.vip_expire
        vip_times = member_info.vip_times
        nomal_times = member_info.nomal_times
        real_times = nomal_times
        vip_status = False
        if member_info.vip_expire > datetime.utcnow():
            vip_status = True
            nomal_times = vip_times + nomal_times
            if vip_expire == -1:
                real_times = -1
        asks_count = db.session.query(Ask).filter_by(
            school_id=school_id,
            student_id=student_id
        ).count()
        result = {
            'code': 1,
            'student_id': student_id,
            'nickname': student.nickname,
            'imgurl': student.imgurl,
            'vip_expire': vip_expire,
            'vip_status': vip_status,
            'vip_times': member_info.vip_times,
            'nomal_times': member_info.nomal_times,
            'real_times': real_times,
            'asks_count': asks_count,
            'timestamp': member_info.timestamp
        }
        return result, 200


student_api.add_resource(Questions, '/asks', endpoint='asks')
student_api.add_resource(Question, '/ask/<id>', endpoint='ask')

student_api.add_resource(StudentAnswers, '/ask/<ask_id>/answers', endpoint='answers')
student_api.add_resource(StudentAnswers, '/ask/answers/<answer_id>')

student_api.add_resource(JoinSchool, '/joinschool/<school_id>')
student_api.add_resource(AnswerGrate, '/ask/<ask_id>/answergrate')

student_api.add_resource(SchoolInfo, '/school/<school_id>')

student_api.add_resource(StudentInSchoolInfo, '/<student_id>')
