import os
from flask import Flask
from app.config import config_by_name

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    from app.api.routes import api_bp
    app.register_blueprint(api_bp)

    return app
