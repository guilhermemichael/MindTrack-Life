from flask import Blueprint, jsonify, request, session
from sqlite3 import IntegrityError

from ..auth import login_required
from ..services.analytics import get_dashboard_data
from ..services.entries import create_entry, delete_entry, get_entry, list_entries, update_entry, validate_entry_form


api_bp = Blueprint("api", __name__)


def _entry_to_dict(entry):
    return {
        "id": entry["id"],
        "entry_date": entry["entry_date"],
        "sleep_hours": entry["sleep_hours"],
        "study_hours": entry["study_hours"],
        "exercise_minutes": entry["exercise_minutes"],
        "reading_hours": entry["reading_hours"],
        "leisure_hours": entry["leisure_hours"],
        "mood_score": entry["mood_score"],
        "progress_percent": entry["progress_percent"],
        "energy_level": entry["energy_level"],
        "notes": entry["notes"],
    }


@api_bp.get("/dashboard")
@login_required
def dashboard_data():
    return jsonify(get_dashboard_data(session["user_id"]))


@api_bp.get("/entries")
@login_required
def entries():
    return jsonify([_entry_to_dict(entry) for entry in list_entries(session["user_id"])])


@api_bp.post("/entries")
@login_required
def create_entry_api():
    payload = validate_entry_form(request.get_json(force=True))
    try:
        create_entry(session["user_id"], payload)
    except IntegrityError:
        return jsonify({"error": "Ja existe um registro para essa data."}), 409
    return jsonify({"message": "Registro criado com sucesso."}), 201


@api_bp.put("/entries/<int:entry_id>")
@login_required
def update_entry_api(entry_id: int):
    payload = validate_entry_form(request.get_json(force=True))
    try:
        update_entry(session["user_id"], entry_id, payload)
    except IntegrityError:
        return jsonify({"error": "Ja existe um registro para essa data."}), 409
    return jsonify({"message": "Registro atualizado com sucesso."})


@api_bp.delete("/entries/<int:entry_id>")
@login_required
def delete_entry_api(entry_id: int):
    get_entry(session["user_id"], entry_id)
    delete_entry(session["user_id"], entry_id)
    return jsonify({"message": "Registro removido com sucesso."})
