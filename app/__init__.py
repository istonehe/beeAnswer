from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

db = SQLAlchemy()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .admin_api import admin_api_bp as admin_api_blueprint
    app.register_blueprint(admin_api_blueprint, url_prefix='/v1/admin')

    from .school_api import school_api_bp as school_api_blueprint
    app.register_blueprint(school_api_blueprint, url_prefix='/v1/school')

    return app
