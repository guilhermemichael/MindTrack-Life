"""professional data architecture

Revision ID: a5530b4e4cb4
Revises:
Create Date: 2026-04-25 03:51:45.215682

"""

from datetime import UTC, date, datetime
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a5530b4e4cb4"
down_revision = None
branch_labels = None
depends_on = None


def _utc_now():
    return datetime.now(UTC)


def _parse_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _parse_datetime(value):
    if value is None:
        return _utc_now()
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return _utc_now()


def _compute_productivity(study_hours, exercise_minutes, mood_score, progress_score):
    score = 0
    score += min(float(study_hours or 0) / 4, 1) * 35
    score += min(int(exercise_minutes or 0) / 45, 1) * 15
    score += (int(mood_score or 0) / 10) * 20
    score += (int(progress_score or 0) / 100) * 30
    return round(min(score, 100))


def _table_exists(inspector, table_name):
    return table_name in inspector.get_table_names()


def _is_legacy_users_table(inspector):
    if not _table_exists(inspector, "users"):
        return False
    columns = {column["name"] for column in inspector.get_columns("users")}
    return "role" not in columns or "updated_at" not in columns


def _is_legacy_daily_entries_table(inspector):
    if not _table_exists(inspector, "daily_entries"):
        return False
    columns = {column["name"] for column in inspector.get_columns("daily_entries")}
    return "progress_score" not in columns or "productivity_score" not in columns


