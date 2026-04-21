import csv
import sqlite3
from pathlib import Path

from flask import current_app, g


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    entry_date TEXT NOT NULL,
    sleep_hours REAL NOT NULL,
    study_hours REAL NOT NULL,
    exercise_minutes INTEGER NOT NULL,
    reading_hours REAL NOT NULL DEFAULT 0,
    leisure_hours REAL NOT NULL DEFAULT 0,
    mood_score INTEGER NOT NULL,
    progress_percent INTEGER NOT NULL,
    energy_level INTEGER NOT NULL DEFAULT 5,
    notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE (user_id, entry_date)
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()


def export_user_entries_to_csv(user_id: int) -> None:
    db = get_db()
    export_dir = Path(current_app.config["EXPORT_DIR"])
    export_dir.mkdir(parents=True, exist_ok=True)
    rows = db.execute(
        """
        SELECT entry_date, sleep_hours, study_hours, exercise_minutes, reading_hours,
               leisure_hours, mood_score, progress_percent, energy_level, notes
        FROM daily_entries
        WHERE user_id = ?
        ORDER BY entry_date
        """,
        (user_id,),
    ).fetchall()

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
        for row in rows:
            writer.writerow(row)


def init_app(app):
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()
