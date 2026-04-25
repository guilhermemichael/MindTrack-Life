from __future__ import annotations

from datetime import date, timedelta
from math import sqrt

from flask import current_app
from sqlalchemy import text

from ..database import db
from ..models.analytics_snapshot import AnalyticsSnapshot
from ..models.entry import DailyEntry
from ..utils.cache import get as cache_get
from ..utils.cache import set as cache_set


def _average(values):
    return round(sum(values) / len(values), 2) if values else 0


def _min_value(values):
    return round(min(values), 2) if values else 0


def _max_value(values):
    return round(max(values), 2) if values else 0


def _to_float(value):
    return float(value or 0)


def _pearson(x_values, y_values):
    if len(x_values) < 3 or len(x_values) != len(y_values):
        return None
    mean_x = sum(x_values) / len(x_values)
    mean_y = sum(y_values) / len(y_values)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
    denominator = sqrt(sum((x - mean_x) ** 2 for x in x_values) * sum((y - mean_y) ** 2 for y in y_values))
    if denominator == 0:
        return None
    return round(numerator / denominator, 2)


def _delta(current_values, previous_values):
    if not current_values and not previous_values:
        return 0
    return round(_average(current_values) - _average(previous_values), 2)


def _is_productive(entry_dict: dict) -> bool:
    return (
        entry_dict["study_hours"] >= 1
        or entry_dict["exercise_minutes"] >= 20
        or entry_dict["progress_score"] >= 40
        or entry_dict["productivity_score"] >= 60
    )


def _streaks(history: list[dict]) -> tuple[int, int]:
    best = current = 0
    rolling = 0

    for item in history:
        if _is_productive(item):
            rolling += 1
            best = max(best, rolling)
        else:
            rolling = 0

    for item in reversed(history):
        if _is_productive(item):
            current += 1
        else:
            break

    return current, best


def _life_score(avg_sleep: float, avg_study: float, avg_mood: float) -> int:
    score = 0
    score += min(avg_sleep / 8, 1) * 30
    score += min(avg_study / 4, 1) * 30
    score += (avg_mood / 10) * 40
    return round(score)


def _profile_name(life_score: int) -> str:
    if life_score > 75:
        return "Produtivo Consistente"
    if life_score > 50:
        return "Equilibrado"
    return "Oscilante"


def _comparison_block(label: str, current_values, previous_values):
    return {
        "label": label,
        "current": _average(current_values),
        "previous": _average(previous_values),
        "delta": _delta(current_values, previous_values),
    }


def _entries_to_history(entries: list[DailyEntry]) -> list[dict]:
    return [entry.to_dict() for entry in entries]


def _period_bounds(entries: list[DailyEntry], period_type: str):
    if not entries:
        return None, None, []

    latest_date = entries[-1].entry_date
    if period_type == "all_time":
        return entries[0].entry_date, latest_date, entries
    if period_type == "weekly":
        start = latest_date - timedelta(days=latest_date.weekday())
        rows = [entry for entry in entries if entry.entry_date >= start]
        return start, latest_date, rows
    if period_type == "monthly":
        start = latest_date.replace(day=1)
        rows = [entry for entry in entries if entry.entry_date >= start]
        return start, latest_date, rows
    raise ValueError(f"Unsupported period_type: {period_type}")


def refresh_analytics_snapshots(user_id: str) -> dict:
    entries = DailyEntry.query.filter_by(user_id=user_id).order_by(DailyEntry.entry_date.asc()).all()
    history = _entries_to_history(entries)

    if not entries:
        AnalyticsSnapshot.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return get_analytics_snapshot(user_id, force_refresh=True)

    valid_keys = set()
    current_streak, _ = _streaks(history)

    for period_type in ("all_time", "weekly", "monthly"):
        period_start, period_end, scoped_entries = _period_bounds(entries, period_type)
        if not scoped_entries:
            continue

        snapshot = AnalyticsSnapshot.query.filter_by(
            user_id=user_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
        ).first()

        if snapshot is None:
            snapshot = AnalyticsSnapshot(
                user_id=user_id,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
            )
            db.session.add(snapshot)

        sleep_values = [_to_float(entry.sleep_hours) for entry in scoped_entries]
        study_values = [_to_float(entry.study_hours) for entry in scoped_entries]
        mood_values = [entry.mood_score for entry in scoped_entries]
        productivity_values = [entry.productivity_score for entry in scoped_entries]
        progress_values = [entry.progress_score for entry in scoped_entries]

        snapshot.avg_sleep = _average(sleep_values)
        snapshot.avg_study = _average(study_values)
        snapshot.avg_mood = _average(mood_values)
        snapshot.avg_productivity = _average(productivity_values)
        snapshot.avg_progress = _average(progress_values)
        snapshot.life_score = _life_score(snapshot.avg_sleep, snapshot.avg_study, snapshot.avg_mood)
        snapshot.consistency_streak = current_streak if period_type == "all_time" else _streaks([entry.to_dict() for entry in scoped_entries])[0]
        valid_keys.add((period_type, period_start, period_end))

    for snapshot in AnalyticsSnapshot.query.filter_by(user_id=user_id).all():
        key = (snapshot.period_type, snapshot.period_start, snapshot.period_end)
        if key not in valid_keys:
            db.session.delete(snapshot)

    db.session.commit()
    return get_analytics_snapshot(user_id, force_refresh=True)


