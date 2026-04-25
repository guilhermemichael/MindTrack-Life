from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, Index

from ..database import GUID, db
from ..utils.helpers import serialize_mapping


class Habit(db.Model):
    __tablename__ = "habits"
    __table_args__ = (
        CheckConstraint("target_value IS NULL OR target_value >= 0", name="ck_habits_target_value"),
        Index("idx_habits_user_active", "user_id", "is_active"),
    )

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(80), nullable=True)
    target_value = db.Column(db.Numeric(8, 2), nullable=True)
    unit = db.Column(db.String(30), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.text("true"))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    user = db.relationship("User", back_populates="habits")
    logs = db.relationship("HabitLog", back_populates="habit", cascade="all, delete-orphan", lazy="selectin")

    def to_dict(self) -> dict:
        return serialize_mapping(
            {
                "id": self.id,
                "user_id": self.user_id,
                "name": self.name,
                "category": self.category,
                "target_value": self.target_value,
                "unit": self.unit,
                "is_active": self.is_active,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        )
