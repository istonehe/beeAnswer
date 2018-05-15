from flask_restful import abort
from sqlalchemy.exc import IntegrityError
from .admin_api import admin_api_bp


class ValidationError(ValueError):
    pass


def bad_request(message):
    abort(404, error='错误的请求', message=message, code='1001')


# IntegrityError
# @admin_api_bp.errorhandler(IntegrityError)
# @admin_api_bp.errorhandler(ValueError)
# def validation_error(e):
#    return bad_request(e.args[0])
