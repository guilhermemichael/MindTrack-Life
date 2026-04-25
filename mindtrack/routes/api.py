from flask import Blueprint, request, session
from sqlalchemy.exc import IntegrityError

from ..auth import login_required
from ..database import db
from ..models.analytics_snapshot import AnalyticsSnapshot
from ..models.audit_log import AuditLog
from ..services.analytics import get_analytics_snapshot
from ..services.entries import ValidationError, create_entry, delete_entry, get_entry, list_entries, update_entry, validate_entry_payload
from ..services.forecast import predict_mood
from ..services.goals import create_goal, delete_goal, get_goal, list_goals, update_goal, validate_goal_payload
from ..services.habits import (
    create_habit,
    create_habit_log,
    delete_habit,
    get_habit,
    list_habit_logs,
    list_habits,
    update_habit,
    validate_habit_log_payload,
    validate_habit_payload,
)
from ..services.insights import generate_insights, list_persisted_insights
from ..utils.helpers import json_error, json_success


api_bp = Blueprint("api", __name__)


def _snapshot(user_id: int):
    analytics = get_analytics_snapshot(user_id)
    forecast = predict_mood(analytics["mood_values"])
    insights = [item.to_dict() for item in list_persisted_insights(user_id)] or generate_insights(analytics, forecast)
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
            "database_architecture": analytics["database_architecture"],
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
            "database_architecture": analytics_data["database_architecture"],
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


@api_bp.put("/entries/<entry_id>")
@login_required
def update_entry_api(entry_id: str):
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


@api_bp.delete("/entries/<entry_id>")
@login_required
def delete_entry_api(entry_id: str):
    if get_entry(session["user_id"], entry_id) is None:
        return json_error("Registro nao encontrado.", status=404)
    delete_entry(session["user_id"], entry_id)
    return json_success({"deleted": True})


@api_bp.get("/snapshots")
@login_required
def snapshots():
    rows = (
        AnalyticsSnapshot.query.filter_by(user_id=session["user_id"])
        .order_by(AnalyticsSnapshot.period_end.desc())
        .all()
    )
    return json_success([row.to_dict() for row in rows])


@api_bp.get("/audit-logs")
@login_required
def audit_logs():
    rows = (
        AuditLog.query.filter_by(user_id=session["user_id"])
        .order_by(AuditLog.created_at.desc())
        .limit(50)
        .all()
    )
    return json_success([row.to_dict() for row in rows])


@api_bp.get("/habits")
@login_required
def habits():
    return json_success([habit.to_dict() for habit in list_habits(session["user_id"])])


@api_bp.post("/habits")
@login_required
def create_habit_api():
    try:
        payload = validate_habit_payload(request.get_json(force=True))
        habit = create_habit(session["user_id"], payload)
        return json_success(habit.to_dict(), status=201)
    except ValidationError as error:
        return json_error(str(error), status=400)


@api_bp.put("/habits/<habit_id>")
@login_required
def update_habit_api(habit_id: str):
    try:
        payload = validate_habit_payload(request.get_json(force=True))
        habit = update_habit(session["user_id"], habit_id, payload)
    except ValidationError as error:
        return json_error(str(error), status=400)

    if habit is None:
        return json_error("Habito nao encontrado.", status=404)
    return json_success(habit.to_dict())


@api_bp.delete("/habits/<habit_id>")
@login_required
def delete_habit_api(habit_id: str):
    if not delete_habit(session["user_id"], habit_id):
        return json_error("Habito nao encontrado.", status=404)
    return json_success({"deleted": True})


@api_bp.get("/habit-logs")
@login_required
def habit_logs():
    return json_success([log.to_dict() for log in list_habit_logs(session["user_id"])])


@api_bp.post("/habit-logs")
@login_required
def create_habit_log_api():
    try:
        payload = validate_habit_log_payload(request.get_json(force=True))
        log = create_habit_log(session["user_id"], payload)
        return json_success(log.to_dict(), status=201)
    except ValidationError as error:
        return json_error(str(error), status=400)
    except IntegrityError:
        db.session.rollback()
        return json_error("Nao foi possivel salvar o log de habito.", status=409)


@api_bp.get("/goals")
@login_required
def goals():
    return json_success([goal.to_dict() for goal in list_goals(session["user_id"])])


@api_bp.post("/goals")
@login_required
def create_goal_api():
    try:
        payload = validate_goal_payload(request.get_json(force=True))
        goal = create_goal(session["user_id"], payload)
        return json_success(goal.to_dict(), status=201)
    except ValidationError as error:
        return json_error(str(error), status=400)


@api_bp.put("/goals/<goal_id>")
@login_required
def update_goal_api(goal_id: str):
    try:
        payload = validate_goal_payload(request.get_json(force=True))
        goal = update_goal(session["user_id"], goal_id, payload)
    except ValidationError as error:
        return json_error(str(error), status=400)

    if goal is None:
        return json_error("Meta nao encontrada.", status=404)
    return json_success(goal.to_dict())


@api_bp.delete("/goals/<goal_id>")
@login_required
def delete_goal_api(goal_id: str):
    if get_goal(session["user_id"], goal_id) is None:
        return json_error("Meta nao encontrada.", status=404)
    delete_goal(session["user_id"], goal_id)
    return json_success({"deleted": True})
