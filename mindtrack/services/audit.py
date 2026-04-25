from flask import has_request_context, request

from ..database import db
from ..models.audit_log import AuditLog
from ..utils.helpers import serialize_mapping


def record_audit_log(
    *,
    user_id: str | None,
    action: str,
    entity_name: str | None,
    entity_id: str | None = None,
    old_data: dict | None = None,
    new_data: dict | None = None,
):
    ip_address = request.remote_addr if has_request_context() else None
    user_agent = request.headers.get("User-Agent") if has_request_context() else None
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_name=entity_name,
        entity_id=entity_id,
        old_data=serialize_mapping(old_data),
        new_data=serialize_mapping(new_data),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.session.add(log)
    return log
