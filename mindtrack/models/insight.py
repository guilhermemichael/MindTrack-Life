from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Index

from ..database import GUID, db
from ..utils.helpers import serialize_mapping


class Insight(db.Model):
    __tablename__ = "insights"
    __table_args__ = (
        Index("idx_insights_user_generated", "user_id", "generated_at"),
    )

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    insight_type = db.Column(db.String(80), nullable=False)
    severity = db.Column(db.String(30), nullable=False, default="info", server_default="info")
    title = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    metric_key = db.Column(db.String(80), nullable=True)
    metric_value = db.Column(db.Numeric(10, 2), nullable=True)
    generated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    read_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User", back_populates="insights")

    def to_dict(self) -> dict:
        return serialize_mapping(
            {
                "id": self.id,
                "user_id": self.user_id,
                "insight_type": self.insight_type,
                "severity": self.severity,
                "title": self.title,
                "message": self.message,
                "metric_key": self.metric_key,
                "metric_value": self.metric_value,
                "generated_at": self.generated_at,
                "read_at": self.read_at,
            }
        )
