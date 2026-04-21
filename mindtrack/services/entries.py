import csv
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Mapping

from flask import current_app

from ..database import db
from ..models.entry import DailyEntry, EntryPayload
from ..utils.cache import invalidate_prefix


class ValidationError(ValueError):
    pass


def _get_value(data: Mapping, key: str, default=None):
    if hasattr(data, "get"):
        return data.get(key, default)
    return default if default is not None else data[key]


def validate_entry_payload(data: Mapping) -> EntryPayload:
    try:
        entry_date = str(_get_value(data, "entry_date", "")).strip()
        date.fromisoformat(entry_date)
        payload = EntryPayload(
            entry_date=entry_date,
            sleep_hours=float(_get_value(data, "sleep_hours")),
            study_hours=float(_get_value(data, "study_hours")),
            exercise_minutes=int(_get_value(data, "exercise_minutes", 0)),
            reading_hours=float(_get_value(data, "reading_hours", 0) or 0),
            leisure_hours=float(_get_value(data, "leisure_hours", 0) or 0),
            mood_score=int(_get_value(data, "mood_score")),
            progress_percent=int(_get_value(data, "progress_percent")),
            energy_level=int(_get_value(data, "energy_level")),
            notes=str(_get_value(data, "notes", "")).strip(),
        )
    except (TypeError, ValueError, KeyError):
        raise ValidationError("Dados do registro invalidos.")

    if not payload.entry_date:
        raise ValidationError("A data do registro e obrigatoria.")
    if not 0 <= payload.sleep_hours <= 24:
        raise ValidationError("Sono deve estar entre 0 e 24 horas.")
    if not 0 <= payload.study_hours <= 16:
        raise ValidationError("Estudo deve estar entre 0 e 16 horas.")
    if not 0 <= payload.exercise_minutes <= 300:
        raise ValidationError("Exercicio deve estar entre 0 e 300 minutos.")
    if not 0 <= payload.reading_hours <= 12:
        raise ValidationError("Leitura deve estar entre 0 e 12 horas.")
    if not 0 <= payload.leisure_hours <= 12:
        raise ValidationError("Lazer deve estar entre 0 e 12 horas.")
    if not 1 <= payload.mood_score <= 10:
        raise ValidationError("Humor deve estar entre 1 e 10.")
    if not 0 <= payload.progress_percent <= 100:
        raise ValidationError("Progresso deve estar entre 0 e 100.")
    if not 1 <= payload.energy_level <= 10:
        raise ValidationError("Energia deve estar entre 1 e 10.")
    if len(payload.notes) > 600:
        raise ValidationError("As notas devem ter no maximo 600 caracteres.")
    return payload


def _touch_user_cache(user_id: int):
    invalidate_prefix(f"analytics:{user_id}")


def create_entry(user_id: int, payload: EntryPayload) -> DailyEntry:
    entry = DailyEntry(user_id=user_id, **asdict(payload))
    db.session.add(entry)
    db.session.commit()
    _touch_user_cache(user_id)
    return entry


def list_entries(user_id: int, descending: bool = True) -> list[DailyEntry]:
    order_by = DailyEntry.entry_date.desc() if descending else DailyEntry.entry_date.asc()
    return list(DailyEntry.query.filter_by(user_id=user_id).order_by(order_by).all())


def get_entry(user_id: int, entry_id: int) -> DailyEntry | None:
    return DailyEntry.query.filter_by(id=entry_id, user_id=user_id).first()


def get_latest_entry(user_id: int) -> DailyEntry | None:
    return DailyEntry.query.filter_by(user_id=user_id).order_by(DailyEntry.entry_date.desc()).first()


def update_entry(user_id: int, entry_id: int, payload: EntryPayload) -> DailyEntry | None:
    entry = get_entry(user_id, entry_id)
    if entry is None:
        return None

    for field, value in asdict(payload).items():
        setattr(entry, field, value)

    db.session.commit()
    _touch_user_cache(user_id)
    return entry


def delete_entry(user_id: int, entry_id: int) -> bool:
    entry = get_entry(user_id, entry_id)
    if entry is None:
        return False

    db.session.delete(entry)
    db.session.commit()
    _touch_user_cache(user_id)
    return True


def export_entries_csv(user_id: int) -> Path:
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
                "reading_hours",
                "leisure_hours",
                "mood_score",
                "progress_percent",
                "energy_level",
                "notes",
            ]
        )
        for entry in list_entries(user_id, descending=False):
            writer.writerow(
                [
                    entry.entry_date,
                    entry.sleep_hours,
                    entry.study_hours,
                    entry.exercise_minutes,
                    entry.reading_hours,
                    entry.leisure_hours,
                    entry.mood_score,
                    entry.progress_percent,
                    entry.energy_level,
                    entry.notes,
                ]
            )

    return export_path
