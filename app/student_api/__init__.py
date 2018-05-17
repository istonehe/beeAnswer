from flask import Blueprint
from flask_restful import Api

student_api_bp = Blueprint('student_api', __name__)
student_api = Api(student_api_bp)

from . import student_auth