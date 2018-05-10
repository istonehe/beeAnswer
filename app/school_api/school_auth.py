from flask import url_for
from flask_restful import Resource, abort, marshal_with, fields as rfields
from webargs import fields
from webargs.flaskparser import use_args
from ..models import Teacher
from .. import db
from . import school_api_bp, school_api


#use_args
teacher_reg = {
    'telephone': fields.Int(required = True),
    'nickname': fields.String(required = True),
    'password': fields.Str(required = True, validate=lambda p: len(p) >= 6),
}

#marshal_with
teacher_info = {
    'id': rfields.Integer,
    'nickname': rfields.String,
    'rename': rfields.String,
    'intro': rfields.String,
    'email': rfields.String ,
    'telephone': rfields.Integer
}

class TeacherReg(Resource):
    @marshal_with(teacher_info, envelope='resource')
    @use_args(teacher_reg)
    def post(self, args):
        teacher = Teacher(telephone= args['telephone'], nickname=args['nickname'], password=args['password'])
        db.session.add(teacher)
        db.session.commit()
        result = Teacher.query.get(teacher.id)
        return result, 201

school_api.add_resource(TeacherReg, '/register')
