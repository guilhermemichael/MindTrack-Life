from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, Index

from ..database import GUID, db
from ..utils.helpers import serialize_mapping


class HabitLog(db.Model):
    __tablename__ = "habit_logs"
    __table_args__ = (
        db.UniqueConstraint("habit_id", "log_date", name="uq_habit_logs_habit_date"),
        CheckConstraint("value >= 0", name="ck_habit_logs_value"),
        Index("idx_habit_logs_user_date", "user_id", "log_date"),
    )

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid4()))
    habit_id = db.Column(GUID(), db.ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(GUID(), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    log_date = db.Column(db.Date, nullable=False, default=date.today)
    value = db.Column(db.Numeric(8, 2), nullable=False, default=0)
    completed = db.Column(db.Boolean, nullable=False, default=False, server_default=db.text("false"))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    habit = db.relationship("Habit", back_populates="logs")
    user = db.relationship("User", back_populates="habit_logs")

    def to_dict(self) -> dict:
        return serialize_mapping(
            {
                "id": self.id,
                "habit_id": self.habit_id,
                "user_id": self.user_id,
                "log_date": self.log_date,
                "value": self.value,
                "completed": self.completed,
                "created_at": self.created_at,
            }
        )
