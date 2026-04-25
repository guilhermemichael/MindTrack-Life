from datetime import date
from typing import Mapping

from ..database import db
from ..models.goal import Goal
from .audit import record_audit_log
from .entries import ValidationError


def _get_value(data: Mapping, key: str, default=None):
    if hasattr(data, "get"):
        return data.get(key, default)
    return default if default is not None else data[key]


def validate_goal_payload(data: Mapping) -> dict:
    title = str(_get_value(data, "title", "")).strip()
    description = str(_get_value(data, "description", "")).strip() or None
    category = str(_get_value(data, "category", "")).strip() or None
    unit = str(_get_value(data, "unit", "")).strip() or None
    status = str(_get_value(data, "status", "active")).strip() or "active"
    target_raw = _get_value(data, "target_value", None)
    current_raw = _get_value(data, "current_value", 0)
    start_raw = str(_get_value(data, "start_date", "")).strip()
    deadline_raw = str(_get_value(data, "deadline", "")).strip()

    if not title:
        raise ValidationError("A meta precisa de um titulo.")

    target_value = float(target_raw) if target_raw not in (None, "") else None
    current_value = float(current_raw) if current_raw not in (None, "") else 0
    if target_value is not None and target_value < 0:
        raise ValidationError("O valor alvo nao pode ser negativo.")
    if current_value < 0:
        raise ValidationError("O valor atual nao pode ser negativo.")

    start_date = date.fromisoformat(start_raw) if start_raw else None
    deadline = date.fromisoformat(deadline_raw) if deadline_raw else None

    return {
        "title": title,
        "description": description,
        "category": category,
        "target_value": target_value,
        "current_value": current_value,
        "unit": unit,
        "status": status,
        "start_date": start_date,
        "deadline": deadline,
    }


def list_goals(user_id: str) -> list[Goal]:
    return Goal.query.filter_by(user_id=user_id).order_by(Goal.created_at.desc()).all()


def get_goal(user_id: str, goal_id: str) -> Goal | None:
    return Goal.query.filter_by(user_id=user_id, id=goal_id).first()


def create_goal(user_id: str, payload: dict) -> Goal:
    goal = Goal(user_id=user_id, **payload)
    db.session.add(goal)
    db.session.flush()
    record_audit_log(
        user_id=user_id,
        action="goal.created",
        entity_name="goals",
        entity_id=goal.id,
        new_data=goal.to_dict(),
    )
    db.session.commit()
    return goal


def update_goal(user_id: str, goal_id: str, payload: dict) -> Goal | None:
    goal = get_goal(user_id, goal_id)
    if goal is None:
        return None

    old_data = goal.to_dict()
    for field, value in payload.items():
        setattr(goal, field, value)

    db.session.flush()
    record_audit_log(
        user_id=user_id,
        action="goal.updated",
        entity_name="goals",
        entity_id=goal.id,
        old_data=old_data,
        new_data=goal.to_dict(),
    )
    db.session.commit()
    return goal


def delete_goal(user_id: str, goal_id: str) -> bool:
    goal = get_goal(user_id, goal_id)
    if goal is None:
        return False

    record_audit_log(
        user_id=user_id,
        action="goal.deleted",
        entity_name="goals",
        entity_id=goal.id,
        old_data=goal.to_dict(),
    )
    db.session.delete(goal)
    db.session.commit()
    return True
