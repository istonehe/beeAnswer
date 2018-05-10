form flask import Blueprint
from flask_restful import Api

teacher_api_bp = Blueprint('teacher_api', __name__)
teacher_api = Api(teacher_api_bp)

from . import error