def _create_users_table():
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=180), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def _create_daily_entries_table():
    op.create_table(
        "daily_entries",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("sleep_hours", sa.Numeric(4, 2), nullable=False),
        sa.Column("study_hours", sa.Numeric(4, 2), nullable=False),
        sa.Column("exercise_minutes", sa.Integer(), nullable=False),
        sa.Column("mood_score", sa.Integer(), nullable=False),
        sa.Column("productivity_score", sa.Integer(), nullable=False),
        sa.Column("progress_score", sa.Integer(), nullable=False),
        sa.Column("reading_hours", sa.Numeric(5, 2), nullable=False),
        sa.Column("leisure_hours", sa.Numeric(5, 2), nullable=False),
        sa.Column("energy_level", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("sleep_hours >= 0 AND sleep_hours <= 24", name="ck_daily_entries_sleep_hours"),
        sa.CheckConstraint("study_hours >= 0 AND study_hours <= 24", name="ck_daily_entries_study_hours"),
        sa.CheckConstraint("exercise_minutes >= 0", name="ck_daily_entries_exercise_minutes"),
        sa.CheckConstraint("mood_score >= 1 AND mood_score <= 10", name="ck_daily_entries_mood_score"),
        sa.CheckConstraint("productivity_score >= 0 AND productivity_score <= 100", name="ck_daily_entries_productivity_score"),
        sa.CheckConstraint("progress_score >= 0 AND progress_score <= 100", name="ck_daily_entries_progress_score"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "entry_date", name="uq_daily_entries_user_date"),
    )
    op.create_index("idx_daily_entries_user_date", "daily_entries", ["user_id", "entry_date"], unique=False)
    op.create_index("ix_daily_entries_user_id", "daily_entries", ["user_id"], unique=False)
    op.create_index("ix_daily_entries_entry_date", "daily_entries", ["entry_date"], unique=False)


def _create_supporting_tables():
    op.create_table(
        "habits",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("target_value", sa.Numeric(8, 2), nullable=True),
        sa.Column("unit", sa.String(length=30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("target_value IS NULL OR target_value >= 0", name="ck_habits_target_value"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_habits_user_active", "habits", ["user_id", "is_active"], unique=False)
    op.create_index("ix_habits_user_id", "habits", ["user_id"], unique=False)

    op.create_table(
        "habit_logs",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("habit_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("value", sa.Numeric(8, 2), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("value >= 0", name="ck_habit_logs_value"),
        sa.ForeignKeyConstraint(["habit_id"], ["habits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("habit_id", "log_date", name="uq_habit_logs_habit_date"),
    )
    op.create_index("idx_habit_logs_user_date", "habit_logs", ["user_id", "log_date"], unique=False)
    op.create_index("ix_habit_logs_habit_id", "habit_logs", ["habit_id"], unique=False)
    op.create_index("ix_habit_logs_user_id", "habit_logs", ["user_id"], unique=False)

    op.create_table(
        "goals",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("target_value", sa.Numeric(10, 2), nullable=True),
        sa.Column("current_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("target_value IS NULL OR target_value >= 0", name="ck_goals_target_value"),
        sa.CheckConstraint("current_value >= 0", name="ck_goals_current_value"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_goals_user_status", "goals", ["user_id", "status"], unique=False)
    op.create_index("ix_goals_user_id", "goals", ["user_id"], unique=False)

    op.create_table(
        "insights",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("insight_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=30), nullable=False, server_default="info"),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metric_key", sa.String(length=80), nullable=True),
        sa.Column("metric_value", sa.Numeric(10, 2), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_insights_user_generated", "insights", ["user_id", "generated_at"], unique=False)
    op.create_index("ix_insights_user_id", "insights", ["user_id"], unique=False)

    op.create_table(
        "analytics_snapshots",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("period_type", sa.String(length=30), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("avg_sleep", sa.Numeric(5, 2), nullable=True),
        sa.Column("avg_study", sa.Numeric(5, 2), nullable=True),
        sa.Column("avg_mood", sa.Numeric(5, 2), nullable=True),
        sa.Column("avg_productivity", sa.Numeric(5, 2), nullable=True),
        sa.Column("avg_progress", sa.Numeric(5, 2), nullable=True),
        sa.Column("life_score", sa.Integer(), nullable=True),
        sa.Column("consistency_streak", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "period_type", "period_start", "period_end", name="uq_analytics_snapshots_period"),
    )
    op.create_index("idx_analytics_user_period", "analytics_snapshots", ["user_id", "period_type", "period_start"], unique=False)
    op.create_index("ix_analytics_snapshots_user_id", "analytics_snapshots", ["user_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=False), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_name", sa.String(length=100), nullable=True),
        sa.Column("entity_id", sa.Uuid(as_uuid=False), nullable=True),
        sa.Column("old_data", sa.JSON(), nullable=True),
        sa.Column("new_data", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], unique=False)


def _migrate_users(bind):
    legacy_rows = bind.execute(sa.text("SELECT * FROM users_legacy")).mappings().all()
    mapping = {}
    for row in legacy_rows:
        new_id = str(uuid4())
        mapping[row["id"]] = new_id
        bind.execute(
            sa.text(
                """
                INSERT INTO users (id, name, email, password_hash, role, created_at, updated_at)
                VALUES (:id, :name, :email, :password_hash, :role, :created_at, :updated_at)
                """
            ),
            {
                "id": new_id,
                "name": row["name"],
                "email": row["email"],
                "password_hash": row["password_hash"],
                "role": "user",
                "created_at": _parse_datetime(row.get("created_at")),
                "updated_at": _parse_datetime(row.get("created_at")),
            },
        )
    return mapping


def _migrate_daily_entries(bind, user_id_map):
    legacy_rows = bind.execute(sa.text("SELECT * FROM daily_entries_legacy ORDER BY entry_date")).mappings().all()
    for row in legacy_rows:
        progress_score = int(row.get("progress_percent") or row.get("progress_score") or 0)
        bind.execute(
            sa.text(
                """
                INSERT INTO daily_entries (
                    id, user_id, entry_date, sleep_hours, study_hours, exercise_minutes,
                    mood_score, productivity_score, progress_score, reading_hours,
                    leisure_hours, energy_level, notes, created_at, updated_at
                )
                VALUES (
                    :id, :user_id, :entry_date, :sleep_hours, :study_hours, :exercise_minutes,
                    :mood_score, :productivity_score, :progress_score, :reading_hours,
                    :leisure_hours, :energy_level, :notes, :created_at, :updated_at
                )
                """
            ),
            {
                "id": str(uuid4()),
                "user_id": user_id_map.get(row["user_id"]),
                "entry_date": _parse_date(row["entry_date"]),
                "sleep_hours": float(row.get("sleep_hours") or 0),
                "study_hours": float(row.get("study_hours") or 0),
                "exercise_minutes": int(row.get("exercise_minutes") or 0),
                "mood_score": int(row.get("mood_score") or 0),
                "productivity_score": _compute_productivity(
                    row.get("study_hours"),
                    row.get("exercise_minutes"),
                    row.get("mood_score"),
                    progress_score,
                ),
                "progress_score": progress_score,
                "reading_hours": float(row.get("reading_hours") or 0),
                "leisure_hours": float(row.get("leisure_hours") or 0),
                "energy_level": int(row.get("energy_level") or 5),
                "notes": row.get("notes") or "",
                "created_at": _parse_datetime(row.get("created_at")),
                "updated_at": _parse_datetime(row.get("updated_at")),
            },
        )


def _create_views(bind):
    dialect = bind.dialect.name
    op.execute("DROP VIEW IF EXISTS weekly_user_summary")
    op.execute("DROP VIEW IF EXISTS sleep_mood_analysis")

    if dialect == "postgresql":
        op.execute(
            """
            CREATE VIEW weekly_user_summary AS
            SELECT
                user_id,
                DATE_TRUNC('week', entry_date) AS week_start,
                ROUND(AVG(sleep_hours), 2) AS avg_sleep,
                ROUND(AVG(study_hours), 2) AS avg_study,
                ROUND(AVG(mood_score), 2) AS avg_mood,
                ROUND(AVG(productivity_score), 2) AS avg_productivity,
                ROUND(AVG(progress_score), 2) AS avg_progress,
                COUNT(*) AS total_entries
            FROM daily_entries
            GROUP BY user_id, DATE_TRUNC('week', entry_date)
            """
        )
        op.execute(
            """
            CREATE VIEW sleep_mood_analysis AS
            SELECT
                user_id,
                COUNT(*) AS total_days,
                ROUND(AVG(sleep_hours), 2) AS avg_sleep,
                ROUND(AVG(mood_score), 2) AS avg_mood,
                ROUND(CORR(sleep_hours, mood_score), 3) AS sleep_mood_correlation
            FROM daily_entries
            GROUP BY user_id
            HAVING COUNT(*) >= 5
            """
        )
    else:
        op.execute(
            """
            CREATE VIEW weekly_user_summary AS
            SELECT
                user_id,
                MIN(entry_date) AS week_start,
                ROUND(AVG(sleep_hours), 2) AS avg_sleep,
                ROUND(AVG(study_hours), 2) AS avg_study,
                ROUND(AVG(mood_score), 2) AS avg_mood,
                ROUND(AVG(productivity_score), 2) AS avg_productivity,
                ROUND(AVG(progress_score), 2) AS avg_progress,
                COUNT(*) AS total_entries
            FROM daily_entries
            GROUP BY user_id, strftime('%Y-%W', entry_date)
            """
        )
        op.execute(
            """
            CREATE VIEW sleep_mood_analysis AS
            SELECT
                user_id,
                COUNT(*) AS total_days,
                ROUND(AVG(sleep_hours), 2) AS avg_sleep,
                ROUND(AVG(mood_score), 2) AS avg_mood,
                NULL AS sleep_mood_correlation
            FROM daily_entries
            GROUP BY user_id
            HAVING COUNT(*) >= 5
            """
        )


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    legacy_users = _is_legacy_users_table(inspector)
    legacy_entries = _is_legacy_daily_entries_table(inspector)

    if legacy_entries:
        op.rename_table("daily_entries", "daily_entries_legacy")
    if legacy_users:
        op.rename_table("users", "users_legacy")

    _create_users_table()
    _create_daily_entries_table()
    _create_supporting_tables()

    user_id_map = {}
    if legacy_users:
        user_id_map = _migrate_users(bind)
    if legacy_entries:
        _migrate_daily_entries(bind, user_id_map)

    if legacy_entries:
        op.drop_table("daily_entries_legacy")
    if legacy_users:
        op.drop_table("users_legacy")

    _create_views(bind)


def downgrade():
    op.execute("DROP VIEW IF EXISTS sleep_mood_analysis")
    op.execute("DROP VIEW IF EXISTS weekly_user_summary")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_analytics_snapshots_user_id", table_name="analytics_snapshots")
    op.drop_index("idx_analytics_user_period", table_name="analytics_snapshots")
    op.drop_table("analytics_snapshots")
    op.drop_index("ix_insights_user_id", table_name="insights")
    op.drop_index("idx_insights_user_generated", table_name="insights")
    op.drop_table("insights")
    op.drop_index("ix_goals_user_id", table_name="goals")
    op.drop_index("idx_goals_user_status", table_name="goals")
    op.drop_table("goals")
    op.drop_index("ix_habit_logs_user_id", table_name="habit_logs")
    op.drop_index("ix_habit_logs_habit_id", table_name="habit_logs")
    op.drop_index("idx_habit_logs_user_date", table_name="habit_logs")
    op.drop_table("habit_logs")
    op.drop_index("ix_habits_user_id", table_name="habits")
    op.drop_index("idx_habits_user_active", table_name="habits")
    op.drop_table("habits")
    op.drop_index("ix_daily_entries_entry_date", table_name="daily_entries")
    op.drop_index("ix_daily_entries_user_id", table_name="daily_entries")
    op.drop_index("idx_daily_entries_user_date", table_name="daily_entries")
    op.drop_table("daily_entries")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
