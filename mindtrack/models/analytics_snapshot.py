from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Index

from ..database import GUID, db
from ..utils.helpers import serialize_mapping


class AnalyticsSnapshot(db.Model):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "period_type",
            "period_start",
            "period_end",
            name="uq_analytics_snapshots_period",
        ),
        Index("idx_analytics_user_period", "user_id", "period_type", "period_start"),
    )

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    period_type = db.Column(db.String(30), nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    avg_sleep = db.Column(db.Numeric(5, 2), nullable=True)
    avg_study = db.Column(db.Numeric(5, 2), nullable=True)
    avg_mood = db.Column(db.Numeric(5, 2), nullable=True)
    avg_productivity = db.Column(db.Numeric(5, 2), nullable=True)
    avg_progress = db.Column(db.Numeric(5, 2), nullable=True)
    life_score = db.Column(db.Integer, nullable=True)
    consistency_streak = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    user = db.relationship("User", back_populates="analytics_snapshots")

    def to_dict(self) -> dict:
        return serialize_mapping(
            {
                "id": self.id,
                "user_id": self.user_id,
                "period_type": self.period_type,
                "period_start": self.period_start,
                "period_end": self.period_end,
                "avg_sleep": self.avg_sleep,
                "avg_study": self.avg_study,
                "avg_mood": self.avg_mood,
                "avg_productivity": self.avg_productivity,
                "avg_progress": self.avg_progress,
                "life_score": self.life_score,
                "consistency_streak": self.consistency_streak,
                "created_at": self.created_at,
            }
        )
