from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, Index

from ..database import GUID, db
from ..utils.helpers import serialize_mapping


class Goal(db.Model):
    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint("target_value IS NULL OR target_value >= 0", name="ck_goals_target_value"),
        CheckConstraint("current_value >= 0", name="ck_goals_current_value"),
        Index("idx_goals_user_status", "user_id", "status"),
    )

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(80), nullable=True)
    target_value = db.Column(db.Numeric(10, 2), nullable=True)
    current_value = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    unit = db.Column(db.String(30), nullable=True)
    status = db.Column(db.String(30), nullable=False, default="active", server_default="active")
    start_date = db.Column(db.Date, nullable=True)
    deadline = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = db.relationship("User", back_populates="goals")

    def to_dict(self) -> dict:
        return serialize_mapping(
            {
                "id": self.id,
                "user_id": self.user_id,
                "title": self.title,
                "description": self.description,
                "category": self.category,
                "target_value": self.target_value,
                "current_value": self.current_value,
                "unit": self.unit,
                "status": self.status,
                "start_date": self.start_date,
                "deadline": self.deadline,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        )
