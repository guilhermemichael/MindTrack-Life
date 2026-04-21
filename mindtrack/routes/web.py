from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from sqlite3 import IntegrityError

from ..auth import login_required
from ..services.analytics import get_dashboard_data
from ..services.entries import create_entry, delete_entry, get_entry, list_entries, update_entry, validate_entry_form


web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("auth.login"))


@web_bp.route("/dashboard")
@login_required
def dashboard():
    data = get_dashboard_data(session["user_id"])
    return render_template("dashboard.html", data=data, today=date.today().isoformat())


@web_bp.route("/entries/new", methods=["GET", "POST"])
@login_required
def create_entry_view():
    if request.method == "POST":
        payload = validate_entry_form(request.form)
        try:
            create_entry(session["user_id"], payload)
            flash("Registro salvo e analise atualizada.", "success")
            return redirect(url_for("web.dashboard"))
        except IntegrityError:
            flash("Ja existe um registro para essa data. Edite o registro existente.", "error")
    return render_template("entries/form.html", entry=None, today=date.today().isoformat())


@web_bp.route("/history")
@login_required
def history():
    entries = list_entries(session["user_id"])
    return render_template("entries/history.html", entries=entries)


@web_bp.route("/entries/<int:entry_id>/edit", methods=["GET", "POST"])
@login_required
def edit_entry(entry_id: int):
    entry = get_entry(session["user_id"], entry_id)
    if request.method == "POST":
        payload = validate_entry_form(request.form)
        try:
            update_entry(session["user_id"], entry_id, payload)
            flash("Registro atualizado com sucesso.", "success")
            return redirect(url_for("web.history"))
        except IntegrityError:
            flash("A data escolhida ja esta ocupada por outro registro.", "error")
    return render_template("entries/form.html", entry=entry, today=date.today().isoformat())


@web_bp.post("/entries/<int:entry_id>/delete")
@login_required
def delete_entry_view(entry_id: int):
    delete_entry(session["user_id"], entry_id)
    flash("Registro removido.", "success")
    return redirect(url_for("web.history"))


@web_bp.route("/insights")
@login_required
def insights():
    data = get_dashboard_data(session["user_id"])
    return render_template("insights.html", data=data)
