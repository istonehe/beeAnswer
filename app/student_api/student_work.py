from flask import g
from flask_restful import Resource, marshal_with, abort, fields as rfields
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Student, School, Teacher, Ask, Answer, Topicimage
from .. import db
from . import student_api


def abort_if_scholl_doesnt_exist(id):
    if School.query.get(id) is None:
        abort(404, message='学校不存在')


def abort_if_student_doesnt_exist(id):
    if Student.query.get(id) is None:
        abort(404, message='学生不存在')


class AskQuestion(Resource):
    ask_args = {
        'school_id': fields.Int(required=True),
        'ask_text': fields.Str(required=True),
        'voice_url': fields.Str(missing=None),
        'voice_duration': fields.Str(missing=None),
        'img_ids': fields.Str(missing=None)
    }

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
        'topicimages': rfields.Nested(img_list),
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
        'topicimages': rfields.Nested(img_list),
        'answers': rfields.Nested(answer_info)
    }

    @marshal_with(ask_info)
    @use_args(ask_args)
    def post(self, args):
        s_id = args['school_id']
        abort_if_scholl_doesnt_exist(s_id)
        if g.student_user.is_school_joined(s_id) is False:
            abort(401, message='学生没有加入学校')
        if g.student_user.can_ask(s_id) is False:
            abort(401, message='你的提问次数已经用完了')
        img_ids = args['img_ids']
        img_list = img_ids.rsplit(',')
        ask = Ask(
            school_id=s_id,
            student_id=g.student_user.id,
            ask_text=args['ask_text'],
            voice_url=args['voice_url'],
            voice_duration=args['voice_duration']
        )
        db.session.add(ask)
        db.session.commit()
        imgs = []
        for i in img_list:
            img = Topicimage.query.get(i)
            img.ask_id = ask.id
            imgs.append(img)
        db.session.add_all(imgs)
        db.session.commit()
        
        return ask, 200
        

class Testtt(Resource):
    test_args = {
        'kaca': fields.Str(missing=None)
    }

    @use_args(test_args)
    def post(self, args):
        return args['kaca']


student_api.add_resource(AskQuestion, '/ask')

student_api.add_resource(Testtt, '/test')
