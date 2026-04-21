from math import sqrt

from flask import current_app

from ..models.entry import DailyEntry
from ..utils.cache import get as cache_get
from ..utils.cache import set as cache_set


def _average(values):
    return round(sum(values) / len(values), 2) if values else 0


def _min_value(values):
    return round(min(values), 2) if values else 0


def _max_value(values):
    return round(max(values), 2) if values else 0


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
        or entry_dict["progress_percent"] >= 40
        or entry_dict["reading_hours"] >= 0.5
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


def get_analytics_snapshot(user_id: int, force_refresh: bool = False) -> dict:
    cache_key = f"analytics:{user_id}:snapshot"
    if not force_refresh:
        cached = cache_get(cache_key)
        if cached is not None:
            return cached

    entries = (
        DailyEntry.query.filter_by(user_id=user_id)
        .order_by(DailyEntry.entry_date.asc())
        .all()
    )

    history = [entry.to_dict() for entry in entries]
    empty_payload = {
        "summary": {
            "life_score": 0,
            "profile": "Sem dados suficientes",
            "avg_mood": 0,
            "avg_sleep": 0,
            "avg_study": 0,
            "avg_progress": 0,
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
        },
        "gamification": {
            "days_to_new_record": 0,
            "weekly_productive_days": 0,
        },
        "charts": {
            "labels": [],
            "mood": [],
            "sleep": [],
            "progress": [],
            "study": [],
            "exercise": [],
            "weekly_labels": ["Semana atual", "Semana anterior"],
            "weekly_mood": [0, 0],
            "weekly_progress": [0, 0],
        },
        "history": [],
        "mood_values": [],
    }

    if not entries:
        return cache_set(cache_key, empty_payload, ttl=current_app.config["CACHE_TTL_SECONDS"])

    mood_values = [entry.mood_score for entry in entries]
    sleep_values = [entry.sleep_hours for entry in entries]
    study_values = [entry.study_hours for entry in entries]
    progress_values = [entry.progress_percent for entry in entries]
    exercise_values = [entry.exercise_minutes for entry in entries]
    energy_values = [entry.energy_level for entry in entries]

    current_week = history[-7:]
    previous_week = history[-14:-7]
    current_streak, best_streak = _streaks(history)
    productive_recent = sum(1 for item in current_week if _is_productive(item))

    avg_mood = _average(mood_values)
    avg_sleep = _average(sleep_values)
    avg_study = _average(study_values)
    avg_progress = _average(progress_values)
    avg_energy = _average(energy_values)
    life_score = _life_score(avg_sleep, avg_study, avg_mood)
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
            "mood": _comparison_block(
                "Humor",
                [item["mood_score"] for item in current_week],
                [item["mood_score"] for item in previous_week],
            ),
            "sleep": _comparison_block(
                "Sono",
                [item["sleep_hours"] for item in current_week],
                [item["sleep_hours"] for item in previous_week],
            ),
            "progress": _comparison_block(
                "Progresso",
                [item["progress_percent"] for item in current_week],
                [item["progress_percent"] for item in previous_week],
            ),
        },
        "gamification": {
            "days_to_new_record": days_to_new_record,
            "weekly_productive_days": productive_recent,
        },
        "charts": {
            "labels": [item["entry_date"] for item in history],
            "mood": mood_values,
            "sleep": sleep_values,
            "progress": progress_values,
            "study": study_values,
            "exercise": exercise_values,
            "weekly_labels": ["Semana atual", "Semana anterior"],
            "weekly_mood": [
                _average([item["mood_score"] for item in current_week]),
                _average([item["mood_score"] for item in previous_week]),
            ],
            "weekly_progress": [
                _average([item["progress_percent"] for item in current_week]),
                _average([item["progress_percent"] for item in previous_week]),
            ],
        },
        "history": list(reversed(history)),
        "mood_values": mood_values,
    }

    return cache_set(cache_key, payload, ttl=current_app.config["CACHE_TTL_SECONDS"])
