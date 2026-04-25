from pathlib import Path

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.types import CHAR, TypeDecorator


db = SQLAlchemy(session_options={"expire_on_commit": False})
migrate = Migrate(compare_type=True)


class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=False))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return str(value)


def init_app(app):
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["EXPORT_DIR"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from .models.analytics_snapshot import AnalyticsSnapshot
        from .models.audit_log import AuditLog
        from .models.entry import DailyEntry
        from .models.goal import Goal
        from .models.habit import Habit
        from .models.habit_log import HabitLog
        from .models.insight import Insight
        from .models.user import User

        if app.config.get("TESTING"):
            db.create_all()
