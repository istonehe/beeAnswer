from flask import Blueprint
from flask_restful import Api

school_api_bp = Blueprint('school_api', __name__)
school_api = Api(school_api_bp)


from . import school_auth
from .. import errors
