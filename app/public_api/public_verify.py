import os
import re
import hashlib
import time
import requests
import uuid
import random
from flask import g, request, current_app
from flask_restful import Resource, abort, marshal_with, fields as rfields
from webargs import fields, validate
from webargs.flaskparser import use_args
from requests.exceptions import ReadTimeout, ConnectTimeout, ConnectionError as _ConnectionError
from ..models import Teacher, Student, Topicimage, School, SchoolStudent
from .. import db
from .. import redis_store
from . import public_api
from ..units import vercode
from ..units import WXBizDataCrypt
from ..dysms_python import demo_sms_send

TIMEOUT = 2
wxurl = 'https://api.weixin.qq.com/sns/jscode2session'


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


# 微信鉴权-学生
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
        # 判断微信返回errcode
        errcode = r.get('errcode', 0)
        if errcode:
            abort(400, code=0, errcode=errcode, message=r.get('errmsg', ' '))
        openid = r.get('openid')
        session_key = r.get('session_key')

        # openid已经存在
        member_info = SchoolStudent.query.filter_by(wx_openid=openid).first()
        if member_info:
            member_info.wx_sessionkey = session_key
            db.session.commit()
            student_id = member_info.student_id
            student = Student.query.get(student_id)
            token = student.generate_auth_token(60*60*24*15)
            # 注意删除 openid sessinkey
            return {'code': 1, 'student_id': student_id, 'token': token}, 200

        # 新的openid入库
        newstudent = Student(nickname=' ')
        db.session.add(newstudent)
        db.session.commit()
        newstudent.join_school(sc_id)
        member_info = SchoolStudent.query.filter_by(
            school_id=sc_id,
            student_id=newstudent.id
        ).first()
        member_info.wx_openid = openid
        member_info.wx_sessionkey = session_key
        db.session.commit()
        token = newstudent.generate_auth_token(60*60*24*15)
        return {'code': 1, 'student_id': newstudent.id, 'token': token}, 200


# 微信鉴权老师
class WxTeacherLogin(Resource):

    login_args = {
        'code': fields.Str(required=True)
    }

    teacher_info = {
        'code': rfields.Integer,
        'token': rfields.String,
        'teacher': rfields.Nested({
            'id': rfields.Integer,
            'nickname': rfields.String,
            'imgurl': rfields.String,
            'intro': rfields.String,
            'gender': rfields.Integer,
            'register': rfields.Boolean
        })
    }

    @use_args(login_args)
    @marshal_with(teacher_info)
    def post(self, args):
        appid = os.getenv('WX_APPID')
        appsecret = os.getenv('WX_APPSECRET')
        code = args['code']
        wxparams = {'appid': appid, 'secret': appsecret, 'js_code': code, 'grant_type': 'authorization_code'}
        try:
            r = requests.get(wxurl, params=wxparams, timeout=TIMEOUT).json()
        except (ConnectTimeout, ReadTimeout):
            raise ConnectTimeoutError(0, 'wx server connect timeout')
        except _ConnectionError:
            raise ConnectionError(0, 'wx server connect error')
        errcode = r.get('errcode', 0)
        if errcode:
            abort(400, code=0, errcode=errcode, message=r.get('errmsg', ' '))
        openid = r.get('openid')
        session_key = r.get('session_key')

        # 如果用户已存在
        teacher = Teacher.query.filter_by(wx_openid=openid).first()
        if teacher:
            teacher.wx_sessionkey = session_key
            db.session.commit()
            token = teacher.generate_auth_token(60*60*24*15)
            teacher.register = True
            if teacher.telephone is None:
                teacher.register = False
            result = {
                'code': 1,
                'teacher': teacher,
                'token': token
            }
            return result, 200

        # 新用户入库
        newteacher = Teacher(nickname='')
        newteacher.wx_openid = openid
        newteacher.wx_sessionkey = session_key
        db.session.add(newteacher)
        db.session.commit()
        token = newteacher.generate_auth_token(60*60*24*15)
        newteacher.register = False
        result = {
            'code': 1,
            'teacher': newteacher,
            'token': token
        }

        return result, 200


# 学生微信资料解密
class StudentWeiXinSecret(Resource):

    wx_info = {
        'nickname': fields.Str(missing=None),
        'avatarUrl': fields.Str(missing=None),
        'gender': fields.Int(validate=validate.OneOf([0, 1, 2]), missing=0),
        'city': fields.Str(missing=None),
        'province': fields.Str(missing=None),
        'country': fields.Str(missing=None),
        'encryptedData': fields.Str(missing=None),
        'iv': fields.Str(missing=None)
    }

    @use_args(wx_info)
    def put(self, args, school_id, student_id):
        school = School.query.get(school_id)
        if school is None:
            abort(404, code=0, message='school not found')
        student = Student.query.get(student_id)
        if student is None:
            abort(404, code=0, message='Student not found')
        # 存入公开数据
        student.nickname = args['nickname']
        student.imgurl = args['avatarUrl']
        student.gender = args['gender']
        student.city = args['city']
        student.province = args['province']
        student.country = args['country']
        # 获取会员信息
        member_info = SchoolStudent.query.filter_by(
            school_id=school_id,
            student_id=student_id
        ).first()
        # 数据解密
        appId = school.wx_appid
        sessionKey = member_info.wx_sessionkey
        encryptedData = args['encryptedData']
        iv = args['iv']
        pc = WXBizDataCrypt.WXBizDataCrypt(appId, sessionKey)
        # 解密结果info
        info = pc.decrypt(encryptedData, iv)
        # 存入敏感数据
        student.wx_unionid = info.get('unionId', None)
        db.session.commit()
        result = {
            'code': 1,
            'message': 'ok',
        }
        return result, 201


