import csv
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Mapping

from flask import current_app

from ..database import db
from ..models.entry import DailyEntry, EntryPayload
from ..utils.cache import invalidate_prefix
from .audit import record_audit_log


class ValidationError(ValueError):
    pass


def _get_value(data: Mapping, key: str, default=None):
    if hasattr(data, "get"):
        return data.get(key, default)
    return default if default is not None else data[key]


def _compute_productivity_score(*, study_hours: float, exercise_minutes: int, mood_score: int, progress_score: int) -> int:
    score = 0
    score += min(study_hours / 4, 1) * 35
    score += min(exercise_minutes / 45, 1) * 15
    score += (mood_score / 10) * 20
    score += (progress_score / 100) * 30
    return round(min(score, 100))


def validate_entry_payload(data: Mapping) -> EntryPayload:
    try:
        entry_date = date.fromisoformat(str(_get_value(data, "entry_date", "")).strip())
        progress_score = int(_get_value(data, "progress_score", _get_value(data, "progress_percent", 0)))
        productivity_value = _get_value(data, "productivity_score", None)
        productivity_score = int(productivity_value) if productivity_value not in (None, "") else None
        payload = EntryPayload(
            entry_date=entry_date,
            sleep_hours=float(_get_value(data, "sleep_hours")),
            study_hours=float(_get_value(data, "study_hours")),
            exercise_minutes=int(_get_value(data, "exercise_minutes", 0)),
            mood_score=int(_get_value(data, "mood_score")),
            productivity_score=productivity_score or 0,
            progress_score=progress_score,
            reading_hours=float(_get_value(data, "reading_hours", 0) or 0),
            leisure_hours=float(_get_value(data, "leisure_hours", 0) or 0),
            energy_level=int(_get_value(data, "energy_level", 5)),
            notes=str(_get_value(data, "notes", "")).strip(),
        )
    except (TypeError, ValueError, KeyError):
        raise ValidationError("Dados do registro invalidos.")

    if not 0 <= payload.sleep_hours <= 24:
        raise ValidationError("Sono deve estar entre 0 e 24 horas.")
    if not 0 <= payload.study_hours <= 24:
        raise ValidationError("Estudo deve estar entre 0 e 24 horas.")
    if not 0 <= payload.exercise_minutes <= 600:
        raise ValidationError("Exercicio deve estar entre 0 e 600 minutos.")
    if not 1 <= payload.mood_score <= 10:
        raise ValidationError("Humor deve estar entre 1 e 10.")
    if not 0 <= payload.progress_score <= 100:
        raise ValidationError("Progresso deve estar entre 0 e 100.")
    if not 0 <= payload.reading_hours <= 24:
        raise ValidationError("Leitura deve estar entre 0 e 24 horas.")
    if not 0 <= payload.leisure_hours <= 24:
        raise ValidationError("Lazer deve estar entre 0 e 24 horas.")
    if not 1 <= payload.energy_level <= 10:
        raise ValidationError("Energia deve estar entre 1 e 10.")
    if len(payload.notes) > 600:
        raise ValidationError("As notas devem ter no maximo 600 caracteres.")

    if payload.productivity_score == 0 and (payload.study_hours > 0 or payload.progress_score > 0 or payload.mood_score > 0):
        payload.productivity_score = _compute_productivity_score(
            study_hours=payload.study_hours,
            exercise_minutes=payload.exercise_minutes,
            mood_score=payload.mood_score,
            progress_score=payload.progress_score,
        )

    if not 0 <= payload.productivity_score <= 100:
        raise ValidationError("Produtividade deve estar entre 0 e 100.")
    return payload


def _touch_user_cache(user_id: str):
    invalidate_prefix(f"analytics:{user_id}")


def _refresh_user_intelligence(user_id: str):
    from .analytics import refresh_analytics_snapshots, refresh_materialized_views
    from .forecast import predict_mood
    from .insights import sync_persisted_insights

    analytics = refresh_analytics_snapshots(user_id)
    refresh_materialized_views()
    forecast = predict_mood(analytics["mood_values"])
    sync_persisted_insights(user_id, analytics, forecast)


def create_entry(user_id: str, payload: EntryPayload) -> DailyEntry:
    entry = DailyEntry(user_id=user_id, **asdict(payload))
    db.session.add(entry)
    db.session.flush()
    record_audit_log(
        user_id=user_id,
        action="entry.created",
        entity_name="daily_entries",
        entity_id=entry.id,
        new_data=entry.to_dict(),
    )
    db.session.commit()
    _touch_user_cache(user_id)
    _refresh_user_intelligence(user_id)
    return entry


def list_entries(user_id: str, descending: bool = True) -> list[DailyEntry]:
    order_by = DailyEntry.entry_date.desc() if descending else DailyEntry.entry_date.asc()
    return list(DailyEntry.query.filter_by(user_id=user_id).order_by(order_by).all())


def get_entry(user_id: str, entry_id: str) -> DailyEntry | None:
    return DailyEntry.query.filter_by(id=entry_id, user_id=user_id).first()


def get_latest_entry(user_id: str) -> DailyEntry | None:
    return DailyEntry.query.filter_by(user_id=user_id).order_by(DailyEntry.entry_date.desc()).first()


def update_entry(user_id: str, entry_id: str, payload: EntryPayload) -> DailyEntry | None:
    entry = get_entry(user_id, entry_id)
    if entry is None:
        return None

    old_data = entry.to_dict()
    for field, value in asdict(payload).items():
        setattr(entry, field, value)

    db.session.flush()
    record_audit_log(
        user_id=user_id,
        action="entry.updated",
        entity_name="daily_entries",
        entity_id=entry.id,
        old_data=old_data,
        new_data=entry.to_dict(),
    )
    db.session.commit()
    _touch_user_cache(user_id)
    _refresh_user_intelligence(user_id)
    return entry


def delete_entry(user_id: str, entry_id: str) -> bool:
    entry = get_entry(user_id, entry_id)
    if entry is None:
        return False

    old_data = entry.to_dict()
    record_audit_log(
        user_id=user_id,
        action="entry.deleted",
        entity_name="daily_entries",
        entity_id=entry.id,
        old_data=old_data,
        new_data=None,
    )
    db.session.delete(entry)
    db.session.commit()
    _touch_user_cache(user_id)
    _refresh_user_intelligence(user_id)
    return True


def export_entries_csv(user_id: str) -> Path:
    export_dir = Path(current_app.config["EXPORT_DIR"])
    export_dir.mkdir(parents=True, exist_ok=True)
    export_path = export_dir / f"user_{user_id}_entries.csv"

    with export_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "date",
                "sleep_hours",
                "study_hours",
                "exercise_minutes",
                "mood_score",
                "productivity_score",
                "progress_score",
                "reading_hours",
                "leisure_hours",
                "energy_level",
                "notes",
            ]
        )
        for entry in list_entries(user_id, descending=False):
            writer.writerow(
                [
                    entry.entry_date.isoformat(),
                    float(entry.sleep_hours),
                    float(entry.study_hours),
                    entry.exercise_minutes,
                    entry.mood_score,
                    entry.productivity_score,
                    entry.progress_score,
                    float(entry.reading_hours),
                    float(entry.leisure_hours),
                    entry.energy_level,
                    entry.notes or "",
                ]
            )

    return export_path
