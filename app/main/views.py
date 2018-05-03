from flask import request, url_for

from . import main
from .. import db

@main.route('/')
def index():
    return '欢迎来访蜜蜂答疑！'
