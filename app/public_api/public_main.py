import os
import re
import hashlib
import time
from flask import g, request, current_app
from flask_restful import Resource, abort, marshal_with, fields as rfields
from flask_httpauth import HTTPBasicAuth
from werkzeug.utils import secure_filename
from webargs import fields, validate
from webargs.flaskparser import use_args
from requests.exceptions import ReadTimeout, ConnectTimeout, ConnectionError as _ConnectionError
from ..models import Teacher, Student, Topicimage, School, SchoolStudent
from .. import db
from .. import redis_store
from . import public_api


auth = HTTPBasicAuth()

basedir = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir, os.path.pardir, os.path.pardir)


def abort_if_school_doesnt_exist(id):
    if School.query.get(id) is None:
        abort(404, code=0, message='学校不存在')


@auth.verify_password
def verify_password(username_or_token, password):
    teacher_user = Teacher.verify_auth_token(username_or_token)
    student_user = Student.verify_auth_token(username_or_token)
    if not (teacher_user or student_user):
        teacher_user = Teacher.query.filter_by(telephone=username_or_token).first()
        student_user = Student.query.filter_by(telephone=username_or_token).first()
        if teacher_user:
            t = teacher_user.verify_password(password)
        if student_user:
            s = student_user.verify_password(password)
        if (not teacher_user or not t) and (not student_user or not s):
            return False
    g.user = teacher_user or student_user
    if teacher_user:
        g.user.user_type = 1
    if student_user:
        g.user.user_type = 2
    return True


@auth.error_handler
def auth_error():
    abort(401, code=4, message='未授权')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def md5Encode(str):
    m = hashlib.md5()
    m.update(str)
    return m.hexdigest()


def rename_file(filename):
    leftname = filename.rsplit('.', 1)[0] + str(time.time())
    md5leftname = md5Encode(leftname.encode('utf-8'))
    exname = filename.rsplit('.', 1)[1]
    return md5leftname + '.' + exname


