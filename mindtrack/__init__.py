import logging
import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import DevelopmentConfig, config_by_name
from .database import init_app as init_database
from .routes.api import api_bp
from .routes.auth import auth_bp
from .routes.web import web_bp


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="../templates",
        static_folder="../static",
    )

    config_name = os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(config_name, DevelopmentConfig))
    if test_config:
        app.config.update(test_config)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    _configure_logging(app)

    init_database(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    app.logger.info("MindTrack-Life app initialized in %s mode.", app.config.get("ENV_NAME", config_name))
    return app


def _configure_logging(app: Flask) -> None:
    level_name = str(app.config.get("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    app.logger.setLevel(level)
