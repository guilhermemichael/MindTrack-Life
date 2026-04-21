from pathlib import Path

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy(session_options={"expire_on_commit": False})


def init_app(app):
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["EXPORT_DIR"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    with app.app_context():
        from .models.entry import DailyEntry
        from .models.user import User

        db.create_all()
