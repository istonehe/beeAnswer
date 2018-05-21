from flask import g
from flask_restful import Resource, marshal_with, fields as flask_restful
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Answer, Student, Teacher
from .. import db
from . import student_api


class AskQuestion(Resource):
    question_info = {
        'school_id': fields.Int(required=True),
        'student_id': fields.Int(required=True),
        'ask_text': fields.Str(required=True),
        'voice_url': fields.Str(missing=None),
        'voice_duration': fields.Str(missing=None),
        'img_ids': fields.Str(missing=None)
    }

    @use_args(question_info)
    def post(self, args):
        img_ids = args['img_ids']
        img_list = img_ids.rsplit(',')
        answer = Answer(
            school_id=args['school_id'],
            student_id=args['student_id'],
            ask_text=args['ask_text'],
            voice_url=args['voice_url'],
            voice_duration=args['voice_duration']
        )
        db.session.add(answer)
        db.session.commit()
        for i in img_list:
            img[i] = Topicimage.query.get(i)
            img[i].answer_id = answer.id
        db.session.add(img)
        db.session.commit()
        

class Testtt(Resource):
    test_args = {
        'kaca': fields.Str(missing=None)
    }

    @use_args(test_args)
    def post(self, args):
        return args['kaca']


student_api.add_resource(AskQuestion, '/ask')

student_api.add_resource(Testtt, '/test')
