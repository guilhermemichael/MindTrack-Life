from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import CheckConstraint, Index

from ..database import GUID, db
from ..utils.helpers import serialize_mapping


@dataclass(slots=True)
class EntryPayload:
    entry_date: date
    sleep_hours: float
    study_hours: float
    exercise_minutes: int
    mood_score: int
    productivity_score: int
    progress_score: int
    reading_hours: float
    leisure_hours: float
    energy_level: int
    notes: str


class DailyEntry(db.Model):
    __tablename__ = "daily_entries"
    __table_args__ = (
        db.UniqueConstraint("user_id", "entry_date", name="uq_daily_entries_user_date"),
        CheckConstraint("sleep_hours >= 0 AND sleep_hours <= 24", name="ck_daily_entries_sleep_hours"),
        CheckConstraint("study_hours >= 0 AND study_hours <= 24", name="ck_daily_entries_study_hours"),
        CheckConstraint("exercise_minutes >= 0", name="ck_daily_entries_exercise_minutes"),
        CheckConstraint("mood_score >= 1 AND mood_score <= 10", name="ck_daily_entries_mood_score"),
        CheckConstraint("productivity_score >= 0 AND productivity_score <= 100", name="ck_daily_entries_productivity_score"),
        CheckConstraint("progress_score >= 0 AND progress_score <= 100", name="ck_daily_entries_progress_score"),
        Index("idx_daily_entries_user_date", "user_id", "entry_date"),
    )

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_date = db.Column(db.Date, nullable=False, index=True)
    sleep_hours = db.Column(db.Numeric(4, 2), nullable=False)
    study_hours = db.Column(db.Numeric(4, 2), nullable=False)
    exercise_minutes = db.Column(db.Integer, nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)
    productivity_score = db.Column(db.Integer, nullable=False, default=0)
    progress_score = db.Column(db.Integer, nullable=False, default=0)
    reading_hours = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    leisure_hours = db.Column(db.Numeric(5, 2), nullable=False, default=0)
    energy_level = db.Column(db.Integer, nullable=False, default=5)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = db.relationship("User", back_populates="entries")

    def to_dict(self) -> dict:
        payload = serialize_mapping(
            {
                "id": self.id,
                "user_id": self.user_id,
                "entry_date": self.entry_date,
                "sleep_hours": self.sleep_hours,
                "study_hours": self.study_hours,
                "exercise_minutes": self.exercise_minutes,
                "mood_score": self.mood_score,
                "productivity_score": self.productivity_score,
                "progress_score": self.progress_score,
                "reading_hours": self.reading_hours,
                "leisure_hours": self.leisure_hours,
                "energy_level": self.energy_level,
                "notes": self.notes or "",
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        )
        payload["progress_percent"] = payload["progress_score"]
        return payload

    @property
    def sleep_hours_float(self) -> float:
        return float(self.sleep_hours or Decimal("0"))

    @property
    def study_hours_float(self) -> float:
        return float(self.study_hours or Decimal("0"))

    @property
    def progress_percent(self) -> int:
        return self.progress_score