def refresh_materialized_views():
    # Placeholder hook for future materialized view refreshes in PostgreSQL.
    return None


def _latest_snapshot(user_id: str, period_type: str) -> AnalyticsSnapshot | None:
    return (
        AnalyticsSnapshot.query.filter_by(user_id=user_id, period_type=period_type)
        .order_by(AnalyticsSnapshot.period_end.desc())
        .first()
    )


def _query_weekly_summary_view(user_id: str):
    try:
        row = db.session.execute(
            text(
                """
                SELECT avg_sleep, avg_study, avg_mood, avg_productivity, avg_progress, total_entries
                FROM weekly_user_summary
                WHERE user_id = :user_id
                ORDER BY week_start DESC
                LIMIT 1
                """
            ),
            {"user_id": user_id},
        ).mappings().first()
        return dict(row) if row else None
    except Exception:
        return None


def _query_productivity_drop(user_id: str):
    dialect = db.session.bind.dialect.name if db.session.bind is not None else ""
    if dialect == "postgresql":
        sql = """
        WITH weekly AS (
            SELECT
                user_id,
                DATE_TRUNC('week', entry_date) AS week_start,
                AVG(productivity_score) AS avg_productivity
            FROM daily_entries
            WHERE user_id = :user_id
            GROUP BY user_id, DATE_TRUNC('week', entry_date)
        ),
        ranked AS (
            SELECT *, LAG(avg_productivity) OVER (ORDER BY week_start) AS previous_week
            FROM weekly
        )
        SELECT week_start, avg_productivity, previous_week,
               ROUND(avg_productivity - previous_week, 2) AS difference
        FROM ranked
        ORDER BY week_start DESC
        LIMIT 1
        """
    else:
        sql = """
        WITH weekly AS (
            SELECT
                user_id,
                MIN(entry_date) AS week_start,
                AVG(productivity_score) AS avg_productivity
            FROM daily_entries
            WHERE user_id = :user_id
            GROUP BY user_id, strftime('%Y-%W', entry_date)
        ),
        ranked AS (
            SELECT *, LAG(avg_productivity) OVER (ORDER BY week_start) AS previous_week
            FROM weekly
        )
        SELECT week_start, avg_productivity, previous_week,
               ROUND(avg_productivity - previous_week, 2) AS difference
        FROM ranked
        ORDER BY week_start DESC
        LIMIT 1
        """
    try:
        row = db.session.execute(text(sql), {"user_id": user_id}).mappings().first()
        return dict(row) if row else None
    except Exception:
        return None


