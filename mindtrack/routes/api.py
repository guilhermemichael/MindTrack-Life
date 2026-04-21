from flask import Blueprint, request, session
from sqlalchemy.exc import IntegrityError

from ..auth import login_required
from ..database import db
from ..services.analytics import get_analytics_snapshot
from ..services.entries import ValidationError, create_entry, delete_entry, get_entry, list_entries, update_entry, validate_entry_payload
from ..services.forecast import predict_mood
from ..services.insights import generate_insights
from ..utils.helpers import json_error, json_success


api_bp = Blueprint("api", __name__)


def _snapshot(user_id: int):
    analytics = get_analytics_snapshot(user_id)
    forecast = predict_mood(analytics["mood_values"])
    insights = generate_insights(analytics, forecast)
    return analytics, forecast, insights


@api_bp.get("/dashboard")
@login_required
def dashboard_data():
    analytics, forecast, insights = _snapshot(session["user_id"])
    return json_success(
        {
            "summary": analytics["summary"],
            "metrics": analytics["metrics"],
            "correlations": analytics["correlations"],
            "comparisons": analytics["comparisons"],
            "gamification": analytics["gamification"],
            "charts": analytics["charts"],
            "history": analytics["history"],
            "forecast": forecast,
            "insights": insights,
        }
    )


@api_bp.get("/entries")
@login_required
def entries():
    return json_success([entry.to_dict() for entry in list_entries(session["user_id"])])


@api_bp.get("/analytics")
@login_required
def analytics():
    analytics_data, _, _ = _snapshot(session["user_id"])
    return json_success(
        {
            "summary": analytics_data["summary"],
            "metrics": analytics_data["metrics"],
            "correlations": analytics_data["correlations"],
            "comparisons": analytics_data["comparisons"],
            "gamification": analytics_data["gamification"],
        }
    )


@api_bp.get("/insights")
@login_required
def insights():
    analytics_data, forecast, insights_data = _snapshot(session["user_id"])
    return json_success(
        {
            "insights": insights_data,
            "profile": analytics_data["summary"]["profile"],
            "life_score": analytics_data["summary"]["life_score"],
            "forecast_direction": forecast["direction"],
        }
    )


@api_bp.get("/forecast")
@login_required
def forecast():
    _, forecast_data, _ = _snapshot(session["user_id"])
    return json_success(forecast_data)


@api_bp.post("/entries")
@login_required
def create_entry_api():
    try:
        payload = validate_entry_payload(request.get_json(force=True))
        entry = create_entry(session["user_id"], payload)
    except ValidationError as error:
        return json_error(str(error), status=400)
    except IntegrityError:
        db.session.rollback()
        return json_error("Ja existe um registro para essa data.", status=409)
    return json_success(entry.to_dict(), status=201)


@api_bp.put("/entries/<int:entry_id>")
@login_required
def update_entry_api(entry_id: int):
    try:
        payload = validate_entry_payload(request.get_json(force=True))
        entry = update_entry(session["user_id"], entry_id, payload)
    except ValidationError as error:
        return json_error(str(error), status=400)
    except IntegrityError:
        db.session.rollback()
        return json_error("Ja existe um registro para essa data.", status=409)

    if entry is None:
        return json_error("Registro nao encontrado.", status=404)
    return json_success(entry.to_dict())


@api_bp.delete("/entries/<int:entry_id>")
@login_required
def delete_entry_api(entry_id: int):
    if get_entry(session["user_id"], entry_id) is None:
        return json_error("Registro nao encontrado.", status=404)
    delete_entry(session["user_id"], entry_id)
    return json_success({"deleted": True})