# 老师微信资料解密
class TeacherWeiXinSecret(Resource):

    wx_info = {
        'nickname': fields.Str(missing=None),
        'avatarUrl': fields.Str(missing=None),
        'gender': fields.Int(validate=validate.OneOf([0, 1, 2]), missing=0),
        'city': fields.Str(missing=None),
        'province': fields.Str(missing=None),
        'country': fields.Str(missing=None),
        'encryptedData': fields.Str(missing=None),
        'iv': fields.Str(missing=None)
    }

    @use_args(wx_info)
    def put(self, args, teacher_id):
        teacher = Teacher.query.get(teacher_id)
        if teacher is None:
            abort(404, code=0, message='teacher not found')
        # 存入公开数据
        teacher.nickname = args['nickname']
        teacher.imgurl = args['avatarUrl']
        teacher.gender = args['gender']
        teacher.city = args['city']
        teacher.province = args['province']
        teacher.country = args['country']
        # 数据解密
        appId = os.getenv('WX_APPID')
        sessionKey = teacher.wx_sessionkey
        encryptedData = args['encryptedData']
        iv = args['iv']
        pc = WXBizDataCrypt.WXBizDataCrypt(appId, sessionKey)
        # 解密结果info
        info = pc.decrypt(encryptedData, iv)
        # 存入敏感数据
        teacher.wx_unionid = info.get('unionId', None)
        db.session.commit()
        result = {
            'code': 1,
            'message': 'ok',
        }
        return result, 201


# 图片验证
class ImgCode(Resource):
    imgcode_args = {
        'uuid': fields.Str(required=True),
        'inputvalue': fields.Str(required=True)
    }

    imgcode_info = {
        'code': rfields.Integer,
        # 'codevalue': rfields.String,
        'imgurl': rfields.String,
        'auuid': rfields.String
    }

    @marshal_with(imgcode_info)
    def get(self):
        imgcodefile = current_app.config['IMGCODE_FILE']
        generateImgCode = vercode.VerCodeImg()
        codeinfo = generateImgCode.create(imgcodefile)
        codevalue = codeinfo.get('codeValue')
        filename = codeinfo.get('fileName')
        imgurl = 'imgcodes/' + filename
        auuid = str(uuid.uuid1())
        # 将uuid和对应的code值存入redis
        redis_store.setex(auuid, 580, codevalue)
        result = {
            'code': 1,
            # 'codevalue': codevalue,
            'imgurl': imgurl,
            'auuid': auuid
        }
        return result, 200

    # only test
    @use_args(imgcode_args)
    def post(self, args):
        uuid = args['uuid']
        inputvalue = args['inputvalue']
        value = redis_store.get(uuid)
        print(value, inputvalue)
        if value.decode('utf-8') == inputvalue:
            return {'code': 1}, 200
        return {'code': 0}, 403


# 短信验证码
class SendSMS(Resource):

    sms_args = {
        'uuid': fields.Str(required=True),
        'inputvalue': fields.Str(required=True),
        'phone_numbers': fields.Str(
            required=True,
            validate=lambda p: re.match('^1[34578]\\d{9}$', p) is not None
        )
    }

    @use_args(sms_args)
    def post(self, args):
        phone_numbers = args['phone_numbers']

        # 验证图片码
        auuid = args['uuid']
        inputvalue = args['inputvalue']
        value = redis_store.get(auuid)
        if value is None:
            return {'code': 0, 'message': '验证码错误'}, 403
        if value.decode('utf-8') != inputvalue:
            redis_store.delete(auuid)
            return {'code': 0, 'message': '验证码错误'}, 403
        redis_store.delete(auuid)

        # 检测手机号是否在60s内存在,返回0可继续
        phone_status = redis_store.exists(phone_numbers)
        if phone_status:
            return {'code': 0, 'message': '请求太频繁'}, 403

        # 生成短信内容
        smsuuid = phone_numbers + '-' + str(uuid.uuid1())
        rndcode = ''
        for t in range(6):
            num = str(random.randint(0, 9))
            rndcode += num
        sign_name = '麦学习软件'
        params = {'code': rndcode, 'product': '麦学习答疑'}

        # 调用发送接口
        send_result = demo_sms_send.send_sms(smsuuid, phone_numbers, sign_name, 'SMS_76030398', params)

        # 存值到redis
        value = phone_numbers + rndcode
        redis_store.setex(smsuuid, 3600, value)

        # 手机入库60s防刷
        redis_store.setex(phone_numbers, 60, 'x')

        print(send_result)

        return {'code': 1, 'uuid': smsuuid}, 200


# 验证手机号存在
class PhoneExist(Resource):
    def get(self, telephone):
        teacher = Teacher.query.filter_by(telephone=telephone).first()
        if teacher:
            return {'code': 0, 'message': '该手机号已经被绑定'}
        return {'code': 1, 'message': '该手机号可以使用'}


public_api.add_resource(WxStudentLogin, '/wxstlogin')
public_api.add_resource(WxTeacherLogin, '/wxteacherlogin')
public_api.add_resource(StudentWeiXinSecret, '/studentwxsecret/<int:school_id>/<int:student_id>')
public_api.add_resource(TeacherWeiXinSecret, '/teacherwxsecret/<int:teacher_id>')

public_api.add_resource(ImgCode, '/imgcode')
public_api.add_resource(PhoneExist, '/phoneexist/<telephone>')
public_api.add_resource(SendSMS, '/sendsms')
