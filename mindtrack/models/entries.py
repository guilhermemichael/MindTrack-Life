from dataclasses import dataclass


@dataclass
class DailyEntryPayload:
    entry_date: str
    sleep_hours: float
    study_hours: float
    exercise_minutes: int
    reading_hours: float
    leisure_hours: float
    mood_score: int
    progress_percent: int
    energy_level: int
    notes: str
