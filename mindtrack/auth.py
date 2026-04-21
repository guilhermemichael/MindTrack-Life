from functools import wraps

from flask import redirect, request, session, url_for


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("user_id") is None:
            if request.path.startswith("/api/"):
                from .utils.helpers import json_error

                return json_error("Autenticacao necessaria.", status=401)
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view
