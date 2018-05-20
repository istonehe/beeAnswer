from flask import g
from flask_restful import Resource, marshal_with, fields as flask_restful
from webargs import fields
from webargs.flaskparser import use_args
from . import student_api 


class AskQuestion(Resource):
    qestion_info = {
        'school_id': fields.Int(required=True),
        'ask_text': fields.Str(),
        'voice_url': fields.Str(),
        'voice_duration': fields.Str()
    }

    @use_args(qestion_info)
    def post(self, args):
        pass


student_api.add_resource(AskQuestion, '/ask')
