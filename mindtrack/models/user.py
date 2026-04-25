from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from ..database import GUID, db
from ..utils.helpers import serialize_mapping


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid4()))
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(30), nullable=False, default="user", server_default="user")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    entries = db.relationship("DailyEntry", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    habits = db.relationship("Habit", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    habit_logs = db.relationship("HabitLog", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    goals = db.relationship("Goal", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    insights = db.relationship("Insight", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    analytics_snapshots = db.relationship(
        "AnalyticsSnapshot",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    audit_logs = db.relationship("AuditLog", back_populates="user", lazy="selectin")

    def to_dict(self) -> dict:
        return serialize_mapping(
            {
                "id": self.id,
                "name": self.name,
                "email": self.email,
                "role": self.role,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
