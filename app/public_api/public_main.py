import os
import re
import hashlib
import time
import requests
from flask import g, request, current_app
from flask_restful import Resource, abort, marshal_with, fields as rfields
from flask_httpauth import HTTPBasicAuth
from werkzeug.utils import secure_filename
from webargs import fields
from webargs.flaskparser import use_args
from requests.exceptions import ReadTimeout, ConnectTimeout, ConnectionError as _ConnectionError
from ..models import Teacher, Student, Topicimage, School
from .. import db
from . import public_api

TIMEOUT = 2
wxurl = 'https://api.weixin.qq.com/sns/jscode2session'

auth = HTTPBasicAuth()

basedir = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir, os.path.pardir, os.path.pardir)
# use_args
teacher_regs = {
    'telephone': fields.Str(
        required=True,
        validate=lambda p: re.match('^1[34578]\\d{9}$', p) is not None
    ),
    'nickname': fields.Str(required=True),
    'tcode': fields.Str(required=True),
    'password': fields.Str(required=True, validate=lambda p: len(p) >= 6)
}

student_regs = {
    'telephone': fields.Str(
        required=True,
        validate=lambda p: re.match('^1[34578]\\d{9}$', p) is not None
    ),
    'nickname': fields.Str(required=True),
    'password': fields.Str(required=True, validate=lambda p: len(p) >= 6)
}

# marshal_with
teacher_info = {
    'id': rfields.Integer,
    'nickname': rfields.String,
    'rename': rfields.String,
    'intro': rfields.String,
    'telephone': rfields.String
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
    return True


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
            abort(400, message='没有文件')
        file = request.files['file']
        if file.filename == '':
            abort(400, message='No selected file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            md5filename = rename_file(filename)
            upfolder = current_app.config['UPLOAD_FOLDER']
            file.save(os.path.join(upfolder, md5filename))
            topicimage = Topicimage(
                img_url='uploads' + '/' + md5filename,
                auth_telephone=g.user.telephone
            )
            db.session.add(topicimage)
            db.session.commit()
            result = {
                'id': topicimage.id,
                'url': 'uploads' + '/' + md5filename,
                'auth_telephone': topicimage.auth_telephone
            }
            return result, 200


class TeacherReg(Resource):
    @marshal_with(teacher_info, envelope='resource')
    @use_args(teacher_regs)
    def post(self, args):
        if Teacher.query.filter_by(telephone=args['telephone']).first():
            abort(401, code=0, message='教师已经存在')
        teacher = Teacher(
            telephone=args['telephone'],
            nickname=args['nickname'],
            password=args['password']
        )
        db.session.add(teacher)
        # 通过邀请码匹配学校并删除已经被使用的邀请码
        if teacher.bind_school(args['tcode']):
            result = Teacher.query.get(teacher.id)
            return result, 201


class StudentReg(Resource):
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


class ConnectTimeoutError(Exception):
    def __init__(self, code, description):
        self.code = code
        self.description = description

    def __str__(self):
        return '%s: %s' % (self.code, self.description)
        abort(400, code=self.code, message=self.description)


class ConnectionError(Exception):
    def __init__(self, code, description):
        self.code = code
        self.description = description

    def __str__(self):
        abort(400, code=self.code, message=self.description)


# 微信鉴权
class WxStudentLogin(Resource):

    wxlogin_args = {
        'code': fields.Str(required=True),
        'school_id': fields.Int(required=True)
    }

    @use_args(wxlogin_args)
    def post(self, args):
        sc_id = args['school_id']
        school = School.query.get(sc_id)
        if school is None:
            abort(404, code=0, message='School not found')
        appid = school.wx_appid
        appsecret = school.wx_appsecret
        code = args['code']
        wxparams = {'appid': appid, 'secret': appsecret, 'js_code': code, 'grant_type': 'authorization_code'}
        try:
            r = requests.get(wxurl, params=wxparams, timeout=TIMEOUT).json()
        except (ConnectTimeout, ReadTimeout):
            raise ConnectTimeoutError(0, 'wx server connect timeout')
        except _ConnectionError:
            raise ConnectionError(0, 'wx server connect error')
        pass
        # 判断微信返回errcode
        errcode = r.get('errcode', 0)
        if errcode:
            abort(400, code=0, errcode=errcode, message=r.get('errmsg', ' '))
        openid = r.get('openid')
        session_key = r.get('session_key')
        student = Student.query.filter_by(wx_openid=openid).first()
        # openid已经存在
        if student:
            student.wx_sessionkey = session_key
            db.session.commit()
            token = student.generate_auth_token(60*60*24*15)
            return {'code': 1, 'student_id': student.id, 'token': token}, 200
        # 新的openid入库
        newstudent = Student(wx_openid=openid, wx_sessionkey=session_key)
        db.session.add(newstudent)
        db.session.commit()
        newstudent.join_school(sc_id)
        token = newstudent.generate_auth_token(60*60*24*15)
        return {'code': 1, 'student_id': newstudent.id, 'token': token}, 200


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


# 微信资料解密
class WeiXinSecret(Resource):
    
    wx_info = {
        'encryptedData': fields.Str(required=True),

    }

    @use_args(wx_info)
    def post(self):
        pass


public_api.add_resource(UploadFile, '/uploads')

public_api.add_resource(StudentReg, '/student/register')
public_api.add_resource(TeacherReg, '/teacher/register')

public_api.add_resource(WxStudentLogin, '/wxstlogin')

public_api.add_resource(SchoolInfo, '/school/<school_id>')
