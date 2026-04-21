from dataclasses import dataclass
from datetime import UTC, datetime

from ..database import db


@dataclass(slots=True)
class EntryPayload:
    entry_date: str
    sleep_hours: float
    study_hours: float
    exercise_minutes: int
    reading_hours: float
    leisure_hours: float
    mood_score: int
    progress_percent: int
    energy_level: int
    notes: str


class DailyEntry(db.Model):
    __tablename__ = "daily_entries"
    __table_args__ = (
        db.UniqueConstraint("user_id", "entry_date", name="uq_daily_entries_user_date"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_date = db.Column(db.String(10), nullable=False, index=True)
    sleep_hours = db.Column(db.Float, nullable=False)
    study_hours = db.Column(db.Float, nullable=False)
    exercise_minutes = db.Column(db.Integer, nullable=False)
    reading_hours = db.Column(db.Float, nullable=False, default=0)
    leisure_hours = db.Column(db.Float, nullable=False, default=0)
    mood_score = db.Column(db.Integer, nullable=False)
    progress_percent = db.Column(db.Integer, nullable=False)
    energy_level = db.Column(db.Integer, nullable=False, default=5)
    notes = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = db.relationship("User", back_populates="entries")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entry_date": self.entry_date,
            "sleep_hours": self.sleep_hours,
            "study_hours": self.study_hours,
            "exercise_minutes": self.exercise_minutes,
            "reading_hours": self.reading_hours,
            "leisure_hours": self.leisure_hours,
            "mood_score": self.mood_score,
            "progress_percent": self.progress_percent,
            "energy_level": self.energy_level,
            "notes": self.notes,
        }
