from flask import Flask

from .database import init_app
from .routes.api import api_bp
from .routes.auth import auth_bp
from .routes.web import web_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_mapping(
        SECRET_KEY="dev-change-me",
        DATABASE=app.instance_path + "/mindtrack.db",
        EXPORT_DIR=app.instance_path + "/exports",
    )

    init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
