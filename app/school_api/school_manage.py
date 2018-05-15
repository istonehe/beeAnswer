from flask import g
from flask_restful import Resource, marshal_with, fields as rfields
from flask_httpauth import HTTPBasicAuth
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Teacher
from .. import db
from . import school_api

auth = HTTPBasicAuth()


class CourseList(Resource):
    def post(self, args):
        pass


school_api.add_resource(CourseList, '/course', endpoint='coures')