def get_analytics_snapshot(user_id: str, force_refresh: bool = False) -> dict:
    cache_key = f"analytics:{user_id}:snapshot"
    if not force_refresh:
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

    entries = DailyEntry.query.filter_by(user_id=user_id).order_by(DailyEntry.entry_date.asc()).all()
    history = _entries_to_history(entries)
    all_time_snapshot = _latest_snapshot(user_id, "all_time")
    weekly_snapshot = _latest_snapshot(user_id, "weekly")
    monthly_snapshot = _latest_snapshot(user_id, "monthly")
    weekly_summary_view = _query_weekly_summary_view(user_id)
    productivity_drop = _query_productivity_drop(user_id)

    empty_payload = {
        "summary": {
            "life_score": 0,
            "profile": "Sem dados suficientes",
            "avg_mood": 0,
            "avg_sleep": 0,
            "avg_study": 0,
            "avg_progress": 0,
            "avg_productivity": 0,
            "avg_energy": 0,
            "current_streak": 0,
            "best_streak": 0,
            "weekly_goal_progress": 0,
            "latest_mood": 0,
        },
        "metrics": {
            "min_mood": 0,
            "max_mood": 0,
            "min_progress": 0,
            "max_progress": 0,
        },
        "correlations": {
            "sleep_mood": None,
            "study_progress": None,
            "exercise_mood": None,
        },
        "comparisons": {
            "mood": {"label": "Humor", "current": 0, "previous": 0, "delta": 0},
            "sleep": {"label": "Sono", "current": 0, "previous": 0, "delta": 0},
            "progress": {"label": "Progresso", "current": 0, "previous": 0, "delta": 0},
            "productivity": {"label": "Produtividade", "current": 0, "previous": 0, "delta": 0},
        },
        "gamification": {
            "days_to_new_record": 0,
            "weekly_productive_days": 0,
        },
        "database_architecture": {
            "weekly_summary_view": weekly_summary_view,
            "productivity_drop": productivity_drop,
            "snapshots": [],
        },
        "charts": {
            "labels": [],
            "mood": [],
            "sleep": [],
            "progress": [],
            "productivity": [],
            "study": [],
            "exercise": [],
            "weekly_labels": ["Semana atual", "Semana anterior"],
            "weekly_mood": [0, 0],
            "weekly_progress": [0, 0],
            "weekly_productivity": [0, 0],
        },
        "history": [],
        "mood_values": [],
    }

    if not entries:
        return cache_set(cache_key, empty_payload, ttl=current_app.config["CACHE_TTL_SECONDS"])

    if not force_refresh and all_time_snapshot is None:
        return refresh_analytics_snapshots(user_id)

    mood_values = [entry.mood_score for entry in entries]
    sleep_values = [_to_float(entry.sleep_hours) for entry in entries]
    study_values = [_to_float(entry.study_hours) for entry in entries]
    progress_values = [entry.progress_score for entry in entries]
    productivity_values = [entry.productivity_score for entry in entries]
    exercise_values = [entry.exercise_minutes for entry in entries]
    energy_values = [entry.energy_level for entry in entries]

    current_week = history[-7:]
    previous_week = history[-14:-7]
    current_streak, best_streak = _streaks(history)
    productive_recent = sum(1 for item in current_week if _is_productive(item))
    avg_energy = _average(energy_values)

    avg_mood = float(all_time_snapshot.avg_mood) if all_time_snapshot and all_time_snapshot.avg_mood is not None else _average(mood_values)
    avg_sleep = float(all_time_snapshot.avg_sleep) if all_time_snapshot and all_time_snapshot.avg_sleep is not None else _average(sleep_values)
    avg_study = float(all_time_snapshot.avg_study) if all_time_snapshot and all_time_snapshot.avg_study is not None else _average(study_values)
    avg_progress = float(all_time_snapshot.avg_progress) if all_time_snapshot and all_time_snapshot.avg_progress is not None else _average(progress_values)
    avg_productivity = float(all_time_snapshot.avg_productivity) if all_time_snapshot and all_time_snapshot.avg_productivity is not None else _average(productivity_values)
    life_score = all_time_snapshot.life_score if all_time_snapshot and all_time_snapshot.life_score is not None else _life_score(avg_sleep, avg_study, avg_mood)
    weekly_goal_progress = round((productive_recent / 7) * 100) if current_week else 0
    days_to_new_record = 0 if current_streak > best_streak else max(best_streak - current_streak + 1, 1)

    payload = {
        "summary": {
            "life_score": life_score,
            "profile": _profile_name(life_score),
            "avg_mood": avg_mood,
            "avg_sleep": avg_sleep,
            "avg_study": avg_study,
            "avg_progress": avg_progress,
            "avg_productivity": avg_productivity,
            "avg_energy": avg_energy,
            "current_streak": current_streak,
            "best_streak": best_streak,
            "weekly_goal_progress": weekly_goal_progress,
            "latest_mood": history[-1]["mood_score"],
        },
        "metrics": {
            "min_mood": _min_value(mood_values),
            "max_mood": _max_value(mood_values),
            "min_progress": _min_value(progress_values),
            "max_progress": _max_value(progress_values),
        },
        "correlations": {
            "sleep_mood": _pearson(sleep_values, mood_values),
            "study_progress": _pearson(study_values, progress_values),
            "exercise_mood": _pearson(exercise_values, mood_values),
        },
        "comparisons": {
            "mood": _comparison_block("Humor", [item["mood_score"] for item in current_week], [item["mood_score"] for item in previous_week]),
            "sleep": _comparison_block("Sono", [item["sleep_hours"] for item in current_week], [item["sleep_hours"] for item in previous_week]),
            "progress": _comparison_block("Progresso", [item["progress_score"] for item in current_week], [item["progress_score"] for item in previous_week]),
            "productivity": _comparison_block("Produtividade", [item["productivity_score"] for item in current_week], [item["productivity_score"] for item in previous_week]),
        },
        "gamification": {
            "days_to_new_record": days_to_new_record,
            "weekly_productive_days": productive_recent,
        },
        "database_architecture": {
            "weekly_summary_view": weekly_summary_view,
            "productivity_drop": productivity_drop,
            "snapshots": [snapshot.to_dict() for snapshot in (all_time_snapshot, weekly_snapshot, monthly_snapshot) if snapshot is not None],
        },
        "charts": {
            "labels": [item["entry_date"] for item in history],
            "mood": mood_values,
            "sleep": sleep_values,
            "progress": progress_values,
            "productivity": productivity_values,
            "study": study_values,
            "exercise": exercise_values,
            "weekly_labels": ["Semana atual", "Semana anterior"],
            "weekly_mood": [_average([item["mood_score"] for item in current_week]), _average([item["mood_score"] for item in previous_week])],
            "weekly_progress": [_average([item["progress_score"] for item in current_week]), _average([item["progress_score"] for item in previous_week])],
            "weekly_productivity": [_average([item["productivity_score"] for item in current_week]), _average([item["productivity_score"] for item in previous_week])],
        },
        "history": list(reversed(history)),
        "mood_values": mood_values,
    }

    return cache_set(cache_key, payload, ttl=current_app.config["CACHE_TTL_SECONDS"])
