from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from flask import jsonify


def normalize_database_url(url: str | None, base_dir: Path, default_sqlite_path: Path) -> str:
    if not url:
        return f"sqlite:///{default_sqlite_path.as_posix()}"

    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)

    if url.startswith("postgresql://") and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)

    if url.startswith("sqlite:///"):
        raw_path = url.removeprefix("sqlite:///")
        if raw_path == ":memory:":
            return url

        path = Path(raw_path)
        if not path.is_absolute():
            return f"sqlite:///{(base_dir / raw_path).resolve().as_posix()}"

    return url


def json_success(data=None, status: int = 200):
    return jsonify({"success": True, "data": data}), status


def json_error(message: str, status: int = 400, details=None):
    payload = {"success": False, "error": message}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status


def serialize_scalar(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def serialize_mapping(mapping: dict | None):
    if mapping is None:
        return None

    serialized = {}
    for key, value in mapping.items():
        if isinstance(value, dict):
            serialized[key] = serialize_mapping(value)
        elif isinstance(value, list):
            serialized[key] = [serialize_scalar(item) for item in value]
        else:
            serialized[key] = serialize_scalar(value)
    return serialized
