import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    FLASK_ADMIN = os.environ.get('FLASK_ADMIN')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a string'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_AS_ASCII = False
    RESTFUL_JSON = dict(ensure_ascii=False)

    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'mp3'])
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
