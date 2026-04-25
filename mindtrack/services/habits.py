from datetime import date
from typing import Mapping

from ..database import db
from ..models.habit import Habit
from ..models.habit_log import HabitLog
from .audit import record_audit_log
from .entries import ValidationError


def _get_value(data: Mapping, key: str, default=None):
    if hasattr(data, "get"):
        return data.get(key, default)
    return default if default is not None else data[key]


def validate_habit_payload(data: Mapping) -> dict:
    name = str(_get_value(data, "name", "")).strip()
    category = str(_get_value(data, "category", "")).strip() or None
    unit = str(_get_value(data, "unit", "")).strip() or None
    is_active = bool(_get_value(data, "is_active", True))
    target_value_raw = _get_value(data, "target_value", None)
    target_value = float(target_value_raw) if target_value_raw not in (None, "") else None

    if not name:
        raise ValidationError("O habito precisa de um nome.")
    if target_value is not None and target_value < 0:
        raise ValidationError("A meta do habito nao pode ser negativa.")

    return {
        "name": name,
        "category": category,
        "unit": unit,
        "is_active": is_active,
        "target_value": target_value,
    }


def validate_habit_log_payload(data: Mapping) -> dict:
    try:
        habit_id = str(_get_value(data, "habit_id")).strip()
        log_date = date.fromisoformat(str(_get_value(data, "log_date")).strip())
        value = float(_get_value(data, "value", 0) or 0)
        completed = bool(_get_value(data, "completed", False))
    except (TypeError, ValueError, KeyError):
        raise ValidationError("Dados do log de habito invalidos.")

    if not habit_id:
        raise ValidationError("O log precisa de um habito.")
    if value < 0:
        raise ValidationError("O valor do log nao pode ser negativo.")

    return {
        "habit_id": habit_id,
        "log_date": log_date,
        "value": value,
        "completed": completed,
    }


def list_habits(user_id: str) -> list[Habit]:
    return Habit.query.filter_by(user_id=user_id).order_by(Habit.created_at.desc()).all()


def get_habit(user_id: str, habit_id: str) -> Habit | None:
    return Habit.query.filter_by(user_id=user_id, id=habit_id).first()


def create_habit(user_id: str, payload: dict) -> Habit:
    habit = Habit(user_id=user_id, **payload)
    db.session.add(habit)
    db.session.flush()
    record_audit_log(
        user_id=user_id,
        action="habit.created",
        entity_name="habits",
        entity_id=habit.id,
        new_data=habit.to_dict(),
    )
    db.session.commit()
    return habit


def update_habit(user_id: str, habit_id: str, payload: dict) -> Habit | None:
    habit = get_habit(user_id, habit_id)
    if habit is None:
        return None

    old_data = habit.to_dict()
    for field, value in payload.items():
        setattr(habit, field, value)

    db.session.flush()
    record_audit_log(
        user_id=user_id,
        action="habit.updated",
        entity_name="habits",
        entity_id=habit.id,
        old_data=old_data,
        new_data=habit.to_dict(),
    )
    db.session.commit()
    return habit


def delete_habit(user_id: str, habit_id: str) -> bool:
    habit = get_habit(user_id, habit_id)
    if habit is None:
        return False

    record_audit_log(
        user_id=user_id,
        action="habit.deleted",
        entity_name="habits",
        entity_id=habit.id,
        old_data=habit.to_dict(),
    )
    db.session.delete(habit)
    db.session.commit()
    return True


def list_habit_logs(user_id: str) -> list[HabitLog]:
    return HabitLog.query.filter_by(user_id=user_id).order_by(HabitLog.log_date.desc()).all()


def create_habit_log(user_id: str, payload: dict) -> HabitLog:
    habit = get_habit(user_id, payload["habit_id"])
    if habit is None:
        raise ValidationError("Habito nao encontrado.")

    log = HabitLog.query.filter_by(habit_id=habit.id, log_date=payload["log_date"]).first()
    if log is None:
        log = HabitLog(user_id=user_id, **payload)
        db.session.add(log)
        action = "habit_log.created"
        old_data = None
    else:
        old_data = log.to_dict()
        log.value = payload["value"]
        log.completed = payload["completed"]
        action = "habit_log.updated"

    db.session.flush()
    record_audit_log(
        user_id=user_id,
        action=action,
        entity_name="habit_logs",
        entity_id=log.id,
        old_data=old_data,
        new_data=log.to_dict(),
    )
    db.session.commit()
    return log