class UploadFile(Resource):
    @auth.login_required
    # @marshal_with(uploadfile_info, envelope='resource')
    def post(self):
        if 'file' not in request.files:
            abort(400, code=0, message='没有文件')
        file = request.files['file']
        if file.filename == '':
            abort(400, code=0, message='No selected file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            md5filename = rename_file(filename)
            upfolder = current_app.config['UPLOAD_FOLDER']
            file.save(os.path.join(upfolder, md5filename))
            topicimage = Topicimage(
                img_url='uploads' + '/' + md5filename,
                auth_telephone=g.user.telephone,
                user_type=g.user.user_type,
                user_id=g.user.id
            )
            db.session.add(topicimage)
            db.session.commit()
            result = {
                'code': 1,
                'id': topicimage.id,
                'user_type': topicimage.user_type,
                'user_id': topicimage.user_id,
                'url': 'uploads' + '/' + md5filename,
                'auth_telephone': topicimage.auth_telephone
            }
            return result, 200


class StudentReg(Resource):

    student_regs = {
        'telephone': fields.Str(
            required=True,
            validate=lambda p: re.match('^1[34578]\\d{9}$', p) is not None
        ),
        'nickname': fields.Str(required=True),
        'password': fields.Str(required=True, validate=lambda p: len(p) >= 6)
    }

    student_info = {
        'id': rfields.Integer,
        'nickname': rfields.String,
        'rename': rfields.String,
        'imgurl': rfields.String,
        'telephone': rfields.String,
        'fromwhere': rfields.String,
        'wxopenid': rfields.String,
        'timestamp': rfields.DateTime(dt_format='iso8601'),
        'disabled': rfields.Boolean,
        'expevalue': rfields.Integer
    }

    @marshal_with(student_info, envelope='resource')
    @use_args(student_regs)
    def post(self, args):
        if Student.query.filter_by(telephone=args['telephone']).first():
            abort(401, code=0, message='学生已经存在')
        student = Student(
            telephone=args['telephone'],
            nickname=args['nickname'],
            password=args['password']
        )
        db.session.add(student)
        db.session.commit()
        return student, 201


class TeacherReg(Resource):
    # use_args
    teacher_regs = {
        'telephone': fields.Str(
            required=True,
            validate=lambda p: re.match('^1[34578]\\d{9}$', p) is not None
        ),
        'nickname': fields.Str(missing=''),
        'tcode': fields.Str(missing=''),
        'password': fields.Str(required=True, validate=lambda p: len(p) >= 6),
        'uuid': fields.Str(required=True),
        'phonecode': fields.Str(required=True)
    }

    # marshal_with
    teacher_info = {
        'code': rfields.Integer,
        'teacher': rfields.Nested({
            'id': rfields.Integer,
            'nickname': rfields.String,
            'intro': rfields.String,
            'telephone': rfields.String
        })
    }

    @marshal_with(teacher_info)
    @use_args(teacher_regs)
    def post(self, args):
        # 验证短信码
        auuid = args['uuid']
        inputvalue = args['phonecode']
        telephone = args['telephone']
        value = redis_store.get(auuid)
        if not value:
            abort(403, code=0, message='验证码错误')
        if value.decode('utf-8') != (telephone + inputvalue):
            redis_store.delete(auuid)
            abort(403, code=0, message='验证码错误')
        redis_store.delete(auuid)

        if Teacher.query.filter_by(telephone=telephone).first():
            abort(401, code=0, message='教师已经存在')
        teacher = Teacher(
            telephone=telephone,
            nickname=args['nickname'],
            password=args['password']
        )
        db.session.add(teacher)
        db.session.commit()
        # 通过邀请码匹配学校并删除已经被使用的邀请码
        tcode = args['tcode']
        if tcode:
            teacher.bind_school(args['tcode'])

        result = {
            'code': 1,
            'teacher': teacher
        }
        return result, 201


class WxTeacherReg(Resource):
    # use_args
    teacher_regs = {
        'teacher_id': fields.Int(required=True),
        'telephone': fields.Str(
            required=True,
            validate=lambda p: re.match('^1[34578]\\d{9}$', p) is not None
        ),
        'password': fields.Str(required=True, validate=lambda p: len(p) >= 6),
        'uuid': fields.Str(required=True),
        'phonecode': fields.Str(required=True)
    }

    # marshal_with
    teacher_info = {
        'code': rfields.Integer,
        'teacher': rfields.Nested({
            'id': rfields.Integer,
            'nickname': rfields.String,
            'intro': rfields.String,
            'telephone': rfields.String
        })
    }

    @marshal_with(teacher_info)
    @use_args(teacher_regs)
    def put(self, args):
        teacher_id = args['teacher_id']
        auuid = args['uuid']
        inputvalue = args['phonecode']
        telephone = args['telephone']
        password = args['password']
        # 验证短信码
        value = redis_store.get(auuid)
        if not value:
            abort(403, code=0, message='验证码错误')
        if value.decode('utf-8') != (telephone + inputvalue):
            redis_store.delete(auuid)
            abort(403, code=0, message='验证码错误')
        redis_store.delete(auuid)

        if Teacher.query.filter_by(telephone=telephone).first():
            abort(401, code=0, message='手机已经绑定到其他账户')

        teacher = Teacher.query.get(teacher_id)
        teacher.telephone = telephone
        teacher.password = password
        db.session.commit()
        result = {
            'code': 1,
            'teacher': teacher
        }
        return result, 201


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
        school = School.query.get(school_id)
        course = school.courses.all()[0]
        result = {
            'code': 1,
            'school': school,
            'course': course
        }
        return result, 200


public_api.add_resource(UploadFile, '/uploads')

public_api.add_resource(StudentReg, '/student/register')
public_api.add_resource(TeacherReg, '/teacher/register')
public_api.add_resource(WxTeacherReg, '/teacher/wxregister')

public_api.add_resource(SchoolInfo, '/school/<int:school_id>')
