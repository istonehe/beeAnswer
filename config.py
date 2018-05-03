import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    FLASK_ADMIN = os.environ.get('FLASK_ADMIN')

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    SQLALCHEMY_DATAABSE_URI = os.environ.get('DEV_DATABASE_URL')

class TestingConfig(Config):
    SQLALCHEMY_DATAABSE_URI = os.environ.get('TEST_DATABASE_URL')

class ProductionConfig(Config):
    SQLALCHEMY_DATAABSE_URI = os.environ.get('DATABASE_URL')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
