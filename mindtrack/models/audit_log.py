from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from ..database import GUID, db
from ..utils.helpers import serialize_mapping


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(GUID(), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(GUID(), db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)
    entity_name = db.Column(db.String(100), nullable=True)
    entity_id = db.Column(GUID(), nullable=True)
    old_data = db.Column(db.JSON, nullable=True)
    new_data = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(80), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))

    user = db.relationship("User", back_populates="audit_logs")

    def to_dict(self) -> dict:
        return serialize_mapping(
            {
                "id": self.id,
                "user_id": self.user_id,
                "action": self.action,
                "entity_name": self.entity_name,
                "entity_id": self.entity_id,
                "old_data": self.old_data,
                "new_data": self.new_data,
                "ip_address": self.ip_address,
                "user_agent": self.user_agent,
                "created_at": self.created_at,
            }
        )
