from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError

from ..database import db
from ..models.user import User
from ..utils.security import check_password, hash_password


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("Preencha todos os campos.", "error")
        elif len(password) < 6:
            flash("A senha precisa ter pelo menos 6 caracteres.", "error")
        elif User.query.filter_by(email=email).first():
            flash("Ja existe uma conta com esse email.", "error")
        else:
            try:
                user = User(name=name, email=email, password_hash=hash_password(password))
                db.session.add(user)
                db.session.commit()
                current_app.logger.info("Novo usuario registrado: %s", email)
                flash("Conta criada com sucesso. Agora faca login.", "success")
                return redirect(url_for("auth.login"))
            except IntegrityError:
                db.session.rollback()
                flash("Nao foi possivel criar a conta agora. Tente novamente.", "error")

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user is None or not check_password(user.password_hash, password):
            flash("Email ou senha invalidos.", "error")
        else:
            session.clear()
            session["user_id"] = user.id
            session["user_name"] = user.name
            session.permanent = True
            current_app.logger.info("Usuario autenticado: %s", email)
            return redirect(url_for("web.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
