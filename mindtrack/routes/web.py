from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, send_file, session, url_for
from sqlalchemy.exc import IntegrityError

from ..auth import login_required
from ..services.analytics import get_analytics_snapshot
from ..services.entries import (
    ValidationError,
    create_entry,
    delete_entry,
    export_entries_csv,
    get_entry,
    get_latest_entry,
    list_entries,
    update_entry,
    validate_entry_payload,
)
from ..services.forecast import predict_mood
from ..services.insights import generate_insights, list_persisted_insights


web_bp = Blueprint("web", __name__)


def _build_dashboard_payload(user_id: str) -> dict:
    analytics = get_analytics_snapshot(user_id)
    forecast = predict_mood(analytics["mood_values"])
    insights = [item.to_dict() for item in list_persisted_insights(user_id)] or generate_insights(analytics, forecast)

    return {
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


@web_bp.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("auth.login"))


@web_bp.route("/dashboard")
@login_required
def dashboard():
    data = _build_dashboard_payload(session["user_id"])
    return render_template("dashboard.html", data=data, today=date.today().isoformat())


@web_bp.route("/entries/new", methods=["GET", "POST"])
@login_required
def create_entry_view():
    previous_entry = get_latest_entry(session["user_id"])
    if request.method == "POST":
        try:
            payload = validate_entry_payload(request.form)
            create_entry(session["user_id"], payload)
            flash("Registro salvo e analise atualizada.", "success")
            return redirect(url_for("web.dashboard"))
        except ValidationError as error:
            flash(str(error), "error")
        except IntegrityError:
            from ..database import db

            db.session.rollback()
            flash("Ja existe um registro para essa data. Edite o registro existente.", "error")
    return render_template(
        "entries/form.html",
        entry=previous_entry,
        is_prefill=True,
        today=date.today().isoformat(),
    )


@web_bp.route("/history")
@login_required
def history():
    entries = list_entries(session["user_id"])
    return render_template("entries/history.html", entries=entries)


@web_bp.route("/entries/<entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id: str):
    entry = get_entry(session["user_id"], entry_id)
    if entry is None:
        flash("Registro nao encontrado.", "error")
        return redirect(url_for("web.history"))

    if request.method == "POST":
        try:
            payload = validate_entry_payload(request.form)
            update_entry(session["user_id"], entry_id, payload)
            flash("Registro atualizado com sucesso.", "success")
            return redirect(url_for("web.history"))
        except ValidationError as error:
            flash(str(error), "error")
        except IntegrityError:
            from ..database import db

            db.session.rollback()
            flash("A data escolhida ja esta ocupada por outro registro.", "error")
    return render_template("entries/form.html", entry=entry, is_prefill=False, today=date.today().isoformat())


@web_bp.post("/entries/<entry_id>/delete")
@login_required
def delete_entry_view(entry_id: str):
    if delete_entry(session["user_id"], entry_id):
        flash("Registro removido.", "success")
    else:
        flash("Registro nao encontrado.", "error")
    return redirect(url_for("web.history"))


@web_bp.route("/insights")
@login_required
def insights():
    data = _build_dashboard_payload(session["user_id"])
    return render_template("insights.html", data=data)


@web_bp.get("/export/csv")
@login_required
def export_csv():
    export_path = export_entries_csv(session["user_id"])
    return send_file(export_path, as_attachment=True, download_name="mindtrack-life-export.csv")
