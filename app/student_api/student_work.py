from flask import g, url_for
from flask_restful import Resource, marshal_with, abort, fields as rfields
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Student, School, Teacher, Ask, Answer, Topicimage, SchoolStudent
from .. import db
from . import student_api


def abort_if_school_doesnt_exist(id):
    if School.query.get(id) is None:
        abort(404, message='学校不存在')


def abort_if_student_doesnt_exist(id):
    if Student.query.get(id) is None:
        abort(404, message='学生不存在')


def abort_if_ask_doesnt_exist(id):
    if Ask.query.get(id) is None:
        abort(404, message='问题不存在')


class Questions(Resource):
    ask_args = {
        'school_id': fields.Int(required=True),
        'ask_text': fields.Str(required=True),
        'voice_url': fields.Str(missing=None),
        'voice_duration': fields.Str(missing=None),
        'img_ids': fields.Str(missing=None)
    }

    ask_list_args = {
        'school_id': fields.Int(required=True),
        'page': fields.Int(missing=1),
        'per_page': fields.Int(missing=10)
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
        'imgs': rfields.List(rfields.String),
        'answer_rate': rfields.Integer
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
        'be_answered': rfields.Boolean
    }

    ask_list_info = {
        'asks': rfields.Nested(ask_info),
        'prev': rfields.String,
        'next': rfields.String,
        'count': rfields.Integer
    }

    @marshal_with(ask_info)
    @use_args(ask_args)
    def post(self, args):
        s_id = args['school_id']
        abort_if_school_doesnt_exist(s_id)
        if g.student_user.is_school_joined(s_id) is False:
            abort(401, message='不是这个学校/机构的学生')
        if g.student_user.can_ask(s_id) is False:
            abort(401, message='你的提问次数已经用完了')
        img_ids = args['img_ids']
        img_list = img_ids.rsplit(',')
        imgs = []
        for i in img_list:
            img = Topicimage.query.get(i)
            if img is None:
                abort(401, message='图片不存在')
            imgs.append(img.img_url)
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
        return ask, 200

    @marshal_with(ask_list_info)
    @use_args(ask_list_args)
    def get(self, args):
        s_id = args['school_id']
        page = args['page']
        per_page = args['per_page']
        abort_if_school_doesnt_exist(s_id)
        if g.student_user.is_school_joined(s_id) is False:
            abort(401, message='不是这个学校/机构的学生')
        pagination = Ask.query.filter_by(
            school_id=s_id,
            student_id=g.student_user.id
        ).paginate(
            page=page, per_page=per_page, error_out=True
        )
        asks = pagination.items
        prev = None
        if pagination.has_prev:
            prev = url_for('student_api.questions', s_id=s_id, page=page-1, per_page=per_page)
        next = None
        if pagination.has_next:
            next = url_for('student_api.asks', s_id=s_id, page=page+1, per_page=per_page)

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
    img_list = {
        'id': rfields.Integer,
        'img_url': rfields.String
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
        'imgs': rfields.List(rfields.String),
        'answer_rate': rfields.Integer
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
        'be_answered': rfields.Boolean
    }

    @marshal_with(ask_info)
    def get(self, id):
        abort_if_ask_doesnt_exist(id)
        ask = Ask.query.get(id)
        if g.student_user.id != ask.student_id:
            abort(401, message='没有权限')
        img_ids = ask.img_ids
        img_list = img_ids.rsplit(',')
        imgs = []
        for i in img_list:
            img = Topicimage.query.get(i)
            imgs.append(img.img_url)
        ask.imgs = imgs
        return ask, 200

    def delete(self, id):
        abort_if_ask_doesnt_exist(id)
        ask = Ask.query.get(id)
        if g.student_user.id != ask.student_id:
            abort(401, message='没有权限')
        db.session.delete(ask)
        db.session.commit()
        return '', 204


class Testtt(Resource):
    test_args = {
        'kaca': fields.Str(missing=None)
    }

    @use_args(test_args)
    def post(self, args):
        return args['kaca']


student_api.add_resource(Questions, '/asks', endpoint='asks')
student_api.add_resource(Question, '/ask/<id>', endpoint='ask')

student_api.add_resource(Testtt, '/test')
