from flask import abort

from ..database import export_user_entries_to_csv, get_db
from ..models.entries import DailyEntryPayload


def validate_entry_form(form) -> DailyEntryPayload:
    try:
        payload = DailyEntryPayload(
            entry_date=form["entry_date"],
            sleep_hours=float(form["sleep_hours"]),
            study_hours=float(form["study_hours"]),
            exercise_minutes=int(form["exercise_minutes"]),
            reading_hours=float(form.get("reading_hours", 0) or 0),
            leisure_hours=float(form.get("leisure_hours", 0) or 0),
            mood_score=int(form["mood_score"]),
            progress_percent=int(form["progress_percent"]),
            energy_level=int(form["energy_level"]),
            notes=form.get("notes", "").strip(),
        )
    except (KeyError, ValueError):
        abort(400, "Dados do registro invalidos.")

    if not payload.entry_date:
        abort(400, "A data do registro e obrigatoria.")
    if not 0 <= payload.sleep_hours <= 24:
        abort(400, "Sono deve estar entre 0 e 24 horas.")
    if not 0 <= payload.study_hours <= 16:
        abort(400, "Estudo deve estar entre 0 e 16 horas.")
    if not 0 <= payload.exercise_minutes <= 300:
        abort(400, "Exercicio deve estar entre 0 e 300 minutos.")
    if not 0 <= payload.reading_hours <= 12:
        abort(400, "Leitura deve estar entre 0 e 12 horas.")
    if not 0 <= payload.leisure_hours <= 12:
        abort(400, "Lazer deve estar entre 0 e 12 horas.")
    if not 1 <= payload.mood_score <= 10:
        abort(400, "Humor deve estar entre 1 e 10.")
    if not 0 <= payload.progress_percent <= 100:
        abort(400, "Progresso deve estar entre 0 e 100.")
    if not 1 <= payload.energy_level <= 10:
        abort(400, "Energia deve estar entre 1 e 10.")
    return payload


def create_entry(user_id: int, payload: DailyEntryPayload):
    db = get_db()
    db.execute(
        """
        INSERT INTO daily_entries (
            user_id, entry_date, sleep_hours, study_hours, exercise_minutes,
            reading_hours, leisure_hours, mood_score, progress_percent, energy_level, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            payload.entry_date,
            payload.sleep_hours,
            payload.study_hours,
            payload.exercise_minutes,
            payload.reading_hours,
            payload.leisure_hours,
            payload.mood_score,
            payload.progress_percent,
            payload.energy_level,
            payload.notes,
        ),
    )
    db.commit()
    export_user_entries_to_csv(user_id)


def update_entry(user_id: int, entry_id: int, payload: DailyEntryPayload):
    db = get_db()
    db.execute(
        """
        UPDATE daily_entries
        SET entry_date = ?, sleep_hours = ?, study_hours = ?, exercise_minutes = ?,
            reading_hours = ?, leisure_hours = ?, mood_score = ?, progress_percent = ?,
            energy_level = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
        """,
        (
            payload.entry_date,
            payload.sleep_hours,
            payload.study_hours,
            payload.exercise_minutes,
            payload.reading_hours,
            payload.leisure_hours,
            payload.mood_score,
            payload.progress_percent,
            payload.energy_level,
            payload.notes,
            entry_id,
            user_id,
        ),
    )
    db.commit()
    export_user_entries_to_csv(user_id)


def delete_entry(user_id: int, entry_id: int):
    db = get_db()
    db.execute("DELETE FROM daily_entries WHERE id = ? AND user_id = ?", (entry_id, user_id))
    db.commit()
    export_user_entries_to_csv(user_id)


def get_entry(user_id: int, entry_id: int):
    db = get_db()
    entry = db.execute(
        "SELECT * FROM daily_entries WHERE id = ? AND user_id = ?",
        (entry_id, user_id),
    ).fetchone()
    if entry is None:
        abort(404, "Registro nao encontrado.")
    return entry


def list_entries(user_id: int):
    db = get_db()
    return db.execute(
        "SELECT * FROM daily_entries WHERE user_id = ? ORDER BY entry_date DESC",
        (user_id,),
    ).fetchall()
