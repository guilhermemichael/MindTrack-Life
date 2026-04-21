from math import sqrt

from ..database import get_db


def _average(values):
    return round(sum(values) / len(values), 2) if values else 0


def _pearson(x_values, y_values):
    if len(x_values) < 3 or len(y_values) < 3 or len(x_values) != len(y_values):
        return None
    mean_x = sum(x_values) / len(x_values)
    mean_y = sum(y_values) / len(y_values)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
    denominator = sqrt(sum((x - mean_x) ** 2 for x in x_values) * sum((y - mean_y) ** 2 for y in y_values))
    if denominator == 0:
        return None
    return round(numerator / denominator, 2)


def _trend(old_values, new_values):
    if not old_values and not new_values:
        return 0
    return round(_average(new_values) - _average(old_values), 2)


def _longest_consistency_streak(rows):
    longest = current = 0
    previous_day = None
    for row in rows:
        productive = row["study_hours"] >= 1 or row["exercise_minutes"] >= 20 or row["progress_percent"] >= 40
        if not productive:
            current = 0
            previous_day = row["entry_date"]
            continue
        if previous_day:
            current += 1
        else:
            current = 1
        previous_day = row["entry_date"]
        longest = max(longest, current)
    return longest


def get_dashboard_data(user_id: int):
    db = get_db()
    rows = db.execute(
        """
        SELECT * FROM daily_entries
        WHERE user_id = ?
        ORDER BY entry_date
        """,
        (user_id,),
    ).fetchall()

    if not rows:
        return {
            "summary": {
                "avg_mood": 0,
                "avg_sleep": 0,
                "avg_progress": 0,
                "consistency_streak": 0,
                "life_score": 0,
            },
            "charts": {
                "labels": [],
                "mood": [],
                "sleep": [],
                "progress": [],
                "study": [],
                "exercise": [],
            },
            "insights": [],
            "history": [],
        }

    mood_values = [row["mood_score"] for row in rows]
    sleep_values = [row["sleep_hours"] for row in rows]
    progress_values = [row["progress_percent"] for row in rows]
    study_values = [row["study_hours"] for row in rows]
    exercise_values = [row["exercise_minutes"] for row in rows]
    recent = rows[-7:]
    previous = rows[-14:-7]

    avg_mood = _average(mood_values)
    avg_sleep = _average(sleep_values)
    avg_progress = _average(progress_values)
    avg_study = _average(study_values)
    avg_exercise = _average(exercise_values)
    life_score = round(
        min(
            100,
            (avg_sleep / 8) * 25
            + (avg_mood / 10) * 25
            + (avg_progress / 100) * 30
            + min(avg_exercise / 45, 1) * 10
            + min(avg_study / 4, 1) * 10,
        ),
        1,
    )

    sleep_mood_corr = _pearson(sleep_values, mood_values)
    study_progress_corr = _pearson(study_values, progress_values)
    exercise_mood_corr = _pearson(exercise_values, mood_values)

    insights = []
    if sleep_mood_corr and sleep_mood_corr >= 0.35:
        insights.append("Seu humor tende a melhorar quando voce dorme mais.")
    if study_progress_corr and study_progress_corr >= 0.35:
        insights.append("As horas de estudo estao ligadas a um progresso mais forte.")
    if exercise_mood_corr and exercise_mood_corr >= 0.30:
        insights.append("Exercicio aparece como um gatilho positivo para o seu humor.")

    no_exercise_days = sum(1 for row in recent if row["exercise_minutes"] == 0)
    if no_exercise_days >= 3:
        insights.append("Nos ultimos dias faltou movimento. Retomar exercicio pode destravar energia e foco.")

    low_days = [
        row["entry_date"]
        for row in recent
        if row["progress_percent"] < 30 and row["mood_score"] <= 5
    ]
    if low_days:
        insights.append("Houve sinais recentes de queda emocional junto com baixa execucao. Vale reduzir friccao e priorizar pequenas vitorias.")

    mood_trend = _trend([row["mood_score"] for row in previous], [row["mood_score"] for row in recent])
    progress_trend = _trend([row["progress_percent"] for row in previous], [row["progress_percent"] for row in recent])

    if mood_trend > 0.4:
        insights.append("Seu humor medio subiu na janela mais recente. Ha um movimento real de melhora.")
    elif mood_trend < -0.4:
        insights.append("Seu humor medio caiu na janela mais recente. Talvez seja hora de rever descanso e carga.")

    if progress_trend > 5:
        insights.append("Sua execucao esta acelerando. O sistema mostra mais consistencia na ultima semana.")
    elif progress_trend < -5:
        insights.append("O progresso desacelerou nos ultimos dias. Ajustes pequenos agora evitam uma queda maior.")

    if not insights:
        insights.append("Voce ainda esta formando padroes. Continue registrando para liberar insights mais precisos.")

    history = [
        {
            "id": row["id"],
            "entry_date": row["entry_date"],
            "sleep_hours": row["sleep_hours"],
            "study_hours": row["study_hours"],
            "exercise_minutes": row["exercise_minutes"],
            "reading_hours": row["reading_hours"],
            "leisure_hours": row["leisure_hours"],
            "mood_score": row["mood_score"],
            "progress_percent": row["progress_percent"],
            "energy_level": row["energy_level"],
            "notes": row["notes"],
        }
        for row in reversed(rows)
    ]

    return {
        "summary": {
            "avg_mood": avg_mood,
            "avg_sleep": avg_sleep,
            "avg_progress": avg_progress,
            "avg_study": avg_study,
            "avg_exercise": avg_exercise,
            "consistency_streak": _longest_consistency_streak(rows),
            "life_score": life_score,
        },
        "charts": {
            "labels": [row["entry_date"] for row in rows],
            "mood": mood_values,
            "sleep": sleep_values,
            "progress": progress_values,
            "study": study_values,
            "exercise": exercise_values,
        },
        "correlations": {
            "sleep_mood": sleep_mood_corr,
            "study_progress": study_progress_corr,
            "exercise_mood": exercise_mood_corr,
        },
        "insights": insights,
        "history": history,
    }
